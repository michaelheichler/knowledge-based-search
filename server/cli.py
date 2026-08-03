# ruff: noqa: BLE001

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import enforce  # type: ignore[import-not-found]
import engines  # type: ignore[import-not-found]
import fetch  # type: ignore[import-not-found]
import method_index  # type: ignore[import-not-found]
import rag  # type: ignore[import-not-found]
import search_core  # type: ignore[import-not-found]
import state as context_state  # type: ignore[import-not-found]

SUCCESS = 0
UNEXPECTED = 1
BAD_ARGS = 2
DAEMON_DOWN = 3
NETWORK_FAILURE = 4
REF_NOT_FOUND = 5

DEFAULT_CONFIG = {"duckduckgo": True}


class BadArgsError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message) -> None:
        raise BadArgsError(message)


def _config_source():
    """Installed defaults stay last because explicit user intent must win."""
    raw = os.environ.get("KBS_CONFIG")
    if raw:
        kind = "environment-json" if raw.strip().startswith("{") else "path"
        return raw, kind
    user_config = Path.home() / ".config" / "kbs" / "config.json"
    if user_config.exists():
        return user_config, "xdg"
    legacy_config = Path(__file__).with_name("config.json")
    if legacy_config.exists():
        return legacy_config, "legacy"
    return None, "default"


def _config_path():
    """The raw source remains available because older callers lack source classification."""
    return _config_source()[0]


def load_config() -> dict:
    """Load the selected config over keyless defaults."""
    config = dict(DEFAULT_CONFIG)
    source, kind = _config_source()
    if source is None:
        return config
    data = _read_config(source)
    if not isinstance(data, dict):
        if kind in {"environment-json", "path"}:
            raise BadArgsError("KBS_CONFIG must be valid JSON or a readable JSON path")
        return config
    config.update(data)
    return config


def _read_config(value):
    """Both source forms share parsing to prevent precedence from changing JSON semantics."""
    try:
        text = str(value)
        if text and text.strip().startswith("{"):
            return json.loads(text)
        path = Path(text)
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return None


def _parser():
    parser = Parser(prog="kbs")
    sub = parser.add_subparsers(dest="command", required=True)
    _query_command(sub, "quick", "quick ranked search", default_limit=8)
    _query_command(sub, "search", "search with summary", default_limit=5)
    _query_command(sub, "plan", "reference-backed search recipes", default_limit=None)
    get = sub.add_parser("get")
    get.add_argument("ref")
    get.add_argument("--session")
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


def _query_command(sub, name, help_text, **options):
    default_limit = options.get("default_limit")
    command = sub.add_parser(name, help=help_text)
    command.add_argument("query", nargs="*")
    command.add_argument("--json", action="store_true")
    if name != "plan":
        command.add_argument("--raw", action="store_true")
        command.add_argument("--scientific", action="store_true")
        command.add_argument("--platform", action="append", default=None)
    if default_limit is not None:
        command.add_argument("--num-results", type=int, default=default_limit)
    return command


def _query(parts, stdin, raw=False):
    if len(parts) == 1 and parts[0] == "-":
        value = stdin.read()
    else:
        value = " ".join(parts)
    return value if raw else value.strip()


def _confidence_label(item):
    confidence = item.get("confidence")
    if not confidence:
        return ""
    trust = item.get("trust")
    return f"{confidence} (trust {trust})" if trust is not None else confidence


def _render_results(results):
    lines = []
    for index, item in enumerate(results, 1):
        lines.extend([f"{index}. {item.get('title', '')}", f"   {item.get('url', '')}"])
        confidence = _confidence_label(item)
        if confidence:
            lines.append(f"   confidence: {confidence}")
        snippet = item.get("snippet", "")
        if snippet:
            lines.append(f"   {snippet}")
    return "\n".join(lines)


def _render_context(data):
    """Fetched evidence stays visible because context work must not disappear from human output."""
    parts = [_render_results(data.get("results", []))]
    summary = data.get("summary", "")
    if summary:
        parts.append(f"Summary:\n{summary}")
    citations = data.get("citations", [])
    if citations:
        sources = ["Sources:"]
        sources.extend(
            _source_line(index, item) for index, item in enumerate(citations, 1)
        )
        parts.append("\n".join(sources))
    suppressed = data.get("already_seen_suppressed", 0)
    parts.append(f"Previously seen results suppressed: {suppressed}")
    return "\n\n".join(part for part in parts if part)


def _render(data):
    """This stays centralized because every command must expose enforcement metadata."""
    parts = [_render_body(data)]
    parts.extend(_render_correction(item) for item in data.get("corrections", []))
    quality = data.get("quality")
    if quality:
        parts.append(_render_quality(quality))
    return "\n".join(part for part in parts if part.strip())


def _render_body(data):
    """Layouts stay separate because shared metadata must be appended exactly once."""
    if "results" in data:
        if "already_seen_suppressed" in data:
            return _render_context(data)
        return _render_results(data["results"])
    if "sections" in data:
        parts = [_render_summary(data)]
        parts.extend(
            f"\n## {section.get('heading', '')}\n{section.get('content', '')}"
            for section in data.get("sections", [])
        )
        return "\n".join(part for part in parts if part.strip())
    if "page_content" in data:
        return f"Source: {data.get('source_url', '')}\n\n{data.get('page_content', '')}".strip()
    if "matched_topics" in data:
        return _render_plan(data)
    return _render_summary(data)


def _render_correction(item):
    """Each item stays compact because correction provenance consumes agent tokens."""
    return f"corrections: {item.get('before', '')} -> {item.get('after', '')} ({item.get('reason', '')})"


