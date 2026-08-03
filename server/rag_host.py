# ruff: noqa
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
from pathlib import Path
import threading
from typing import Any, cast
import time

_ENGLISH_MODELS = os.path.expanduser("~/.english-for-agents/models")
_RUNTIME_SUBDIR = "kbs"
_EMBED_DIR = os.environ.get(
    "KBS_EMBED_MLX_MODEL_DIR",
    os.path.join(_ENGLISH_MODELS, "jina-embeddings-v5-text-nano-mlx"),
)
_JINA_DIR = os.environ.get(
    "KBS_JINA_MLX_DIR", os.path.join(_ENGLISH_MODELS, "jina-reranker-v3-mlx")
)
_EMBED_TASK = os.environ.get("KBS_EMBED_TASK", "text-matching")
_FAKE = os.environ.get("KBS_FAKE_MODEL") == "1"


def _env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name, default):
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


_CACHE_LIMIT_BYTES = _env_int("KBS_MLX_CACHE_LIMIT_BYTES", 512 * 1024 * 1024)
_IDLE_SECS = _env_float("KBS_RAG_IDLE_SECS", 600.0)
_IDLE_POLL_SECS = 5.0
_model_lock = threading.Lock()
_embedder = None
_reranker = None


def _set_cache_limit():
    try:
        import mlx.core as mx  # type: ignore[import-not-found]

        mx.set_cache_limit(_CACHE_LIMIT_BYTES)
    except Exception:
        pass


def _clear_mlx_cache():
    try:
        import mlx.core as mx  # type: ignore[import-not-found]

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
            _start_request(self.server)
            try:
                message = json.loads(line)
                response = _dispatch(
                    message, cast(Any, self.server).ref_dir, self.server
                )
            except Exception as exc:
                response = {"error": str(exc)}
            finally:
                _finish_request(self.server)
            self.wfile.write((json.dumps(response) + "\n").encode())
            self.wfile.flush()


class _Server(socketserver.ThreadingUnixStreamServer):
    allow_reuse_address = False

    def __init__(self, sock_path, ref_dir):
        self.ref_dir = ref_dir
        self._shutting_down = False
        self._last_request_at = time.monotonic()
        self._active_requests = 0
        self._request_lock = threading.Lock()
        super().__init__(sock_path, _Handler)


def _runtime_dir():
    """Isolation is required because shared socket paths allow cross user interference."""
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    directory = base / _RUNTIME_SUBDIR
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    return directory


def default_sock_path():
    """Return the configured or private default daemon socket path."""
    override = os.environ.get("KBS_RAG_SOCK_PATH")
    return override or str(_runtime_dir() / "rag.sock")


def default_ref_dir():
    return os.environ.get("KBS_RAG_REF_DIR", default_sock_path() + ".refs")


def _status_response(server):
    """Monotonic time is required because wall clock changes must not distort idle age."""
    last_request_at, active_requests = _request_snapshot(server)
    return {
        "status": "alive",
        "model_warm": _model_warm(),
        "last_request_at": last_request_at,
        "idle_seconds": max(0.0, time.monotonic() - last_request_at),
        "active_requests": active_requests,
        "shutting_down": getattr(server, "_shutting_down", False),
    }


def _blocked_by_shutdown(operation, server):
    """New work stops because accepting it would race server closure."""
    return getattr(server, "_shutting_down", False) and operation in {
        "attach",
        "attach_turn",
        "embed",
        "rerank",
    }


def _dispatch(message, ref_dir, server):
    operation = message.get("op")
    if operation == "status":
        return _status_response(server)
    if _blocked_by_shutdown(operation, server):
        return {"error": "host is shutting down"}
    if operation == "embed":
        return {"vectors": _embed(message.get("texts", []))}
    if operation == "rerank":
        return {
            "results": _rerank(message.get("query", ""), message.get("documents", []))
        }
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
    return {"released": True, "last": is_last}


def _start_request(server):
    lock = getattr(server, "_request_lock", None)
    if lock is None:
        return
    with lock:
        server._active_requests += 1


def _finish_request(server):
    lock = getattr(server, "_request_lock", None)
    if lock is None:
        server._last_request_at = time.monotonic()
        return
    with lock:
        server._active_requests = max(0, server._active_requests - 1)
        server._last_request_at = time.monotonic()


def _request_snapshot(server):
    lock = getattr(server, "_request_lock", None)
    if lock is None:
        if not hasattr(server, "_last_request_at"):
            server._last_request_at = time.monotonic()
        return server._last_request_at, 0
    with lock:
        return server._last_request_at, server._active_requests


