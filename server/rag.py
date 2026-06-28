import contextlib
import fcntl
import json
import os
import socket
import stat
import subprocess
import threading
import time

import bm25s
import numpy as np

_CONNECT_TIMEOUT = 10.0
_REQUEST_TIMEOUT = 120.0
_DEFAULT_SOCK = os.path.join(os.environ.get("TMPDIR", "/tmp"), "kbs-rag.sock")
_LOADER_PY = "/Users/michael/dev/skills/skill-model-loader/.venv/bin/python"
_HOST = os.path.join(os.path.dirname(__file__), "rag_host.py")
_spawn_lock = threading.Lock()
_RRF_K = 60


def default_sock_path():
    return os.environ.get("KBS_RAG_SOCK_PATH", _DEFAULT_SOCK)


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
            with contextlib.suppress(Exception):
                rerank_order.append(int(row["index"]))
        alignment_orders.append(rerank_order)
    relevance_scores = dict(_rrf(alignment_orders))
    return _by_order(results, relevance_scores)


def _request_host(msg, sock_path, ref_dir, host_argv, env):
    conn = _connect_or_spawn(sock_path, ref_dir, host_argv, env)
    if conn is None:
        return None
    return _request_on(conn, msg)


def _connect_or_spawn(sock_path, ref_dir, host_argv, env):
    conn = _connect(sock_path)
    if conn is not None:
        return conn
    lock_path = sock_path + ".spawnlock"
    with _spawn_lock:
        os.makedirs(os.path.dirname(sock_path), exist_ok=True)
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            conn = _poll_for_host(sock_path, stop_if_absent=True)
            if conn is not None:
                return conn
            with contextlib.suppress(OSError):
                os.remove(sock_path)
            argv = list(host_argv) if host_argv else [_LOADER_PY, _HOST]
            subprocess.Popen(
                argv + [sock_path, ref_dir],
                start_new_session=True,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return _poll_for_host(sock_path, stop_if_absent=False)
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)


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


def _stale_path(sock_path):
    try:
        return os.path.exists(sock_path) and not stat.S_ISSOCK(os.stat(sock_path).st_mode)
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
        return " ".join(str(result.get(key, "")) for key in ("title", "snippet", "url")).strip()
    return str(result)


def _bm25_order(query, docs):
    if not docs:
        return []
    try:
        retriever = bm25s.BM25()
        retriever.index(bm25s.tokenize(docs, show_progress=False), show_progress=False)
        response = retriever.retrieve(bm25s.tokenize([query], show_progress=False), k=len(docs), show_progress=False)
        return _coerce_indices(response)
    except Exception:
        return list(range(len(docs)))


def _coerce_indices(response):
    documents = response[0] if isinstance(response, tuple) else getattr(response, "documents", response)
    first = documents[0] if len(documents) and isinstance(documents[0], (list, tuple, np.ndarray)) else documents
    return [int(index) for index in first]


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
    return -int(digits) if digits.isdigit() else 1


def _cosine(left, right):
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right)) / (left_norm * right_norm)


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
