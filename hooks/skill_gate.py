#!/usr/bin/env python3
# ruff: noqa
import json
import os
import re
import shlex
import sys

SKILL_NAME = "knowledge-based-search"
_CONTROL_TOKENS = set(";&|(){}\n`")
_KBS_FALLBACK_RE = re.compile(r"(?:^|[\s('\"])(?:\S*/)?kbs(?:\s|$)")
_TRANSCRIPT_CACHE: dict[str, tuple[int, bool]] = {}
SKILL_DENY_REASON = (
    "Load the knowledge-based-search skill with the Skill tool first, then reformulate the "
    "query with its method and run the search again. This gate fires until the skill is loaded "
    "this session."
)
TRANSCRIPT_DENY_REASON = (
    "KBS use is denied because the session transcript is missing or unreadable. "
    "Restore transcript access, load the knowledge-based-search skill, and retry."
)
WEB_SEARCH_DENY_REASON = "Built-in web search is disabled. Use kbs through Bash or a configured Linkup tool instead."
_WEB_SEARCH_TOOLS = {"WebSearch", "web_search", "websearch"}


def _line_loads_skill(line):
    try:
        entry = json.loads(line)
    except ValueError:
        return False
    content = entry.get("message", {}).get("content")
    if not isinstance(content, list):
        return False
    return any(_item_loads_skill(item) for item in content)


def _is_our_skill_id(skill_id):
    return isinstance(skill_id, str) and skill_id in {
        SKILL_NAME,
        f"{SKILL_NAME}:{SKILL_NAME}",
    }


def _item_loads_skill(item):
    return (
        isinstance(item, dict)
        and item.get("type") == "tool_use"
        and item.get("name") == "Skill"
        and isinstance(item.get("input"), dict)
        and _is_our_skill_id(item["input"].get("skill"))
    )


def _tool_name(event):
    return event.get("tool_name") or event.get("tool", {}).get("name", "")


def _is_assignment(token):
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token))


def _is_kbs_path(token):
    if token in {"kbs", "./bin/kbs"}:
        return True
    return token.endswith("/kbs")


def _strip_assignments(tokens):
    while tokens and _is_assignment(tokens[0]):
        tokens = tokens[1:]
    return tokens


def _env_split_payload(option, tokens):
    if not (option.startswith("-S") or option.startswith("--split-string")):
        return None
    packed = option.split("=", 1)[1] if "=" in option else option[2:]
    return packed or (tokens.pop(0) if tokens else "")


def _strip_env_prefix(tokens):
    tokens = tokens[1:]
    while tokens and tokens[0].startswith("-"):
        option = tokens.pop(0)
        packed = _env_split_payload(option, tokens)
        if packed is not None:
            return _strip_assignments(_split_tokens(packed) + tokens)
        if option in {"-u", "--unset"} and tokens:
            tokens.pop(0)
    return _strip_assignments(tokens)


def _split_tokens(text):
    """Tokenize with a whitespace fallback because env -S strings may not shlex."""
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def _strip_command_prefix(tokens):
    tokens = tokens[1:]
    if tokens and tokens[0] in {"-v", "-V"}:
        return []
    while tokens and tokens[0] in {"-p", "--"}:
        tokens = tokens[1:]
    return tokens


def _strip_wrapper_options(tokens, value_options):
    args = list(tokens)
    while args and args[0].startswith("-"):
        option = args.pop(0)
        if option == "--":
            break
        name = option.split("=", 1)[0]
        if name in value_options and "=" not in option and args:
            args.pop(0)
    return args


def _timeout_invokes_kbs(tokens):
    value_options = {"-k", "--kill-after", "-s", "--signal"}
    args = _strip_wrapper_options(tokens[1:], value_options)
    return len(args) > 1 and _tokens_invoke_kbs(args[1:])


def _shell_command_argument(tokens):
    for index, option in enumerate(tokens[1:], 1):
        short_command = option.startswith("-") and not option.startswith("--")
        if (short_command and "c" in option[1:]) or option == "--command":
            return tokens[index + 1] if index + 1 < len(tokens) else ""
    return ""


def _wrapped_tokens_invoke_kbs(tokens, executable):
    if executable in {"bash", "sh", "zsh"}:
        command = _shell_command_argument(tokens)
        return bool(command) and _command_invokes_kbs(command)
    if executable == "timeout":
        return _timeout_invokes_kbs(tokens)
    value_options = {
        "sudo": {"-u", "--user", "-g", "--group", "-h", "--host", "-C"},
        "nice": {"-n", "--adjustment"},
        "time": {"-o", "--output", "-f", "--format"},
        "xargs": {"-a", "--arg-file", "-E", "-I", "-L", "-n", "-P", "-s"},
    }
    if executable in {"sudo", "nice", "time", "nohup", "xargs"}:
        args = _strip_wrapper_options(tokens[1:], value_options.get(executable, set()))
        return _tokens_invoke_kbs(args)
    return False


