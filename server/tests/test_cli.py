import ast
import importlib
import io
import json
from pathlib import Path

cli = importlib.import_module("cli")
rag = importlib.import_module("rag")
search_context = importlib.import_module("search_context")
search_core = importlib.import_module("search_core")
search_deep = importlib.import_module("search_deep")


def run_cli(argv, stdin="") -> tuple:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli.main(argv, io.StringIO(stdin), stdout, stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def _fake_quick(query, config, num_results=8):
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


def _fake_search(query, config, num_results=5):
    return {
        "summary": f"Summary {query} {num_results}",
        "citations": [{"title": "Source", "url": "https://example.com/source"}],
        "result_ids": ["r1"],
    }


def _fake_get(ref, session=None):
    if ref == "r404":
        raise KeyError(ref)
    return {"source_url": ref, "page_content": "Page text"}


def _fake_deep(query, config, max_rounds=3):
    return {
        "summary": f"Deep {query} {max_rounds}",
        "sections": [],
        "citations": [],
    }


def _fake_context(
    query, config, context="", max_rounds=3, per_engine=20, fetch_top_k=5, session=None
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


def install_core_stubs(monkeypatch) -> None:
    monkeypatch.setattr(search_core, "quick_web_search", _fake_quick)
    monkeypatch.setattr(search_core, "web_search", _fake_search)
    monkeypatch.setattr(search_core, "get_content", _fake_get)
    monkeypatch.setattr(search_deep, "deep_research", _fake_deep)
    monkeypatch.setattr(search_context, "deep_context_aware_search", _fake_context)
    search_core.RESULT_URLS.clear()


def test_config_resolution_prefers_env_then_user_config(monkeypatch, tmp_path) -> None:
    home = tmp_path / "home"
    user_config = home / ".config" / "kbs" / "config.json"
    user_config.parent.mkdir(parents=True)
    user_config.write_text(
        json.dumps({"duckduckgo": False, "searxng_url": "https://user.test"}),
        encoding="utf-8",
    )
    env_config = tmp_path / "env.json"
    env_config.write_text(
        json.dumps({"searxng_url": "https://env-path.test"}), encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))

    monkeypatch.setenv("KBS_CONFIG", '{"searxng_url": "https://env-json.test"}')
    assert cli.load_config()["searxng_url"] == "https://env-json.test"
    monkeypatch.setenv("KBS_CONFIG", str(env_config))
    assert cli.load_config()["searxng_url"] == "https://env-path.test"
    monkeypatch.delenv("KBS_CONFIG")
    assert cli.load_config()["searxng_url"] == "https://user.test"
    assert "searxng_url" not in cli.DEFAULT_CONFIG


def test_invalid_explicit_config_returns_bad_args(monkeypatch) -> None:
    monkeypatch.setenv("KBS_CONFIG", "{not-json")

    code, stdout, stderr = run_cli(["doctor", "--json"])

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert "KBS_CONFIG must be valid JSON" in stderr


def test_doctor_redacts_inline_config_secret(monkeypatch) -> None:
    secret = "secret-google-api-key"
    config = json.dumps({"google_api_key": secret, "duckduckgo": True})
    monkeypatch.setenv("KBS_CONFIG", config)

    code, stdout, stderr = run_cli(["doctor", "--json"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert json.loads(stdout)["config_source"] == "environment-json"
    assert secret not in stdout
    assert config not in stdout


def test_quick_markdown_output(monkeypatch) -> None:
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["quick", "alpha", "beta", "--num-results", "2"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert stdout == ("1. Quick alpha beta\n   https://example.com/quick\n   limit 2\n")


def test_rendered_confidence_includes_numeric_trust() -> None:
    item = {
        "title": "Trusted source",
        "url": "https://example.com",
        "confidence": "primary",
        "trust": 95,
    }

    assert "confidence: primary (trust 95)" in cli._render_results([item])
    assert "[confidence: primary (trust 95)]" in cli._source_line(1, item)


def test_search_json_output_and_stdin(monkeypatch) -> None:
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["search", "-", "--json"], stdin="from stdin")

    assert code == cli.SUCCESS
    assert stderr == ""
    assert stdout == (
        '{"citations": [{"title": "Source", "url": "https://example.com/source"}], '
        '"result_ids": ["r1"], "summary": "Summary from stdin 5"}\n'
    )


def test_query_after_double_dash(monkeypatch) -> None:
    install_core_stubs(monkeypatch)

    code, stdout, stderr = run_cli(["quick", "--", "--literal"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert "Quick --literal" in stdout


def test_platform_requires_scientific() -> None:
    code, stdout, stderr = run_cli(["quick", "query", "--platform", "arxiv"])

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert "--platform requires --scientific" in stderr


def test_unknown_platform_rejected() -> None:
    code, stdout, stderr = run_cli(
        ["quick", "query", "--scientific", "--platform", "openalex"]
    )

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert "openalex" in stderr
    assert "arxiv" in stderr
    assert "library" in stderr


def test_plan_rejects_scientific_flag() -> None:
    code, stdout, stderr = run_cli(["plan", "query", "--scientific"])

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert "unrecognized arguments" in stderr


def test_scientific_flag_threads_to_search_core(monkeypatch) -> None:
    captured = {}

    def fake_quick(query, config, num_results=8, **options) -> dict:
        captured.update(
            query=query, config=config, num_results=num_results, options=options
        )
        return {"results": []}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)
    code, stdout, stderr = run_cli(
        ["quick", "query", "--scientific", "--platform", "arxiv", "--platform", "library"]
    )
    assert code == cli.SUCCESS
    assert stdout == ""
    assert stderr == ""
    assert captured["options"] == {"scientific": True, "platform": ["arxiv", "library"]}


def test_injection_shaped_tokens_are_plain_query(monkeypatch) -> None:
    captured = []

    def fake_quick(query, config, num_results=8) -> dict:
        captured.append(query)
        return {"results": []}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)

    code, _, stderr = run_cli(["quick", "$(touch hacked)", "&&", "whoami"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert captured == ["$(touch hacked) && whoami"]


def test_stdin_injection_shaped_text_is_plain_query(monkeypatch) -> None:
    captured = []

    def fake_search(query, config, num_results=5) -> dict:
        captured.append(query)
        return {"summary": "", "citations": [], "result_ids": []}

    monkeypatch.setattr(search_core, "web_search", fake_search)

    code, _, stderr = run_cli(["search", "-"], stdin="$(touch hacked) && whoami")

    assert code == cli.SUCCESS
    assert stderr == ""
    assert captured == ["$(touch hacked) && whoami"]


def test_get_accepts_url_and_missing_ref_has_no_traceback(monkeypatch) -> None:
    install_core_stubs(monkeypatch)

    ok, stdout, stderr = run_cli(["get", "https://example.com/page"])
    missing, _, missing_err = run_cli(["get", "r404"])

    assert ok == cli.SUCCESS
    assert "Page text" in stdout
    assert stderr == ""
    assert missing == cli.REF_NOT_FOUND
    assert "ref-not-found: r404" in missing_err
    assert "Traceback" not in missing_err


def test_deep_and_context_commands(monkeypatch) -> None:
    install_core_stubs(monkeypatch)

    deep_code, deep_out, _ = run_cli(["deep", "alpha", "--max-rounds", "2"])
    context_code, context_out, _ = run_cli(
        ["context", "alpha", "--context", "ctx", "--session", "s1"]
    )

    assert deep_code == cli.SUCCESS
    assert "Deep alpha 2" in deep_out
    assert context_code == cli.SUCCESS
    assert "https://example.com/context" in context_out
    assert "s1" in context_out


def test_doctor_and_daemon_status_json(monkeypatch, tmp_path) -> None:
    socket_path = str(tmp_path / "rag.sock")
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(rag, "default_sock_path", lambda: socket_path)

    doctor_code, doctor_out, _ = run_cli(["doctor", "--json"])
    daemon_code, daemon_out, _ = run_cli(["daemon", "status", "--json"])

    doctor = json.loads(doctor_out)
    daemon = json.loads(daemon_out)

    assert doctor_code == cli.SUCCESS
    assert doctor["state_path"] == str(tmp_path / "state.json")
    assert doctor["socket_path"] == socket_path
    assert "path_discovery" in doctor
    assert "model_warm" in doctor
    assert "available" in doctor["dense_ranking"]
    assert doctor["dense_ranking"]["reason"]
    assert "kbs doctor" in doctor["examples"]
    assert "config_source" in doctor
    assert daemon_code == cli.DAEMON_DOWN
    assert daemon["persistent_process"] == "rag_host"
    assert daemon["status"] == "down"
    assert daemon["state_path"] == str(tmp_path / "state.json")


def _alive_daemon_status(socket_path):
    return {
        "status": "alive",
        "persistent_process": "rag_host",
        "socket_path": str(socket_path),
        "socket_exists": True,
        "socket_stale": False,
        "model_warm": True,
        "last_request_at": 12.0,
        "idle_seconds": 0.5,
    }


def test_daemon_status_reports_socket_state(monkeypatch, tmp_path) -> None:
    socket_path = tmp_path / "rag.sock"
    monkeypatch.setattr(rag, "daemon_status", lambda: _alive_daemon_status(socket_path))
    code, stdout, stderr = run_cli(["daemon", "status"])
    json_code, json_out, _ = run_cli(["daemon", "status", "--json"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert "status: alive" in stdout
    assert "model_warm: True" in stdout
    assert str(socket_path) in stdout
    assert json_code == cli.SUCCESS
    assert '"code": 0' in json_out
    assert '"path_discovery"' in json_out


def test_url_metacharacters_are_data(monkeypatch) -> None:
    captured = []

    def fake_get(ref, session=None) -> dict:
        captured.append(ref)
        return {"source_url": ref, "page_content": "Page text"}

    monkeypatch.setattr(search_core, "get_content", fake_get)
    url = "https://x.com/?a=1&b=$(whoami)#frag"

    code, _, stderr = run_cli(["get", url])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert captured == [url]


def test_newlines_in_query_are_data(monkeypatch) -> None:
    captured = []

    def fake_search(query, config, num_results=5) -> dict:
        captured.append(query)
        return {"summary": "", "citations": [], "result_ids": []}

    monkeypatch.setattr(search_core, "web_search", fake_search)

    code, _, stderr = run_cli(["search", "line1\nline2"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert captured == ["line1\nline2"]


def test_render_golden_outputs() -> None:
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


def test_context_render_includes_summary_citations_and_suppressed_count() -> None:
    data = {
        "results": [{"title": "T", "url": "https://u", "snippet": "S"}],
        "summary": "Fetched context summary",
        "citations": [{"title": "Source", "url": "https://source"}],
        "already_seen_suppressed": 3,
    }

    rendered = cli._render(data)

    assert "Fetched context summary" in rendered
    assert "1. Source https://source" in rendered
    assert "Previously seen results suppressed: 3" in rendered


def test_all_provider_failure_maps_to_network_exit(monkeypatch) -> None:
    def fail(query, k=10, timeout=12) -> None:
        raise OSError("provider offline")

    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: {"duckduckgo": True, "mwmbl": False, "wikipedia": False},
    )
    monkeypatch.setattr(search_core.engines, "duckduckgo", fail)
    code, stdout, stderr = run_cli(["quick", "query", "--raw"])

    assert code == cli.NETWORK_FAILURE
    assert stdout == ""
    assert "network-failure: all configured search providers failed" in stderr


def test_blocked_duckduckgo_maps_to_network_exit(monkeypatch) -> None:
    """A captcha is provider failure, not an honest empty result set."""
    blocked = "<html>captcha unusual traffic</html>"
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: {"duckduckgo": True, "mwmbl": False, "wikipedia": False},
    )
    monkeypatch.setattr(search_core.engines, "_get", lambda *args, **kwargs: blocked)

    code, stdout, stderr = run_cli(["quick", "query", "--raw"])

    assert code == cli.NETWORK_FAILURE
    assert stdout == ""
    assert "all configured search providers failed" in stderr


def test_blocked_get_reports_policy_error(monkeypatch) -> None:
    def block(url, max_chars) -> None:
        raise cli.fetch.BlockedFetchError("private addresses are not allowed")

    monkeypatch.setattr(search_core, "fetch_clean", block)
    code, stdout, stderr = run_cli(["get", "http://127.0.0.1/"])

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert stderr == "blocked-fetch: private addresses are not allowed\n"


def test_get_passes_explicit_session(monkeypatch) -> None:
    captured = []

    def fake_get(ref, session=None) -> dict:
        captured.append((ref, session))
        return {"source_url": "https://example.com", "page_content": "text"}

    monkeypatch.setattr(search_core, "get_content", fake_get)
    code, _, stderr = run_cli(["get", "r1", "--session", "s1"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert captured == [("r1", "s1")]


def test_bad_args_exit_code_uses_injected_stderr() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = cli.main(
        ["search", "--num-results", "bad", "alpha"], io.StringIO(), stdout, stderr
    )

    assert code == cli.BAD_ARGS
    assert stdout.getvalue() == ""
    assert "bad-args:" in stderr.getvalue()


def test_bin_kbs_entrypoint_is_executable() -> None:
    entrypoint = Path("bin/kbs")

    assert entrypoint.exists()
    assert entrypoint.stat().st_mode & 0o111


def test_cli_uses_no_shell_true() -> None:
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


def test_cli_imports_no_subprocess() -> None:
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


def test_plan_markdown_output() -> None:
    code, stdout, stderr = run_cli(["plan", "verify", "a", "viral", "claim"])

    assert code == cli.SUCCESS
    assert stderr == ""
    assert stdout == (
        "Route: fact-checking\n"
        "\n"
        "References:\n"
        "- references/exposingtheinvisible/fact-checking.md\n"
        "- references/exposingtheinvisible/evaluate-evidence.md\n"
        "\n"
        "Commands:\n"
        "kbs search 'verify a viral claim' fact check\n"
        "kbs deep 'verify a viral claim'\n"
    )


def test_plan_json_output() -> None:
    code, stdout, stderr = run_cli(["plan", "who owns example.com", "--json"])

    assert code == cli.SUCCESS
    assert stderr == ""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError("CLI emitted invalid JSON") from exc
    assert data["route"] == "company-domain"
    assert "exposingtheinvisible/companies.md" in data["references"]
    assert any("site:" in command for command in data["commands"])
    assert "company-domain" in data["matched_topics"]


def test_plan_empty_query_bad_args() -> None:
    code, stdout, stderr = run_cli(["plan"])

    assert code == cli.BAD_ARGS
    assert stdout == ""
    assert "bad-args:" in stderr
    assert "Traceback" not in stderr


def test_scientific_bucket_rendering_includes_headers_and_items() -> None:
    data = {
        "buckets": [
            {
                "name": "Physics",
                "results": [
                    {"title": "Paper", "url": "https://example.com/paper"}
                ],
            },
            {"name": "Uncategorized", "results": []},
        ]
    }

    rendered = cli._render(data)

    assert "## Physics" in rendered
    assert "1. Paper" in rendered
    assert "## Uncategorized" in rendered
