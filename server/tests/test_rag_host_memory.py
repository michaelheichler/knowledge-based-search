import fcntl
import importlib
import os
import stat
import tempfile
import threading
import time
from pathlib import Path

import pytest
import rag


def _fresh_real_host(cache_limit_bytes):
    os.environ.pop("KBS_FAKE_MODEL", None)
    os.environ["KBS_MLX_CACHE_LIMIT_BYTES"] = str(cache_limit_bytes)
    import rag_host

    return importlib.reload(rag_host)


def _fake_host():
    os.environ["KBS_FAKE_MODEL"] = "1"
    import rag_host

    return importlib.reload(rag_host)


@pytest.mark.integration
def test_repeated_embeds_keep_the_cache_capped_and_cleared():
    if os.environ.get("KBS_OFFLINE") == "1":
        pytest.skip("KBS_OFFLINE=1")
    mlx_core = pytest.importorskip("mlx.core")
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

    assert mlx_core.get_cache_memory() <= cap
    assert mlx_core.get_cache_memory() < 1024 * 1024


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


def test_default_socket_uses_private_user_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.delenv("KBS_RAG_SOCK_PATH", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    socket_path = Path(rag.default_sock_path())

    assert socket_path == tmp_path / ".cache" / "kbs" / "rag.sock"
    assert stat.S_IMODE(socket_path.parent.stat().st_mode) == 0o700


def test_live_host_lock_prevents_socket_unlink(monkeypatch, tmp_path):
    socket_path = str(tmp_path / "rag.sock")
    Path(socket_path).write_text("socket placeholder", encoding="utf-8")
    lock_fd = os.open(socket_path + ".hostlock", os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    monkeypatch.setattr(rag, "_connect", lambda path: None)
    monkeypatch.setattr(rag, "_poll_for_host", lambda path, stop_if_absent: None)
    monkeypatch.setattr(
        rag.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("spawned host")
    )
    try:
        assert rag._recover_or_spawn(socket_path, str(tmp_path / "refs"), None, None) is None
        assert Path(socket_path).exists()
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def test_dense_status_explains_missing_backend(monkeypatch):
    import embed_backend

    monkeypatch.setattr(embed_backend, "is_apple_silicon", lambda: True)
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "mlx_embeddings" or name.startswith("mlx_embeddings."):
            raise ImportError("no module named mlx_embeddings")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)

    status = rag.dense_ranking_status()

    assert status["available"] is False
    assert "mlx_embeddings" in status["reason"]


def test_dense_status_reports_available_for_this_platform():
    import embed_backend

    if embed_backend.is_apple_silicon():
        pytest.importorskip("mlx_embeddings")
        expected_reason = "mlx_embeddings is installed"
    else:
        pytest.importorskip("llama_cpp")
        expected_reason = "llama_cpp is installed"

    status = rag.dense_ranking_status()

    assert status == {"available": True, "reason": expected_reason}
