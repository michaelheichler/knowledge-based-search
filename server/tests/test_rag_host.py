# ruff: noqa
import contextlib
import importlib
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import rag

_HOST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag_host.py")


def _paths():
    root = tempfile.mkdtemp(prefix="kbs-rag-")
    return os.path.join(root, "rag.sock"), os.path.join(root, "refs")


def _env():
    env = os.environ.copy()
    env["KBS_FAKE_MODEL"] = "1"
    return env


def _fake_host():
    os.environ["KBS_FAKE_MODEL"] = "1"
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import rag_host

    return importlib.reload(rag_host)


def test_fake_host_embed_and_rerank_roundtrip():
    host = _fake_host()
    ref_dir = tempfile.mkdtemp(prefix="kbs-rag-refs-")
    server = type("Server", (), {"_shutting_down": False})()
    vectors = host._dispatch(
        {"op": "embed", "texts": ["alpha", "beta"]}, ref_dir, server
    )["vectors"]
    ranked = host._dispatch(
        {"op": "rerank", "query": "alpha", "documents": ["alpha doc", "beta doc"]},
        ref_dir,
        server,
    )["results"]
    assert len(vectors) == 2
    assert all(isinstance(value, float) for value in vectors[0])
    assert sorted(row["index"] for row in ranked) == [0, 1]
    assert all(set(row) == {"index", "score"} for row in ranked)


def test_rag_host_paths_are_portable():
    root = Path(__file__).resolve().parents[1]
    forbidden = "/".join(["", "Users", "michael", "dev", "skills"])
    for name in ("rag.py", "rag_host.py"):
        text = (root / name).read_text(encoding="utf-8")
        assert forbidden not in text


def test_status_reports_alive_after_prior_embed():
    host = _fake_host()
    sock_path, ref_dir = _paths()
    server = host._Server(sock_path, ref_dir)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert rag.embed(["alpha"], sock_path=sock_path, ref_dir=ref_dir) is not None
        status = rag.daemon_status(sock_path)
    finally:
        server.shutdown()
        thread.join(timeout=1)
        server.server_close()
        with contextlib.suppress(OSError):
            os.remove(sock_path)
    assert status["status"] == "alive"
    assert status["model_warm"]
    assert status["last_request_at"] is not None


def test_spawn_once_reuses_warm_process(monkeypatch):
    sock_path, ref_dir = _paths()
    spawned = []
    state = {"live": False}

    conn = object()

    class Popen:
        def __init__(self, argv, **kwargs):
            spawned.append(argv)
            state["live"] = True

    monkeypatch.setattr(rag, "_connect", lambda path: conn if state["live"] else None)
    monkeypatch.setattr(
        rag,
        "_poll_for_host",
        lambda path, stop_if_absent: conn if state["live"] else None,
    )
    monkeypatch.setattr(rag.subprocess, "Popen", Popen)

    first = rag._connect_or_spawn(
        sock_path, ref_dir, ["python", "server/rag_host.py"], _env()
    )
    second = rag._connect_or_spawn(
        sock_path, ref_dir, ["python", "server/rag_host.py"], _env()
    )

    assert first is not None
    assert second is not None
    assert len(spawned) == 1


def test_spawn_poll_waits_when_socket_is_absent(monkeypatch):
    sock_path, ref_dir = _paths()
    calls = []

    class Conn:
        pass

    def connect(path):
        return None

    def poll(path, stop_if_absent):
        calls.append(stop_if_absent)
        return Conn() if len(calls) == 2 else None

    monkeypatch.setattr(rag, "_connect", connect)
    monkeypatch.setattr(rag, "_poll_for_host", poll)
    monkeypatch.setattr(rag.subprocess, "Popen", lambda *args, **kwargs: None)

    result = rag._connect_or_spawn(
        sock_path, ref_dir, ["python", "server/rag_host.py"], _env()
    )

    assert result is not None
    assert calls == [True, False]


def test_default_host_spawn_uses_kbs_python(monkeypatch):
    sock_path, ref_dir = _paths()
    spawned = []

    monkeypatch.setenv("KBS_PYTHON", "/tmp/kbs-python")
    monkeypatch.setattr(rag, "_connect", lambda path: None)
    monkeypatch.setattr(rag, "_poll_for_host", lambda path, stop_if_absent: None)
    monkeypatch.setattr(
        rag.subprocess, "Popen", lambda argv, **kwargs: spawned.append(argv)
    )

    rag._connect_or_spawn(sock_path, ref_dir, None, _env())

    assert spawned[0][0] == "/tmp/kbs-python"


def test_rag_host_loader_dir_uses_env(monkeypatch):
    monkeypatch.setenv("KBS_LOADER_DIR", "/tmp/loader")
    host = _fake_host()

    assert host._loader_dir() == "/tmp/loader"