def _begin_shutdown(server):
    server._shutting_down = True
    shutdown = getattr(server, "shutdown", None)
    if callable(shutdown):
        threading.Thread(target=shutdown, daemon=True).start()


def _model_warm():
    return _FAKE or _embedder is not None or _reranker is not None


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
        result = []
        for row in raw:
            try:
                result.append(
                    {
                        "index": int(row["index"]),
                        "score": float(
                            row.get("score", row.get("relevance_score", 0.0))
                        ),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
        _clear_mlx_cache()
        return result


def _fake_vector(text):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round((digest[index] - 128) / 128.0, 6) for index in range(8)]


def _fake_rerank(query, docs):
    rows = []
    for index, doc in enumerate(docs):
        score = sum(_fake_vector(query + "\n" + doc))
        try:
            rows.append({"index": index, "score": float(score)})
        except (TypeError, ValueError):
            continue
    rows.sort(key=lambda row: -row["score"])
    return rows


def _embedding_config():
    """Metadata is checked first because invalid settings must fail before weight allocation."""
    try:
        with open(os.path.join(_EMBED_DIR, "config.json"), encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise RuntimeError("embedding config not readable") from exc


def _embedding_module():
    """Path loading is required because the model implementation is not an installed package."""
    spec = importlib.util.spec_from_file_location(
        "kbs_jina_embed", os.path.join(_EMBED_DIR, "model.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("embedding model module not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _initialize_embedder(mx, tokenizer_class):
    """Assets share one directory because mismatched weights and tokens produce invalid vectors."""
    module = _embedding_module()
    model_class = next(
        getattr(module, name)
        for name in dir(module)
        if name.endswith("EmbeddingModel") and isinstance(getattr(module, name), type)
    )
    model = _build_embed_model(module, model_class, _embedding_config())
    weights = mx.load(os.path.join(_EMBED_DIR, "model.safetensors"))
    if hasattr(model, "sanitize"):
        weights = model.sanitize(weights)
    model.load_weights(list(weights.items()))
    mx.eval(model.parameters())
    tokenizer = tokenizer_class.from_file(os.path.join(_EMBED_DIR, "tokenizer.json"))
    return model, tokenizer


def _load_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    import mlx.core as mx  # type: ignore[import-not-found]
    from tokenizers import Tokenizer  # type: ignore[import-not-found]

    model, tokenizer = _initialize_embedder(mx, Tokenizer)

    def encode(texts):
        output = model.encode(texts, tokenizer, task_type=_EMBED_TASK)
        mx.eval(output)
        return output

    _embedder = encode
    return _embedder


def _build_embed_model(module, model_class, config):
    try:
        return model_class(config)
    except TypeError:
        pass
    except ValueError:
        pass
    except RuntimeError:
        pass
    for name in dir(module):
        candidate = getattr(module, name)
        if name.endswith("Config") and hasattr(candidate, "from_dict"):
            try:
                return model_class(candidate.from_dict(config))
            except TypeError:
                continue
            except ValueError:
                continue
            except RuntimeError:
                continue
    raise RuntimeError("no usable Jina embedding config")


def _load_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    cwd = os.getcwd()
    sys.path.insert(0, _JINA_DIR)
    try:
        os.chdir(_JINA_DIR)
        from rerank import MLXReranker  # type: ignore[import-not-found]

        _reranker = MLXReranker()
    finally:
        os.chdir(cwd)
        with contextlib.suppress(ValueError):
            sys.path.remove(_JINA_DIR)
    return _reranker


def _idle_watchdog(server, ref_dir):
    """Idle shutdown is required because warm models must release memory after demand stops."""
    while not getattr(server, "_shutting_down", False):
        time.sleep(_IDLE_POLL_SECS)
        if getattr(server, "_shutting_down", False):
            return
        last_request_at, active_requests = _request_snapshot(server)
        if active_requests or time.monotonic() - last_request_at < _IDLE_SECS:
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
    try:
        os.makedirs(os.path.dirname(sock_path), mode=0o700, exist_ok=True)
    except OSError:
        return
    host_lock_fd = os.open(sock_path + ".hostlock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(host_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(host_lock_fd)
        return
    Path(sock_path).unlink(missing_ok=True)
    _set_cache_limit()
    server = _Server(sock_path, ref_dir)

    def stop(sig, frame):
        _begin_shutdown(server)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    threading.Thread(target=_idle_watchdog, args=(server, ref_dir), daemon=True).start()
    server.serve_forever(poll_interval=0.2)
    server.server_close()
    Path(sock_path).unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _run(default_sock_path(), default_ref_dir())
    elif len(sys.argv) == 3:
        _run(sys.argv[1], sys.argv[2])
    else:
        sys.exit("usage: rag_host.py <sock_path> <ref_dir>")
