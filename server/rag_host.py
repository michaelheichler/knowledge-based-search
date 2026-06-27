import contextlib
import hashlib
import importlib.util
import json
import os
import signal
import socketserver
import sys
import threading

_LOADER_DIR = "/Users/michael/dev/skills/skill-model-loader"
_ENGLISH_MODELS = os.path.expanduser("~/.english-for-agents/models")
_DEFAULT_SOCK = os.path.join(os.environ.get("TMPDIR", "/tmp"), "kbs-rag.sock")
_EMBED_DIR = os.environ.get(
    "KBS_EMBED_MLX_MODEL_DIR",
    os.path.join(_ENGLISH_MODELS, "jina-embeddings-v5-text-nano-mlx"),
)
_JINA_DIR = os.environ.get("KBS_JINA_MLX_DIR", os.path.join(_ENGLISH_MODELS, "jina-reranker-v3-mlx"))
_EMBED_TASK = os.environ.get("KBS_EMBED_TASK", "text-matching")
_FAKE = os.environ.get("KBS_FAKE_MODEL") == "1"
_model_lock = threading.Lock()
_embedder = None
_reranker = None

sys.path.insert(0, _LOADER_DIR)
import refcount


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
        return vectors.tolist() if hasattr(vectors, "tolist") else vectors


def _rerank(query, documents):
    docs = [str(doc) for doc in documents]
    if _FAKE:
        return _fake_rerank(str(query), docs)
    if not docs:
        return []
    with _model_lock:
        raw = _load_reranker().rerank(str(query), docs)
        return [{"index": int(row["index"]), "score": float(row.get("score", row.get("relevance_score", 0.0)))} for row in raw]


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


def _load_embedder():
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


def _run(sock_path, ref_dir):
    with contextlib.suppress(OSError):
        os.unlink(sock_path)
    os.makedirs(os.path.dirname(sock_path), exist_ok=True)
    server = _Server(sock_path, ref_dir)

    def stop(sig, frame):
        _begin_shutdown(server)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    server.serve_forever(poll_interval=0.2)
    server.server_close()
    with contextlib.suppress(OSError):
        os.unlink(sock_path)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _run(default_sock_path(), default_ref_dir())
    elif len(sys.argv) == 3:
        _run(sys.argv[1], sys.argv[2])
    else:
        sys.exit("usage: rag_host.py <sock_path> <ref_dir>")
