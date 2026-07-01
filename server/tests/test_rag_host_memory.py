import importlib
import os
import sys
import tempfile
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_EMBED_DIR = os.path.expanduser(
    "~/.english-for-agents/models/jina-embeddings-v5-text-nano-mlx"
)


def _fresh_real_host(cache_limit_bytes):
    os.environ.pop("KBS_FAKE_MODEL", None)
    os.environ["KBS_MLX_CACHE_LIMIT_BYTES"] = str(cache_limit_bytes)
    import rag_host

    return importlib.reload(rag_host)


def _fake_host():
    os.environ["KBS_FAKE_MODEL"] = "1"
    import rag_host

    return importlib.reload(rag_host)


@pytest.mark.skipif(
    not os.path.isdir(_EMBED_DIR), reason="jina embed MLX weights not present"
)
def test_repeated_embeds_keep_the_cache_capped_and_cleared():
    mx = pytest.importorskip("mlx.core")
    cap = 32 * 1024 * 1024
    host = _fresh_real_host(cap)
    host._set_cache_limit()
    server = type("Server", (), {"ref_dir": None, "_shutting_down": False})()

    for _ in range(20):
        host._dispatch(
            {"op": "embed", "texts": ["a short sentence to embed"] * 4},
            server.ref_dir,
            server,
        )

    assert mx.get_cache_memory() <= cap
    assert mx.get_cache_memory() < 1024 * 1024


def test_idle_watchdog_clears_cache_and_shuts_down_after_timeout():
    host = _fake_host()
    host._IDLE_SECS = 0.05
    host._IDLE_POLL_SECS = 0.01
    ref_dir = tempfile.mkdtemp(prefix="kbs-rag-refs-")
    calls = []

    class Server:
        _shutting_down = False

        def shutdown(self):
            calls.append("shutdown")

    server = Server()
    thread = threading.Thread(
        target=host._idle_watchdog, args=(server, ref_dir), daemon=True
    )
    thread.start()
    deadline = time.monotonic() + 2
    while not calls and time.monotonic() < deadline:
        time.sleep(0.01)
    thread.join(timeout=1)

    assert calls == ["shutdown"]
