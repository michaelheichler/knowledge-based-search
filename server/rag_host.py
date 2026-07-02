import contextlib
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
import signal
import socketserver
import sys
import threading
import time

_ENGLISH_MODELS = os.path.expanduser("~/.english-for-agents/models")
_DEFAULT_SOCK = os.path.join(os.environ.get("TMPDIR", "/tmp"), "kbs-rag.sock")
_EMBED_DIR = os.environ.get(
    "KBS_EMBED_MLX_MODEL_DIR",
    os.path.join(_ENGLISH_MODELS, "jina-embeddings-v5-text-nano-mlx"),
)
_JINA_DIR = os.environ.get("KBS_JINA_MLX_DIR", os.path.join(_ENGLISH_MODELS, "jina-reranker-v3-mlx"))
_EMBED_TASK = os.environ.get("KBS_EMBED_TASK", "text-matching")
_FAKE = os.environ.get("KBS_FAKE_MODEL") == "1"
_CACHE_LIMIT_BYTES = int(
    os.environ.get("KBS_MLX_CACHE_LIMIT_BYTES", str(512 * 1024 * 1024))
)
_IDLE_SECS = float(os.environ.get("KBS_RAG_IDLE_SECS", "600"))
_IDLE_POLL_SECS = 5.0
_model_lock = threading.Lock()
_embedder = None
_reranker = None


def _set_cache_limit():
    try:
        import mlx.core as mx

        mx.set_cache_limit(_CACHE_LIMIT_BYTES)
    except Exception:
        pass


def _clear_mlx_cache():
    try:
        import mlx.core as mx

        mx.clear_cache()
    except Exception:
        pass


def _loader_dir():
    return os.environ.get(
        "KBS_LOADER_DIR",
        os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "skill-model-loader",
        ),
    )


_LOADER_DIR = _loader_dir()
sys.path.insert(0, _LOADER_DIR)
refcount = importlib.import_module("refcount")


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            line = raw.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
                response = _dispatch(message, self.server.ref_dir, self.server)
            except Exception as exc:
                response = {"error": str(exc)}
            self.wfile.write((json.dumps(response) + "\n").encode())
            self.wfile.flush()


class _Server(socketserver.ThreadingUnixStreamServer):
    allow_reuse_address = False

    def __init__(self, sock_path, ref_dir):
        self.ref_dir = ref_dir
        self._shutting_down = False
        super().__init__(sock_path, _Handler)


def default_sock_path():
    return os.environ.get("KBS_RAG_SOCK_PATH", _DEFAULT_SOCK)


def default_ref_dir():
    return os.environ.get("KBS_RAG_REF_DIR", default_sock_path() + ".refs")


def _dispatch(message, ref_dir, server):
    operation = message.get("op")
    if getattr(server, "_shutting_down", False) and operation in ("attach", "attach_turn", "embed", "rerank"):
        return {"error": "host is shutting down"}
    if operation == "embed":
        return {"vectors": _embed(message.get("texts", []))}
    if operation == "rerank":
        return {"results": _rerank(message.get("query", ""), message.get("documents", []))}
    counter = refcount.Refcount(ref_dir)
    if operation == "attach":
        return {"ref": counter.attach(message["tool"], message["session"])}
    if operation == "attach_turn":
        return {"ref": counter.attach_turn(message["turn_id"])}
    if operation == "release":
        is_last = counter.detach(message["ref"])
    elif operation == "release_turn":
        is_last = counter.detach_turn(message["turn_id"])
    else:
        return {"error": f"unknown op {operation!r}"}
    if is_last:
        _begin_shutdown(server)
    return {"released": True, "last": is_last}


def _begin_shutdown(server):
    server._shutting_down = True
    threading.Thread(target=server.shutdown, daemon=True).start()


def _embed(texts):
    clean = [str(text) for text in texts]
    if _FAKE:
        return [_fake_vector(text) for text in clean]
    with _model_lock:
        model = _load_embedder()
        vectors = model(clean)
        result = vectors.tolist() if hasattr(vectors, "tolist") else vectors
        _clear_mlx_cache()
        return result


