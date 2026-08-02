# ruff: noqa
import contextlib
import fcntl
import json
import os
import socket
import stat
import subprocess
import threading
import time
from pathlib import Path

import bm25s
import numpy as np

_CONNECT_TIMEOUT = 10.0
_REQUEST_TIMEOUT = 120.0
_RUNTIME_SUBDIR = "kbs"
_HOST = os.path.join(os.path.dirname(__file__), "rag_host.py")
_spawn_lock = threading.Lock()
_RRF_K = 60


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


def _loader_python():
    return os.environ.get(
        "KBS_PYTHON", os.path.join(_loader_dir(), ".venv", "bin", "python")
    )


def dense_ranking_status():
    """Report whether the external dense model host can be started."""
    loader = Path(_loader_dir())
    checks = [
        ("model loader", loader / "refcount.py"),
        ("model loader Python", Path(_loader_python())),
    ]
    if os.environ.get("KBS_FAKE_MODEL") != "1":
        models = Path.home() / ".english-for-agents" / "models"
        embed = Path(
            os.environ.get(
                "KBS_EMBED_MLX_MODEL_DIR", models / "jina-embeddings-v5-text-nano-mlx"
            )
        )
        rerank = Path(
            os.environ.get("KBS_JINA_MLX_DIR", models / "jina-reranker-v3-mlx")
        )
        checks.extend((("embedding model", embed), ("reranking model", rerank)))
    for label, path in checks:
        if not path.exists():
            return {"available": False, "reason": f"{label} missing at {path}"}
    python_path = Path(_loader_python())
    if not python_path.is_file() or not os.access(python_path, os.X_OK):
        reason = f"model loader Python is not executable at {python_path}"
        return {"available": False, "reason": reason}
    return {"available": True, "reason": "model loader and model paths are present"}


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


def embed(texts, sock_path=None, ref_dir=None, host_argv=None, env=None):
    try:
        response = _request_host(
            {"op": "embed", "texts": list(texts)},
            sock_path or default_sock_path(),
            ref_dir or default_ref_dir(),
            host_argv,
            env,
        )
        vectors = response.get("vectors") if response else None
        return vectors if isinstance(vectors, list) else None
    except Exception:
        return None


def rerank(query, docs, sock_path=None, ref_dir=None, host_argv=None, env=None):
    try:
        response = _request_host(
            {"op": "rerank", "query": query, "documents": list(docs)},
            sock_path or default_sock_path(),
            ref_dir or default_ref_dir(),
            host_argv,
            env,
        )
        results = response.get("results") if response else None
        return results if isinstance(results, list) else None
    except Exception:
        return None


def rank(query, results):
    docs = [_doc_text(result) for result in results]
    alignment_orders = [_bm25_order(query, docs)]
    vectors = embed([query] + docs)
    if vectors is not None:
        with contextlib.suppress(Exception):
            alignment_orders.append(_dense_order(vectors))
    reranked = rerank(query, docs)
    if reranked is not None:
        rerank_order = []
        for row in reranked:
            try:
                rerank_order.append(int(row["index"]))
            except Exception:
                continue
        alignment_orders.append(rerank_order)
    relevance_scores = dict(_rrf(alignment_orders))
    return _by_order(results, relevance_scores)


def _request_host(msg, sock_path, ref_dir, host_argv, env):
    conn = _connect_or_spawn(sock_path, ref_dir, host_argv, env)
    if conn is None:
        return None
    return _request_on(conn, msg)


def _connect_or_spawn(sock_path, ref_dir, host_argv, env):
    """This decision is serialized because clients must not spawn duplicate model hosts."""
    conn = _connect(sock_path)
    if conn is not None:
        return conn
    with _spawn_lock:
        try:
            os.makedirs(os.path.dirname(sock_path), mode=0o700, exist_ok=True)
        except OSError:
            return None
        return _connect_under_spawn_lock(sock_path, ref_dir, host_argv, env)