def _render_quality(quality):
    """One compact label is required because diversity text must not duplicate results."""
    diversity = quality.get("distinct_root_domains", 0)
    metric = quality.get("domain_metric", "root domains")
    flag = "low diversity" if quality.get("low_diversity") else "diverse"
    return f"quality: {flag}, {diversity} {metric}, {quality.get('verification', 'single-source')}"


def _render_plan(data):
    lines = [f"Route: {data['route']}", "", "References:"]
    lines.extend(f"- references/{ref}" for ref in data.get("references", []))
    lines.append("")
    lines.append("Commands:")
    lines.extend(data.get("commands", []))
    return "\n".join(lines)


def _source_line(index, item):
    """Confidence stays beside each citation because separated labels obscure attribution."""
    confidence = _confidence_label(item)
    label = f" [confidence: {confidence}]" if confidence else ""
    return f"{index}. {item.get('title', '')}{label} {item.get('url', '')}".rstrip()


def _render_summary(data):
    lines = []
    summary = data.get("summary", "")
    if summary:
        lines.append(summary)
    citations = data.get("citations", [])
    if citations:
        lines.append("\nSources:")
        for index, item in enumerate(citations, 1):
            lines.append(_source_line(index, item))
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
        "kbs plan trace username alice",
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
        "dense_ranking": rag.dense_ranking_status(),
        "path_discovery": _path_discovery(),
        "config_source": _config_source()[1],
        "searxng_url": config.get("searxng_url", ""),
        "examples": _examples(),
    }


def _daemon_status():
    status = rag.daemon_status()
    status["code"] = SUCCESS if status.get("status") == "alive" else DAEMON_DOWN
    status["state_path"] = str(context_state.state_file())
    status["path_discovery"] = _path_discovery()
    status["examples"] = _examples()
    return status


def _dispatch_query(args, stdin, config):
    """This boundary is shared because every query command needs identical enforcement."""
    if args.platform and not args.scientific:
        raise BadArgsError("--platform requires --scientific")
    valid_platforms = engines.SCIENTIFIC_PLATFORMS | {"library"}
    invalid = sorted(item for item in (args.platform or []) if item not in valid_platforms)
    if invalid:
        allowed = ", ".join(sorted(valid_platforms))
        raise BadArgsError(
            f"unknown platform {invalid[0]!r}; valid platforms: {allowed}"
        )
    literal = enforce.enforcement_disabled(args.raw)
    query = _query(args.query, stdin, literal)
    raw = {"raw": True} if args.raw else {}
    sci = {"scientific": True, "platform": args.platform} if args.scientific else {}
    if args.command == "quick":
        return search_core.quick_web_search(query, config, args.num_results, **raw, **sci)
    if args.command == "search":
        return search_core.web_search(query, config, args.num_results, **raw, **sci)
    if args.command == "deep":
        return search_core.deep_research(query, config, args.max_rounds, **raw, **sci)
    return search_core.deep_context_aware_search(
        query,
        config,
        args.context,
        args.max_rounds,
        args.per_engine,
        args.fetch_top_k,
        args.session,
        **raw,
        **sci,
    )


def _dispatch(args, stdin):
    """Search config stays lazy because commands without queries must not start providers."""
    if args.command in {"quick", "search", "deep", "context"}:
        return _dispatch_query(args, stdin, load_config())
    if args.command == "get":
        return search_core.get_content(args.ref, args.session)
    if args.command == "plan":
        try:
            return method_index.plan_search(_query(args.query, stdin))
        except ValueError as exc:
            raise BadArgsError(str(exc)) from exc
    if args.command == "doctor":
        return _doctor()
    return _daemon_status()


def _run_command(argv, stdin, stdout):
    """These steps stay together because main requires one stable exit code boundary."""
    args = _parser().parse_args(argv)
    data = _dispatch(args, stdin)
    if args.command == "daemon" and args.daemon_command == "status":
        _emit(data, args.json, stdout)
        return SUCCESS if data.get("status") == "alive" else DAEMON_DOWN
    _emit(data, getattr(args, "json", False), stdout)
    return SUCCESS


def _main_inputs(args, kwargs):
    """Both calling forms remain because older callers inject streams positionally."""
    names = ("argv", "stdin", "stdout", "stderr")
    defaults = (sys.argv[1:], sys.stdin, sys.stdout, sys.stderr)
    provided = dict(zip(names, args, strict=False))
    provided.update(kwargs)
    return tuple(
        default if provided.get(name) is None else provided[name]
        for name, default in zip(names, defaults, strict=True)
    )


def main(*args, **kwargs) -> int:
    argv, stdin, stdout, stderr = _main_inputs(args, kwargs)
    started = time.perf_counter()
    try:
        return _run_command(argv, stdin, stdout)
    except BadArgsError as exc:
        stderr.write(f"bad-args: {exc}\n")
        return BAD_ARGS
    except KeyError as exc:
        stderr.write(f"ref-not-found: {exc.args[0]}\n")
        return REF_NOT_FOUND
    except fetch.BlockedFetchError as exc:
        stderr.write(f"blocked-fetch: {exc}\n")
        return BAD_ARGS
    except BrokenPipeError:
        return SUCCESS
    except OSError as exc:
        stderr.write(f"network-failure: {exc}\n")
        return NETWORK_FAILURE
    except Exception as exc:
        stderr.write(f"unexpected-error: {exc}\n")
        stderr.write(f"elapsed_ms={int((time.perf_counter() - started) * 1000)}\n")
        return UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
