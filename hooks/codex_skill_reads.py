import json
import re
import shlex
from pathlib import Path, PurePosixPath


SKILL_NAME = "knowledge-based-search"
_EXEC_COMMAND = re.compile(r'^\s*(?:text\(\s*|(?:const|let|var)\s+\w+\s*=\s*)?await tools\.exec_command\(\s*\{\s*["\']?cmd["\']?\s*:\s*')


def _json(value):
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return None


def _skill_paths():
    home = Path.home()
    roots = [home / host / "skills" for host in (".codex", ".agents", ".claude")]
    roots.append(Path(__file__).resolve().parents[1] / "skills")
    return {(root / SKILL_NAME / "SKILL.md").resolve() for root in roots}


def _skill_content(command):
    if not isinstance(command, str):
        return None
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if len(tokens) != 2 or PurePosixPath(tokens[0]).name != "cat":
        return None
    path = Path(tokens[1]).expanduser().resolve()
    if path not in _skill_paths():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeError):
        return None


def _command(payload):
    name = payload.get("name")
    if not isinstance(name, str):
        return None
    name = name.removeprefix("functions.")
    if name == "exec_command":
        args = _json(payload.get("arguments"))
        return args.get("cmd") if isinstance(args, dict) else None
    source = payload.get("input", "")
    if name != "exec" or not isinstance(source, str) or source.count("tools.exec_command(") != 1:
        return None
    match = _EXEC_COMMAND.match(source)
    if not match:
        return None
    try:
        command, _ = json.JSONDecoder().raw_decode(source[match.end():])
        return command
    except ValueError:
        return None


def _delivered_skill(output, content):
    parsed = _json(output)
    if isinstance(parsed, dict):
        if parsed.get("type") in ("input_text", "text"):
            return _delivered_skill(parsed.get("text"), content)
        return parsed.get("exit_code") == 0 and content in str(parsed.get("output", ""))
    if isinstance(parsed, list):
        return any(_delivered_skill(item, content) for item in parsed)
    return isinstance(output, str) and content in output and bool(re.search(r"^Process exited with code 0$", output, re.MULTILINE))


class CodexSkillReads:
    def __init__(self):
        self.pending = {}

    def loads_skill(self, entry):
        if not isinstance(entry, dict) or entry.get("type") != "response_item":
            return False
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            return False
        call_id = payload.get("call_id")
        kind = payload.get("type")
        if not isinstance(kind, str):
            return False
        if kind in {"function_call", "custom_tool_call"}:
            content = _skill_content(_command(payload))
            if content and isinstance(call_id, str):
                self.pending[call_id] = content
        if kind in {"function_call_output", "custom_tool_call_output"} and isinstance(call_id, str) and call_id in self.pending:
            return _delivered_skill(payload.get("output"), self.pending.pop(call_id))
        return False
