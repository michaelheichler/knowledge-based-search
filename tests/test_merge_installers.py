import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MCP_COMMAND = "/Users/michael/dev/skills/skill-model-loader/.venv/bin/python"
SERVER = str(ROOT / "server" / "mcp_server.py")


def run_script(*args, env=None):
    subprocess.run([PYTHON, *map(str, args)], check=True, cwd=ROOT, env=env)


class MergeInstallerTests(unittest.TestCase):
    def test_claude_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "claude.json"
            settings = Path(td) / "settings.json"
            cfg.write_text(
                json.dumps(
                    {
                        "theme": "dark",
                        "mcpServers": {"other": {"command": "x"}},
                        "hooks": {
                            "SessionStart": [
                                {"hooks": [{"type": "command", "command": f"python3 {ROOT}/hooks/session_start.py"}]},
                                {"hooks": [{"type": "command", "command": "python3 /tmp/other/hooks/session_start.py"}]},
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            settings.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {"hooks": [{"type": "command", "command": "python3 /tmp/other/hooks/session_start.py"}]},
                                {"hooks": [{"type": "command", "command": f"python3 {ROOT}/hooks/session_start.py"}]},
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            args = [
                ROOT / "claude-code" / "merge-claude-settings.py",
                cfg,
                ROOT / "claude-code" / "claude-settings.snippet.json",
                ROOT,
                settings,
            ]
            run_script(*args)
            run_script(*args)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            settings_data = json.loads(settings.read_text(encoding="utf-8"))
            assert data["theme"] == "dark"
            assert data["mcpServers"]["knowledge-based-search"]["command"] == MCP_COMMAND
            assert data["mcpServers"]["knowledge-based-search"]["args"] == [SERVER]
            assert "knowledge-based-search/hooks" not in json.dumps(data)
            assert json.dumps(data).count("/tmp/other/hooks/session_start.py") == 1
            assert json.dumps(settings_data).count("knowledge-based-search/hooks/session_start.py") == 1
            assert json.dumps(settings_data).count("knowledge-based-search/hooks/prompt_inject.py") == 1
            assert json.dumps(settings_data).count("knowledge-based-search/hooks/method_inject.py") == 1
            assert json.dumps(settings_data).count("/tmp/other/hooks/session_start.py") == 1
            assert len(list(Path(td).glob("settings.json.kbs.*.bak"))) == 2

    def test_claude_merge_uses_default_settings_path(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            home = Path(td) / "home"
            cfg = Path(td) / "claude.json"
            env = os.environ.copy()
            env["HOME"] = str(home)
            args = [ROOT / "claude-code" / "merge-claude-settings.py", cfg, ROOT / "claude-code" / "claude-settings.snippet.json", ROOT]
            run_script(*args, env=env)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            settings = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
            self.assertIn("knowledge-based-search", data["mcpServers"])
            self.assertNotIn("knowledge-based-search/hooks", json.dumps(data))
            self.assertEqual(json.dumps(settings).count("knowledge-based-search/hooks/session_start.py"), 1)

    def test_codex_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            cfg.write_text('[mcp_servers.other]\ncommand = "x"\n', encoding="utf-8")
            args = [ROOT / "codex" / "merge-codex-config.py", cfg, ROOT / "codex" / "codex-config.snippet.toml", ROOT]
            run_script(*args)
            run_script(*args)
            text = cfg.read_text(encoding="utf-8")
            self.assertEqual(text.count("[mcp_servers.knowledge-based-search]"), 1)
            self.assertEqual(text.count("[[hooks.SessionStart]]"), 1)
            self.assertEqual(text.count("[[hooks.UserPromptSubmit]]"), 1)
            self.assertEqual(text.count("session_start.py"), 1)
            self.assertEqual(text.count("prompt_inject.py"), 1)

    def test_pi_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text(json.dumps({"extensions": ["/tmp/other.ts"], "keep": True}), encoding="utf-8")
            ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
            args = [ROOT / "pi" / "merge-pi-settings.py", cfg, ext]
            run_script(*args)
            run_script(*args)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertIs(data["keep"], True)
            self.assertEqual(data["extensions"].count(str(ext)), 1)
            self.assertIn("/tmp/other.ts", data["extensions"])
            self.assertEqual(data["mcpServers"]["knowledge-based-search"]["command"], MCP_COMMAND)
            self.assertEqual(data["mcpServers"]["knowledge-based-search"]["args"], [SERVER])


if __name__ == "__main__":
    unittest.main()
