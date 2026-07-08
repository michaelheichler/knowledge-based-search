# ruff: noqa: PLR0913

import ast
import importlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
cli = importlib.import_module("cli")
rag = importlib.import_module("rag")
search_core = importlib.import_module("search_core")


def run_cli(argv, stdin=""):
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli.main(argv, io.StringIO(stdin), stdout, stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def install_core_stubs(monkeypatch):
    def fake_quick(query, config, num_results=8):
        return {
            "results": [
                {
                    "title": f"Quick {query}",
                    "url": "https://example.com/quick",
                    "snippet": f"limit {num_results}",
                    "engine": "stub",
                }
            ]
        }

    def fake_search(query, config, num_results=5):
        return {
            "summary": f"Summary {query} {num_results}",
            "citations": [{"title": "Source", "url": "https://example.com/source"}],
            "result_ids": ["r1"],
        }

    def fake_get(ref):
        return {"source_url": ref, "page_content": "Page text"}

    def fake_deep(query, config, max_rounds=3):
        return {
            "summary": f"Deep {query} {max_rounds}",
            "sections": [],
            "citations": [],
        }

    def fake_context(
        query,
        config,
        context="",
        max_rounds=3,
        per_engine=20,
        fetch_top_k=5,
        session=None,
    ):
        return {
            "query": query,
            "context": context,
            "results": [
                {
                    "title": "Ctx",
                    "url": "https://example.com/context",
                    "snippet": session or "",
                }
            ],
            "already_seen_suppressed": 0,
            "summary": "",
            "citations": [],
            "result_ids": [],
        }

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)
    monkeypatch.setattr(search_core, "web_search", fake_search)
    monkeypatch.setattr(search_core, "get_content", fake_get)
    monkeypatch.setattr(search_core, "deep_research", fake_deep)
    monkeypatch.setattr(search_core, "deep_context_aware_search", fake_context)
    search_core.RESULT_URLS.clear()


def test_quick_markdown_output(monkeypatch):
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["quick", "alpha", "beta", "--num-results", "2"])

    assert code == cli.OK
    assert stderr == ""
    assert stdout == ("1. Quick alpha beta\n   https://example.com/quick\n   limit 2\n")


def test_search_json_output_and_stdin(monkeypatch):
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["search", "-", "--json"], stdin="from stdin")

    assert code == cli.OK
    assert stderr == ""
    assert stdout == (
        '{"citations": [{"title": "Source", "url": "https://example.com/source"}], '
        '"result_ids": ["r1"], "summary": "Summary from stdin 5"}\n'
    )


def test_query_after_double_dash(monkeypatch):
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["quick", "--", "--literal"])

    assert code == cli.OK
    assert stderr == ""
    assert "Quick --literal" in stdout


def test_injection_shaped_tokens_are_plain_query(monkeypatch):
    captured = []

    def fake_quick(query, config, num_results=8):
        captured.append(query)
        return {"results": []}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)

    code, _, stderr = run_cli(["quick", "$(touch hacked)", "&&", "whoami"])

    assert code == cli.OK
    assert stderr == ""
    assert captured == ["$(touch hacked) && whoami"]


def test_stdin_injection_shaped_text_is_plain_query(monkeypatch):
    captured = []

    def fake_search(query, config, num_results=5):
        captured.append(query)
        return {"summary": "", "citations": [], "result_ids": []}

    monkeypatch.setattr(search_core, "web_search", fake_search)

    code, _, stderr = run_cli(["search", "-"], stdin="$(touch hacked) && whoami")

    assert code == cli.OK
    assert stderr == ""
    assert captured == ["$(touch hacked) && whoami"]


def test_get_accepts_url_and_missing_ref_has_no_traceback(monkeypatch):
    install_core_stubs(monkeypatch)

    ok, stdout, stderr = run_cli(["get", "https://example.com/page"])
    missing, _, missing_err = run_cli(["get", "r404"])

    assert ok == cli.OK
    assert "Page text" in stdout
    assert stderr == ""
    assert missing == cli.REF_NOT_FOUND
    assert "ref-not-found: r404" in missing_err
    assert "Traceback" not in missing_err


def test_deep_and_context_commands(monkeypatch):
    install_core_stubs(monkeypatch)

    deep_code, deep_out, _ = run_cli(["deep", "alpha", "--max-rounds", "2"])
    context_code, context_out, _ = run_cli(
        ["context", "alpha", "--context", "ctx", "--session", "s1"]
    )

    assert deep_code == cli.OK
    assert "Deep alpha 2" in deep_out
    assert context_code == cli.OK
    assert "https://example.com/context" in context_out
    assert "s1" in context_out


