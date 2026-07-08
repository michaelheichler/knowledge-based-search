# ruff: noqa: ANN001, ANN201, ANN202, BLE001, PLR0911, TRY300

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import rag  # type: ignore[import-not-found]
import search_core  # type: ignore[import-not-found]
import state as context_state  # type: ignore[import-not-found]

OK = 0
UNEXPECTED = 1
BAD_ARGS = 2
DAEMON_DOWN = 3
NETWORK_FAILURE = 4
REF_NOT_FOUND = 5

DEFAULT_CONFIG = {"searxng_url": "https://endianness.de", "duckduckgo": True}


class BadArgsError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BadArgsError(message)


def load_config():
    config = dict(DEFAULT_CONFIG)
    raw = os.environ.get("KBS_CONFIG")
    data = (
        _read_config(raw)
        if raw
        else _read_config(Path(__file__).with_name("config.json"))
    )
    if isinstance(data, dict):
        config.update(data)
    return config


def _read_config(value):
    try:
        text = str(value)
        if text and text.strip().startswith("{"):
            return json.loads(text)
        path = Path(text)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return None


def _parser():
    parser = Parser(prog="kbs")
    sub = parser.add_subparsers(dest="command", required=True)
    _query_command(sub, "quick", "quick ranked search", default_limit=8)
    _query_command(sub, "search", "search with summary", default_limit=5)
    get = sub.add_parser("get")
    get.add_argument("ref")
    get.add_argument("--json", action="store_true")
    deep = _query_command(sub, "deep", "bounded deep research", default_limit=None)
    deep.add_argument("--max-rounds", type=int, default=3)
    context = _query_command(sub, "context", "context-aware search", default_limit=None)
    context.add_argument("--context", default="")
    context.add_argument("--max-rounds", type=int, default=3)
    context.add_argument("--per-engine", type=int, default=20)
    context.add_argument("--fetch-top-k", type=int, default=5)
    context.add_argument("--session")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    daemon = sub.add_parser("daemon")
    daemon_sub = daemon.add_subparsers(dest="daemon_command", required=True)
    status = daemon_sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    return parser


def _query_command(sub, name, help_text, default_limit):
    command = sub.add_parser(name, help=help_text)
    command.add_argument("query", nargs="*")
    command.add_argument("--json", action="store_true")
    if default_limit is not None:
        command.add_argument("--num-results", type=int, default=default_limit)
    return command


def _query(parts, stdin):
    if len(parts) == 1 and parts[0] == "-":
        return stdin.read().strip()
    return " ".join(parts).strip()


def _render(data):
    if "results" in data:
        lines = []
        for index, item in enumerate(data["results"], 1):
            lines.append(f"{index}. {item.get('title', '')}")
            lines.append(f"   {item.get('url', '')}")
            snippet = item.get("snippet", "")
            if snippet:
                lines.append(f"   {snippet}")
        return "\n".join(lines)
    if "sections" in data:
        parts = [_render_summary(data)]
        parts.extend(
            f"\n## {section.get('heading', '')}\n{section.get('content', '')}"
            for section in data.get("sections", [])
        )
        return "\n".join(part for part in parts if part.strip())
    if "page_content" in data:
        return f"Source: {data.get('source_url', '')}\n\n{data.get('page_content', '')}".strip()
    return _render_summary(data)


def _render_summary(data):
    lines = []
    summary = data.get("summary", "")
    if summary:
        lines.append(summary)
    citations = data.get("citations", [])
    if citations:
        lines.append("\nSources:")
        for index, item in enumerate(citations, 1):
            lines.append(
                f"{index}. {item.get('title', '')} {item.get('url', '')}".rstrip()
            )
    if not lines:
        lines.extend(f"{key}: {value}" for key, value in data.items())
    return "\n".join(lines)


def _emit(data, as_json, stdout):
    text = json.dumps(data, sort_keys=True) if as_json else _render(data)
    if text:
        stdout.write(text + "\n")


def _examples():
    return [
        "kbs quick climate data",
        "kbs search climate data",
        "kbs get https://example.com",
        "kbs deep climate data",
        "kbs context climate --context research --session demo",
        "kbs doctor",
    ]


def _kbs_path():
    return str(Path(__file__).resolve().parents[1] / "bin" / "kbs")


def _path_discovery():
    found = shutil.which("kbs")
    return {
        "which_kbs": found or "",
        "expected_kbs_path": _kbs_path(),
        "on_path": found is not None,
    }


def _doctor():
    path = context_state.state_file()
    config = load_config()
    daemon = _daemon_status()
    return {
        "status": "ok",
        "kbs_path": _kbs_path(),
        "state_path": str(path),
        "socket_path": daemon["socket_path"],
        "daemon": daemon,
        "model_warm": daemon.get("model_warm"),
        "path_discovery": _path_discovery(),
        "config_source": os.environ.get("KBS_CONFIG", "server/config.json"),
        "searxng_url": config.get("searxng_url", ""),
        "examples": _examples(),
    }


def _daemon_status():
    status = rag.daemon_status()
    status["code"] = OK if status.get("status") == "alive" else DAEMON_DOWN
    status["state_path"] = str(context_state.state_file())
    status["path_discovery"] = _path_discovery()
    status["examples"] = _examples()
    return status


def _dispatch(args, stdin):
    config = load_config()
    if args.command == "quick":
        return search_core.quick_web_search(
            _query(args.query, stdin), config, args.num_results
        )
    if args.command == "search":
        return search_core.web_search(
            _query(args.query, stdin), config, args.num_results
        )
    if args.command == "get":
        if args.ref in search_core.RESULT_URLS or args.ref.startswith(
            ("http://", "https://")
        ):
            return search_core.get_content(args.ref)
        raise KeyError(args.ref)
    if args.command == "deep":
        return search_core.deep_research(
            _query(args.query, stdin), config, args.max_rounds
        )
    if args.command == "context":
        return search_core.deep_context_aware_search(
            _query(args.query, stdin),
            config,
            args.context,
            args.max_rounds,
            args.per_engine,
            args.fetch_top_k,
            args.session,
        )
    if args.command == "doctor":
        return _doctor()
    return _daemon_status()


def main(argv=None, stdin=None, stdout=None, stderr=None):
    argv = sys.argv[1:] if argv is None else argv
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    started = time.perf_counter()
    try:
        args = _parser().parse_args(argv)
        data = _dispatch(args, stdin)
        if args.command == "daemon" and args.daemon_command == "status":
            _emit(data, args.json, stdout)
            return OK if data.get("status") == "alive" else DAEMON_DOWN
        _emit(data, getattr(args, "json", False), stdout)
        return OK
    except BadArgsError as exc:
        stderr.write(f"bad-args: {exc}\n")
        return BAD_ARGS
    except KeyError as exc:
        stderr.write(f"ref-not-found: {exc.args[0]}\n")
        return REF_NOT_FOUND
    except BrokenPipeError:
        return OK
    except OSError as exc:
        stderr.write(f"network-failure: {exc}\n")
        return NETWORK_FAILURE
    except Exception as exc:
        stderr.write(f"unexpected-error: {exc}\n")
        stderr.write(f"elapsed_ms={int((time.perf_counter() - started) * 1000)}\n")
        return UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