def _strip_builtin_prefixes(tokens):
    """Peel shell builtin layers because eval needs a full re-parse of its args."""
    while tokens:
        name = os.path.basename(tokens[0])
        if name == "env":
            tokens = _strip_env_prefix(tokens)
            continue
        if name == "command":
            tokens = _strip_command_prefix(tokens)
            continue
        if name == "exec":
            tokens = _strip_wrapper_options(tokens[1:], {"-a"})
            continue
        if name == "eval":
            return [], " ".join(tokens[1:])
        return tokens, None
    return tokens, None


def _python_script(tokens):
    args = list(tokens[1:])
    while args and args[0].startswith("-"):
        option = args.pop(0)
        if option == "--":
            break
        if option in {"-c", "-m"}:
            return ""
        if option in {"-W", "-X"} and args:
            args.pop(0)
    return args[0] if args else ""


def _tokens_invoke_kbs(tokens):
    tokens, eval_payload = _strip_builtin_prefixes(_strip_assignments(list(tokens)))
    if eval_payload is not None:
        return _command_invokes_kbs(eval_payload)
    if not tokens:
        return False
    if _is_kbs_path(tokens[0]):
        return True
    executable = os.path.basename(tokens[0])
    if _wrapped_tokens_invoke_kbs(tokens, executable):
        return True
    if executable in {"python", "python3"}:
        return _is_kbs_path(_python_script(tokens))
    return False


def _shell_segments(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}\n`")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = "#"
    segments = [[]]
    for token in lexer:
        if token and set(token) <= _CONTROL_TOKENS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def _command_invokes_kbs(command):
    try:
        return any(_tokens_invoke_kbs(segment) for segment in _shell_segments(command))
    except ValueError:
        return bool(_KBS_FALLBACK_RE.search(command))


def _is_kbs_invocation(event):
    if _tool_name(event) != "Bash":
        return False
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    return isinstance(command, str) and _command_invokes_kbs(command)


def _transcript_is_readable(path):
    return isinstance(path, str) and os.path.isfile(path) and os.access(path, os.R_OK)


def deny_reason(event) -> str:
    """Return the denial reason that explains the blocked action."""
    if _tool_name(event) in _WEB_SEARCH_TOOLS:
        return WEB_SEARCH_DENY_REASON
    if "transcript_path" in event and not _transcript_is_readable(
        event.get("transcript_path")
    ):
        return TRANSCRIPT_DENY_REASON
    return SKILL_DENY_REASON


def _transcript_loaded_skill(path, stamp):
    cached = _TRANSCRIPT_CACHE.get(path)
    if cached and cached[0] == stamp:
        return cached[1]
    with open(path, encoding="utf-8") as handle:
        loaded = any(SKILL_NAME in line and _line_loads_skill(line) for line in handle)
    _TRANSCRIPT_CACHE[path] = (stamp, loaded)
    return loaded


def should_block(event) -> bool:
    """Return whether the hook must deny this tool invocation."""
    if _tool_name(event) in _WEB_SEARCH_TOOLS:
        return True
    if not _is_kbs_invocation(event):
        return False
    if "transcript_path" not in event:
        return False
    path = event.get("transcript_path")
    if not _transcript_is_readable(path):
        return True
    try:
        stamp = os.stat(path).st_mtime_ns
        return not _transcript_loaded_skill(path, stamp)
    except OSError:
        return True


def deny_output(reason=SKILL_DENY_REASON) -> dict:
    """Build a Claude Code PreToolUse denial response."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> None:
    """Read one hook event and print a denial only when required."""
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    if should_block(event):
        print(json.dumps(deny_output(deny_reason(event))))


def _demo_skill_line(skill, **values):
    tool_input = {"skill": skill, **values}
    return json.dumps(
        {
            "message": {
                "content": [{"type": "tool_use", "name": "Skill", "input": tool_input}]
            }
        }
    )


_DEMO_BYPASSES = (
    "./bin/kbs search x",
    "/opt/tool/bin/kbs search x",
    "python3 /opt/tool/bin/kbs search x",
    "command kbs search x",
    "env KBS_SESSION=x kbs search x",
    "true && kbs search x",
    "echo x |\nkbs search x",
    'bash -c "kbs search x"',
    "timeout 5 kbs search x",
    "timeout --signal KILL 5 kbs search x",
    "sudo -u root kbs search x",
    "nice -n 10 kbs search x",
    "time -p kbs search x",
    "nohup kbs search x",
    "xargs kbs",
    "../kbs search x",
    'kbs search "unbalanced',
)


def demo() -> None:
    """Check exact skill detection and invocation bypass coverage."""
    assert _line_loads_skill(_demo_skill_line(SKILL_NAME))
    decoy = _demo_skill_line("interview-me", args=SKILL_NAME)
    assert not _line_loads_skill(decoy)
    assert all(_command_invokes_kbs(command) for command in _DEMO_BYPASSES)
    assert not _command_invokes_kbs("printf '%s' kbs")
    assert deny_output()["hookSpecificOutput"]["permissionDecision"] == "deny"
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