def test_doctor_and_daemon_status_json(monkeypatch, tmp_path):
    socket_path = str(tmp_path / "rag.sock")
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(rag, "default_sock_path", lambda: socket_path)

    doctor_code, doctor_out, _ = run_cli(["doctor", "--json"])
    daemon_code, daemon_out, _ = run_cli(["daemon", "status", "--json"])

    try:
        doctor = json.loads(doctor_out)
        daemon = json.loads(daemon_out)
    except json.JSONDecodeError as exc:
        raise AssertionError("CLI emitted invalid JSON") from exc

    assert doctor_code == cli.OK
    assert doctor["state_path"] == str(tmp_path / "state.json")
    assert doctor["socket_path"] == socket_path
    assert "path_discovery" in doctor
    assert "model_warm" in doctor
    assert "kbs doctor" in doctor["examples"]
    assert "config_source" in doctor
    assert daemon_code == cli.DAEMON_DOWN
    assert daemon["persistent_process"] == "rag_host"
    assert daemon["status"] == "down"
    assert daemon["state_path"] == str(tmp_path / "state.json")


def test_daemon_status_reports_socket_state(monkeypatch, tmp_path):
    socket_path = tmp_path / "rag.sock"
    monkeypatch.setattr(
        rag,
        "daemon_status",
        lambda: {
            "status": "alive",
            "persistent_process": "rag_host",
            "socket_path": str(socket_path),
            "socket_exists": True,
            "socket_stale": False,
            "model_warm": True,
            "last_request_at": 12.0,
            "idle_seconds": 0.5,
        },
    )

    code, stdout, stderr = run_cli(["daemon", "status"])
    json_code, json_out, _ = run_cli(["daemon", "status", "--json"])

    assert code == cli.OK
    assert stderr == ""
    assert "status: alive" in stdout
    assert "model_warm: True" in stdout
    assert str(socket_path) in stdout
    assert json_code == cli.OK
    assert '"code": 0' in json_out
    assert '"path_discovery"' in json_out


def test_url_metacharacters_are_data(monkeypatch):
    captured = []

    def fake_get(ref):
        captured.append(ref)
        return {"source_url": ref, "page_content": "Page text"}

    monkeypatch.setattr(search_core, "get_content", fake_get)
    url = "https://x.com/?a=1&b=$(whoami)#frag"

    code, _, stderr = run_cli(["get", url])

    assert code == cli.OK
    assert stderr == ""
    assert captured == [url]


def test_newlines_in_query_are_data(monkeypatch):
    captured = []

    def fake_search(query, config, num_results=5):
        captured.append(query)
        return {"summary": "", "citations": [], "result_ids": []}

    monkeypatch.setattr(search_core, "web_search", fake_search)

    code, _, stderr = run_cli(["search", "line1\nline2"])

    assert code == cli.OK
    assert stderr == ""
    assert captured == ["line1\nline2"]


def test_render_golden_outputs():
    assert cli._render(
        {"results": [{"title": "T", "url": "https://u", "snippet": "S"}]}
    ) == ("1. T\n   https://u\n   S")
    assert cli._render(
        {"summary": "Sum", "citations": [{"title": "Src", "url": "https://s"}]}
    ) == ("Sum\n\nSources:\n1. Src https://s")
    assert cli._render({"source_url": "https://u", "page_content": "Body"}) == (
        "Source: https://u\n\nBody"
    )
    assert cli._render(
        {"summary": "Deep", "sections": [{"heading": "H", "content": "C"}]}
    ) == ("Deep\n\n## H\nC")
    assert cli._render({"status": "down", "socket_path": "/run/kbs.sock"}) == (
        "status: down\nsocket_path: /run/kbs.sock"
    )


def test_bad_args_exit_code_uses_injected_stderr():
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = cli.main(
        ["search", "--num-results", "bad", "alpha"], io.StringIO(), stdout, stderr
    )

    assert code == cli.BAD_ARGS
    assert stdout.getvalue() == ""
    assert "bad-args:" in stderr.getvalue()


def test_bin_kbs_entrypoint_is_executable():
    entrypoint = Path("bin/kbs")

    assert entrypoint.exists()
    assert entrypoint.stat().st_mode & 0o111


def test_cli_uses_no_shell_true():
    tree = ast.parse(Path("server/cli.py").read_text(encoding="utf-8"))
    shell_true = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.keyword)
        and node.arg == "shell"
        and isinstance(node.value, ast.Constant)
        and bool(node.value.value)
    ]

    assert shell_true == []


def test_cli_imports_no_subprocess():
    tree = ast.parse(Path("server/cli.py").read_text(encoding="utf-8"))
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imported_from = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]

    assert "subprocess" not in imports
    assert "subprocess" not in imported_from