def test_run_unlinks_the_socket_after_a_graceful_shutdown(monkeypatch):
    host = _fake_host()
    sock_path, ref_dir = _paths()
    unlinked = []

    class Server:
        def __init__(self, path, refs):
            self.path = path

        def serve_forever(self, poll_interval=0.2):
            pass

        def server_close(self):
            pass

    def unlink(path):
        unlinked.append(path)

    monkeypatch.setattr(host, "_Server", Server)
    monkeypatch.setattr(host.os, "unlink", unlink)
    monkeypatch.setattr(host.os, "makedirs", lambda *args, **kwargs: None)
    monkeypatch.setattr(host.signal, "signal", lambda *args, **kwargs: None)

    host._run(sock_path, ref_dir)

    assert unlinked == [Path(sock_path), Path(sock_path)]


def test_dead_socket_failure_returns_none():
    sock_path, ref_dir = _paths()
    Path(sock_path).write_text("dead", encoding="utf-8")
    result = rag.embed(
        ["alpha"],
        sock_path=sock_path,
        ref_dir=ref_dir,
        host_argv=["/missing/python", _HOST],
        env=_env(),
    )
    assert result is None
    Path(sock_path).unlink(missing_ok=True)


def test_connect_or_spawn_recovers_from_crashed_daemon_socket(monkeypatch):
    sock_path, ref_dir = _paths()
    dead = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    dead.bind(sock_path)
    dead.close()
    spawned = []

    class Conn:
        pass

    def popen(argv, **kwargs):
        assert not os.path.exists(sock_path)
        spawned.append(argv)

    monkeypatch.setattr(rag.subprocess, "Popen", popen)
    monkeypatch.setattr(rag, "_poll_for_host", lambda path, stop_if_absent: Conn())

    result = rag._connect_or_spawn(
        sock_path, ref_dir, ["python", "server/rag_host.py"], _env()
    )

    assert result is not None
    assert len(spawned) == 1


def test_idle_watchdog_uses_last_request_not_live_refs(monkeypatch):
    host = _fake_host()
    ref_dir = tempfile.mkdtemp(prefix="kbs-rag-refs-")
    calls = []
    counter = host.refcount.Refcount(ref_dir)
    counter.attach("pytest", "s1")
    monkeypatch.setattr(host, "_IDLE_SECS", 0.0)
    monkeypatch.setattr(host, "_IDLE_POLL_SECS", 0.0)
    monkeypatch.setattr(host, "_clear_mlx_cache", lambda: calls.append("clear"))

    class Server:
        _shutting_down = False
        _last_request_at = time.monotonic() - 10
        _active_requests = 0
        _request_lock = threading.Lock()

        def shutdown(self):
            calls.append("shutdown")

    server = Server()
    host._idle_watchdog(server, ref_dir)
    deadline = time.monotonic() + 1
    while calls != ["clear", "shutdown"] and time.monotonic() < deadline:
        time.sleep(0.01)

    assert calls == ["clear", "shutdown"]


def test_idle_watchdog_does_not_shutdown_during_active_request(monkeypatch):
    host = _fake_host()
    ref_dir = tempfile.mkdtemp(prefix="kbs-rag-refs-")
    calls = []
    monkeypatch.setattr(host, "_IDLE_SECS", 0.0)
    monkeypatch.setattr(host, "_IDLE_POLL_SECS", 0.01)
    monkeypatch.setattr(host, "_clear_mlx_cache", lambda: calls.append("clear"))

    class Server:
        _shutting_down = False
        _last_request_at = time.monotonic() - 10
        _active_requests = 1
        _request_lock = threading.Lock()

        def shutdown(self):
            calls.append("shutdown")

    server = Server()
    thread = threading.Thread(
        target=host._idle_watchdog, args=(server, ref_dir), daemon=True
    )
    thread.start()
    time.sleep(0.05)
    server._shutting_down = True
    thread.join(timeout=1)

    assert calls == []


def test_release_last_ref_waits_for_idle_watchdog(monkeypatch):
    host = _fake_host()
    ref_dir = tempfile.mkdtemp(prefix="kbs-rag-refs-")
    calls = []
    monkeypatch.setattr(host.refcount, "_start_time", lambda pid: 1.0)

    class Server:
        _shutting_down = False

        def shutdown(self):
            calls.append("shutdown")

    server = Server()
    response = host._dispatch(
        {"op": "attach", "tool": "pytest", "session": "s1"}, ref_dir, server
    )
    released = host._dispatch(
        {"op": "release", "ref": response["ref"]}, ref_dir, server
    )
    time.sleep(0.05)
    assert released == {"released": True, "last": True}
    assert calls == []
