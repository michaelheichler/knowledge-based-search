import json

import pytest

from skill_gate import should_block


@pytest.fixture
def skill_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / ".codex/skills/knowledge-based-search/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("Search with primary sources.\nVerify current facts.\n", encoding="utf-8")
    return path


def transcript_event(tmp_path, name, arguments, output):
    transcript = tmp_path / "session.jsonl"
    call = {"type": "function_call", "name": name, "arguments": json.dumps(arguments), "call_id": "read"}
    if name == "exec":
        call = {"type": "custom_tool_call", "name": name, "input": arguments, "call_id": "read"}
    result = {"type": "function_call_output", "call_id": "read", "output": output}
    transcript.write_text("\n".join(json.dumps({"type": "response_item", "payload": item}) for item in (call, result)))
    return {"tool_name": "Bash", "tool_input": {"command": "kbs quick docs"}, "transcript_path": str(transcript)}


@pytest.mark.parametrize("prefix,suffix", [("text(", ")"), ("const result = ", "; text(result.output)"), ("let result = ", "; text(result)")])
def test_wrapped_codex_skill_read_loads_gate(tmp_path, skill_path, prefix, suffix):
    source = prefix + 'await tools.exec_command({cmd:' + json.dumps(f"cat {skill_path}") + '})' + suffix + ';'
    output = [{"type": "input_text", "text": json.dumps({"exit_code": 0, "output": skill_path.read_text()})}]
    event = transcript_event(tmp_path, "exec", source, output)
    assert not should_block(event)


def test_direct_codex_skill_read_loads_gate(tmp_path, skill_path):
    output = json.dumps({"exit_code": 0, "output": skill_path.read_text()})
    event = transcript_event(tmp_path, "exec_command", {"cmd": f"cat {skill_path}"}, output)
    assert not should_block(event)


@pytest.mark.parametrize("command,exit_code", [("cat {skill}", 1), ("echo {skill}", 0), ("head -n 1 {skill}", 0)])
def test_failed_or_partial_reads_keep_gate_closed(tmp_path, skill_path, command, exit_code):
    output = json.dumps({"exit_code": exit_code, "output": skill_path.read_text()})
    event = transcript_event(tmp_path, "exec_command", {"cmd": command.format(skill=skill_path)}, output)
    assert should_block(event)


def test_same_named_decoy_does_not_load_gate(tmp_path, skill_path):
    decoy = tmp_path / "knowledge-based-search/SKILL.md"
    decoy.parent.mkdir()
    decoy.write_text(skill_path.read_text())
    output = json.dumps({"exit_code": 0, "output": decoy.read_text()})
    event = transcript_event(tmp_path, "exec_command", {"cmd": f"cat {decoy}"}, output)
    assert should_block(event)


@pytest.mark.parametrize("output", ["pending", {"exit_code": 0, "output": "Search with primary sources."}])
def test_missing_or_truncated_result_does_not_load_gate(tmp_path, skill_path, output):
    event = transcript_event(tmp_path, "exec_command", {"cmd": f"cat {skill_path}"}, output)
    assert should_block(event)


def test_malformed_transcript_entries_do_not_crash_gate(tmp_path):
    event = transcript_event(tmp_path, "exec_command", {"cmd": "echo hello"}, "pending")
    with (tmp_path / "session.jsonl").open("a") as handle:
        handle.write('\nnull\n[]\n{"message":null}\n')
    assert should_block(event)


def test_missing_exit_status_does_not_load_gate(tmp_path, skill_path):
    output = {"output": skill_path.read_text()}
    event = transcript_event(tmp_path, "exec_command", {"cmd": f"cat {skill_path}"}, output)
    assert should_block(event)


@pytest.mark.parametrize("payload", [
    {"type": [], "name": "exec_command"},
    {"type": "function_call", "name": None},
    {"type": "function_call", "name": []},
])
def test_malformed_codex_payload_keeps_gate_closed(tmp_path, payload):
    event = transcript_event(tmp_path, "exec_command", {"cmd": "echo hello"}, "pending")
    with (tmp_path / "session.jsonl").open("a") as handle:
        handle.write("\n" + json.dumps({"type": "response_item", "payload": payload}))
    assert should_block(event)