def _rerank(query, documents):
    docs = [str(doc) for doc in documents]
    if _FAKE:
        return _fake_rerank(str(query), docs)
    if not docs:
        return []
    with _model_lock:
        raw = _load_reranker().rerank(str(query), docs)
        result = [
            {
                "index": int(row["index"]),
                "score": float(row.get("score", row.get("relevance_score", 0.0))),
            }
            for row in raw
        ]
        _clear_mlx_cache()
        return result


def _fake_vector(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round((digest[index] - 128) / 128.0, 6) for index in range(8)]


def _fake_rerank(query, docs):
    rows = []
    for index, doc in enumerate(docs):
        score = sum(_fake_vector(query + "\n" + doc))
        rows.append({"index": index, "score": float(score)})
    rows.sort(key=lambda row: -row["score"])
    return rows


def _load_embedder():  # craftsman-ignore: PY002
    global _embedder
    if _embedder is not None:
        return _embedder
    import mlx.core as mx
    from tokenizers import Tokenizer

    with open(os.path.join(_EMBED_DIR, "config.json"), encoding="utf-8") as handle:
        config = json.load(handle)
    spec = importlib.util.spec_from_file_location("kbs_jina_embed", os.path.join(_EMBED_DIR, "model.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model_class = next(getattr(module, name) for name in dir(module) if name.endswith("EmbeddingModel") and isinstance(getattr(module, name), type))
    model = _build_embed_model(module, model_class, config)
    weights = mx.load(os.path.join(_EMBED_DIR, "model.safetensors"))
    if hasattr(model, "sanitize"):
        weights = model.sanitize(weights)
    model.load_weights(list(weights.items()))
    mx.eval(model.parameters())
    tokenizer = Tokenizer.from_file(os.path.join(_EMBED_DIR, "tokenizer.json"))

    def encode(texts):
        output = model.encode(texts, tokenizer, task_type=_EMBED_TASK)
        mx.eval(output)
        return output

    _embedder = encode
    return _embedder


def _build_embed_model(module, model_class, config):
    try:
        return model_class(config)
    except Exception:
        for name in dir(module):
            candidate = getattr(module, name)
            if name.endswith("Config") and hasattr(candidate, "from_dict"):
                with contextlib.suppress(Exception):
                    return model_class(candidate.from_dict(config))
    raise RuntimeError("no usable Jina embedding config")


def _load_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    cwd = os.getcwd()
    sys.path.insert(0, _JINA_DIR)
    try:
        os.chdir(_JINA_DIR)
        from rerank import MLXReranker
        _reranker = MLXReranker()
    finally:
        os.chdir(cwd)
        with contextlib.suppress(ValueError):
            sys.path.remove(_JINA_DIR)
    return _reranker


def _idle_watchdog(server, ref_dir):
    """After _IDLE_SECS with no attached client and no request in flight, clear the cache and shut down."""
    counter = refcount.Refcount(ref_dir)
    zero_since = None
    while not getattr(server, "_shutting_down", False):
        time.sleep(_IDLE_POLL_SECS)
        if getattr(server, "_shutting_down", False):
            return
        if counter.live_count() != 0:
            zero_since = None
            continue
        if zero_since is None:
            zero_since = time.monotonic()
            continue
        if time.monotonic() - zero_since < _IDLE_SECS:
            continue
        if not _model_lock.acquire(blocking=False):
            continue
        try:
            _clear_mlx_cache()
        finally:
            _model_lock.release()
        _begin_shutdown(server)
        return


def _run(sock_path, ref_dir):
    # Held for the process lifetime so a second host can never bind over a live one and double-load the models.
    host_lock_fd = os.open(sock_path + ".hostlock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(host_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(0)
    with contextlib.suppress(OSError):
        os.unlink(sock_path)
    os.makedirs(os.path.dirname(sock_path), exist_ok=True)
    _set_cache_limit()
    server = _Server(sock_path, ref_dir)

    def stop(sig, frame):
        _begin_shutdown(server)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    threading.Thread(target=_idle_watchdog, args=(server, ref_dir), daemon=True).start()
    server.serve_forever(poll_interval=0.2)
    server.server_close()
    # AF_UNIX close() does not remove the bound path, so unlink it ourselves.
    with contextlib.suppress(OSError):
        os.unlink(sock_path)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _run(default_sock_path(), default_ref_dir())
    elif len(sys.argv) == 3:
        _run(sys.argv[1], sys.argv[2])
    else:
        sys.exit("usage: rag_host.py <sock_path> <ref_dir>")