def _connect_under_spawn_lock(sock_path, ref_dir, host_argv, env):
    """The lock covers stale checks and creation because separating them leaves a spawn race."""
    lock_fd = os.open(sock_path + ".spawnlock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return _recover_or_spawn(sock_path, ref_dir, host_argv, env)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def _host_lock_held(sock_path):
    """The lifetime lock is authoritative because one failed connection does not prove death."""
    lock_fd = os.open(sock_path + ".hostlock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(lock_fd)
        return True
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    return False


def _recover_or_spawn(sock_path, ref_dir, host_argv, env):
    """Removal waits for lock proof because a live host may briefly reject connections."""
    conn = _connect(sock_path)
    if conn is not None:
        return conn
    if not os.path.exists(sock_path):
        conn = _poll_for_host(sock_path, stop_if_absent=True)
        if conn is not None:
            return conn
    if _host_lock_held(sock_path):
        return _poll_for_host(sock_path, stop_if_absent=False)
    if os.path.exists(sock_path):
        with contextlib.suppress(OSError):
            os.remove(sock_path)
    argv = list(host_argv) if host_argv else [_loader_python(), _HOST]
    subprocess.Popen(
        argv + [sock_path, ref_dir],
        start_new_session=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return _poll_for_host(sock_path, stop_if_absent=False)


def _poll_for_host(sock_path, stop_if_absent):
    deadline = time.monotonic() + _CONNECT_TIMEOUT
    while time.monotonic() < deadline:
        conn = _connect(sock_path)
        if conn is not None:
            return conn
        if _stale_path(sock_path):
            return None
        if stop_if_absent and not os.path.exists(sock_path):
            return None
        time.sleep(0.05)
    return None


def _connect(sock_path):
    if not os.path.exists(sock_path):
        return None
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.settimeout(1.0)
        conn.connect(sock_path)
        return conn
    except OSError:
        with contextlib.suppress(OSError):
            conn.close()
        return None


def _request(sock_path, msg, timeout=_REQUEST_TIMEOUT):
    conn = _connect(sock_path)
    if conn is None:
        return None
    return _request_on(conn, msg, timeout)


def _base_daemon_status(socket_path):
    """Stable keys are required because CLI consumers compare daemon states structurally."""
    return {
        "status": "down",
        "persistent_process": "rag_host",
        "socket_path": socket_path,
        "socket_exists": os.path.exists(socket_path),
        "socket_stale": False,
        "model_warm": None,
        "last_request_at": None,
        "idle_seconds": None,
    }


def daemon_status(sock_path=None):
    """Report daemon reachability and model warmth."""
    socket_path = sock_path or default_sock_path()
    status = _base_daemon_status(socket_path)
    if not status["socket_exists"]:
        return status
    if _stale_path(socket_path):
        status["status"] = "stale"
        status["socket_stale"] = True
        return status
    response = _request(socket_path, {"op": "status"}, timeout=1.0)
    if response is None:
        status["status"] = "stale"
        status["socket_stale"] = True
        return status
    status.update(response)
    status["status"] = "alive"
    status["socket_stale"] = False
    return status


def _stale_path(sock_path):
    try:
        return os.path.exists(sock_path) and not stat.S_ISSOCK(
            os.stat(sock_path).st_mode
        )
    except OSError:
        return False


def _request_on(sock, msg, timeout=_REQUEST_TIMEOUT):
    try:
        sock.settimeout(timeout)
        sock.sendall((json.dumps(msg) + "\n").encode())
        chunks = b""
        while b"\n" not in chunks:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks += chunk
        return json.loads(chunks.split(b"\n")[0]) if chunks else None
    except (OSError, ValueError):
        return None
    finally:
        with contextlib.suppress(OSError):
            sock.close()


def _doc_text(result):
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return " ".join(
            str(result.get(key, "")) for key in ("title", "snippet", "url")
        ).strip()
    return str(result)


def _bm25_order(query, docs):
    if not docs:
        return []
    try:
        retriever = bm25s.BM25()
        retriever.index(bm25s.tokenize(docs, show_progress=False), show_progress=False)
        response = retriever.retrieve(
            bm25s.tokenize([query], show_progress=False),
            k=len(docs),
            show_progress=False,
        )
        return _coerce_indices(response)
    except Exception:
        return list(range(len(docs)))


def _coerce_indices(response):
    documents = (
        response[0]
        if isinstance(response, tuple)
        else getattr(response, "documents", response)
    )
    first = (
        documents[0]
        if len(documents) and isinstance(documents[0], (list, tuple, np.ndarray))
        else documents
    )
    try:
        return [int(index) for index in first]
    except Exception:
        return []


def _dense_order(vectors):
    if not vectors or len(vectors) < 2:
        return []
    query = np.asarray(vectors[0], dtype=float)
    scores = []
    for index, vector in enumerate(vectors[1:]):
        scores.append((index, _cosine(query, np.asarray(vector, dtype=float))))
    scores.sort(key=lambda item: -item[1])
    return [index for index, score in scores]


def _date_key(result):
    date = result.get("date", "") if isinstance(result, dict) else ""
    digits = date.replace("-", "")
    try:
        return -int(digits) if digits.isdigit() else 1
    except ValueError:
        return 1


def _cosine(left, right):
    try:
        left_norm = float(np.linalg.norm(left))
        right_norm = float(np.linalg.norm(right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return float(np.dot(left, right)) / (left_norm * right_norm)
    except Exception:
        return 0.0


def _rrf(rankings):
    scores = {}
    for ranking in rankings:
        for position, index in enumerate(ranking):
            scores[index] = scores.get(index, 0.0) + 1.0 / (_RRF_K + position + 1)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def _by_order(results, relevance_scores):
    max_score = max(relevance_scores.values(), default=0.0)
    ranked = []
    for index, result in enumerate(results):
        score = relevance_scores.get(index, 0.0)
        relevance = round(score / max_score, 2) if max_score else 0.0
        if isinstance(result, dict):
            result["relevance"] = relevance
        ranked.append((relevance, _date_key(result), index, result))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[3] for item in ranked]
