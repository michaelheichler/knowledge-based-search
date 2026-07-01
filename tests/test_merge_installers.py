import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MCP_COMMAND = "/tmp/kbs-python"
SERVER = str(ROOT / "server" / "mcp_server.py")


def run_script(*args, env=None):
    subprocess.run([PYTHON, *map(str, args)], check=True, cwd=ROOT, env=env)


def write_installer_stub(path, marker):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import sys",
                "from pathlib import Path",
                f"Path(sys.argv[1]).write_text({marker!r}, encoding='utf-8')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


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
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": f"python3 {ROOT}/hooks/session_start.py",
                                        }
                                    ]
                                },
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 /tmp/other/hooks/session_start.py",
                                        }
                                    ]
                                },
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
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "python3 /tmp/other/hooks/session_start.py",
                                        }
                                    ]
                                },
                                {
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": f"python3 {ROOT}/hooks/session_start.py",
                                        }
                                    ]
                                },
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
            env = os.environ.copy()
            env["KBS_PYTHON"] = MCP_COMMAND
            run_script(*args, env=env)
            run_script(*args, env=env)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            settings_data = json.loads(settings.read_text(encoding="utf-8"))
            assert data["theme"] == "dark"
            assert (
                data["mcpServers"]["knowledge-based-search"]["command"] == MCP_COMMAND
            )
            assert data["mcpServers"]["knowledge-based-search"]["args"] == [SERVER]
            assert "knowledge-based-search/hooks" not in json.dumps(data)
            assert json.dumps(data).count("/tmp/other/hooks/session_start.py") == 1
            assert (
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/session_start.py"
                )
                == 1
            )
            assert (
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/prompt_inject.py"
                )
                == 1
            )
            assert (
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/method_inject.py"
                )
                == 1
            )
            assert (
                json.dumps(settings_data).count("/tmp/other/hooks/session_start.py")
                == 1
            )
            assert len(list(Path(td).glob("settings.json.kbs.*.bak"))) == 2

    def test_claude_merge_uses_default_settings_path(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            home = Path(td) / "home"
            cfg = Path(td) / "claude.json"
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["KBS_PYTHON"] = MCP_COMMAND
            args = [
                ROOT / "claude-code" / "merge-claude-settings.py",
                cfg,
                ROOT / "claude-code" / "claude-settings.snippet.json",
                ROOT,
            ]
            run_script(*args, env=env)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            settings = json.loads(
                (home / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            self.assertIn("knowledge-based-search", data["mcpServers"])
            self.assertNotIn("knowledge-based-search/hooks", json.dumps(data))
            self.assertEqual(
                json.dumps(settings).count(
                    "knowledge-based-search/hooks/session_start.py"
                ),
                1,
            )

    def test_codex_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            cfg.write_text('[mcp_servers.other]\ncommand = "x"\n', encoding="utf-8")
            args = [
                ROOT / "codex" / "merge-codex-config.py",
                cfg,
                ROOT / "codex" / "codex-config.snippet.toml",
                ROOT,
            ]
            env = os.environ.copy()
            env["KBS_PYTHON"] = MCP_COMMAND
            run_script(*args, env=env)
            run_script(*args, env=env)
            text = cfg.read_text(encoding="utf-8")
            self.assertEqual(text.count("[mcp_servers.knowledge-based-search]"), 1)
            self.assertIn(f'command = "{MCP_COMMAND}"', text)
            self.assertEqual(text.count("[[hooks.SessionStart]]"), 1)
            self.assertEqual(text.count("[[hooks.UserPromptSubmit]]"), 1)
            self.assertEqual(text.count("session_start.py"), 1)
            self.assertEqual(text.count("prompt_inject.py"), 1)

    def test_pi_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            sibling = "/tmp/knowledge-based-search-extras/index.ts"
            cfg.write_text(
                json.dumps({"extensions": ["/tmp/other.ts", sibling], "keep": True}),
                encoding="utf-8",
            )
            ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
            args = [ROOT / "pi" / "merge-pi-settings.py", cfg, ext]
            env = os.environ.copy()
            env["KBS_PYTHON"] = MCP_COMMAND
            run_script(*args, env=env)
            run_script(*args, env=env)
            data = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertIs(data["keep"], True)
            self.assertEqual(data["extensions"].count(str(ext)), 1)
            self.assertIn("/tmp/other.ts", data["extensions"])
            self.assertIn(sibling, data["extensions"])
            self.assertEqual(
                data["mcpServers"]["knowledge-based-search"]["command"], MCP_COMMAND
            )
            self.assertEqual(
                data["mcpServers"]["knowledge-based-search"]["args"], [SERVER]
            )

    def test_pi_merge_uses_kbs_dir_for_copied_extension(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            copied = Path(td) / "copied" / "index.ts"
            copied.parent.mkdir()
            copied.write_text("", encoding="utf-8")
            env = os.environ.copy()
            env["KBS_DIR"] = str(ROOT)
            env["KBS_PYTHON"] = MCP_COMMAND

            run_script(ROOT / "pi" / "merge-pi-settings.py", cfg, copied, env=env)

            data = json.loads(cfg.read_text(encoding="utf-8"))
            self.assertEqual(
                [str(Path(item).resolve()) for item in data["extensions"]],
                [str(copied.resolve())],
            )
            self.assertEqual(
                data["mcpServers"]["knowledge-based-search"]["args"], [SERVER]
            )

    def test_pi_extension_uses_kbs_dir_override(self):
        ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
        text = ext.read_text(encoding="utf-8")

        self.assertIn("process.env.KBS_DIR", text)

    def test_pi_extension_guards_missing_startup_prompt(self):
        ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
        text = ext.read_text(encoding="utf-8")

        self.assertIn('event?.systemPrompt ?? ""', text)


def test_install_explicit_codex_target_skips_claude_auto_detection():
    assert (ROOT / "install.sh").exists()
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        repo = Path(td) / "repo"
        home = Path(td) / "home"
        repo.mkdir()
        home.mkdir()
        (home / ".claude").mkdir()
        (home / ".codex").mkdir()
        (repo / "server").mkdir()
        (repo / "skills" / "knowledge-based-search").mkdir(parents=True)
        (repo / "codex").mkdir()
        (repo / "codex" / "codex-config.snippet.toml").write_text("", encoding="utf-8")
        (repo / "claude-code").mkdir()
        (repo / "claude-code" / "claude-settings.snippet.json").write_text(
            "{}", encoding="utf-8"
        )
        (repo / "pi" / "extensions" / "knowledge-based-search").mkdir(parents=True)
        (repo / "pi" / "extensions" / "knowledge-based-search" / "index.ts").write_text(
            "", encoding="utf-8"
        )
        write_installer_stub(repo / "codex" / "merge-codex-config.py", "codex")
        write_installer_stub(
            repo / "claude-code" / "merge-claude-settings.py", "claude"
        )
        write_installer_stub(repo / "pi" / "merge-pi-settings.py", "pi")
        (repo / "install.sh").write_text(
            (ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8"
        )
        env = os.environ.copy()
        env["HOME"] = str(home)

        subprocess.run(
            ["bash", str(repo / "install.sh"), "--codex", "-y"],
            check=True,
            cwd=repo,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        assert not (home / ".claude.json").exists()
        assert (home / ".codex" / "config.toml").read_text(encoding="utf-8") == "codex"


if __name__ == "__main__":
    unittest.main()
