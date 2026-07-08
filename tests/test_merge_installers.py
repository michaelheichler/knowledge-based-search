# ruff: noqa
"""Tests for merge installers and install.sh."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise AssertionError(f"failed to parse {path}: {exc}") from exc


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
    def _initial_claude_cfg(self):
        return {
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

    def _initial_claude_settings(self):
        return {
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

    def test_claude_merge_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "claude.json"
            settings = Path(td) / "settings.json"
            cfg.write_text(json.dumps(self._initial_claude_cfg()), encoding="utf-8")
            settings.write_text(
                json.dumps(self._initial_claude_settings()), encoding="utf-8"
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
            data = read_json(cfg)
            settings_data = read_json(settings)
            self.assertEqual(data["theme"], "dark")
            self.assertEqual(data["mcpServers"], {"other": {"command": "x"}})
            self.assertNotIn("knowledge-based-search", data["mcpServers"])
            self.assertNotIn("knowledge-based-search/hooks", json.dumps(data))
            self.assertEqual(
                json.dumps(data).count("/tmp/other/hooks/session_start.py"), 1
            )
            self.assertEqual(
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/session_start.py"
                ),
                1,
            )
            self.assertEqual(
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/prompt_inject.py"
                ),
                1,
            )
            self.assertEqual(
                json.dumps(settings_data).count(
                    "knowledge-based-search/hooks/method_inject.py"
                ),
                1,
            )
            self.assertEqual(json.dumps(settings_data).count('"matcher": "Bash"'), 2)
            self.assertEqual(
                json.dumps(settings_data).count("/tmp/other/hooks/session_start.py"),
                1,
            )
            self.assertEqual(len(list(Path(td).glob("settings.json.kbs.*.bak"))), 2)

    def test_claude_merge_uses_default_settings_path(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            home = Path(td) / "home"
            cfg = Path(td) / "claude.json"
            env = os.environ.copy()
            env["HOME"] = str(home)
            args = [
                ROOT / "claude-code" / "merge-claude-settings.py",
                cfg,
                ROOT / "claude-code" / "claude-settings.snippet.json",
                ROOT,
            ]
            run_script(*args, env=env)
            data = read_json(cfg)
            settings = read_json(home / ".claude" / "settings.json")
            self.assertNotIn("mcpServers", data)
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
            run_script(*args)
            run_script(*args)
            text = cfg.read_text(encoding="utf-8")
            self.assertNotIn("[mcp_servers.knowledge-based-search]", text)
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
            run_script(*args)
            run_script(*args)
            data = read_json(cfg)
            self.assertIs(data["keep"], True)
            self.assertEqual(data["extensions"].count(str(ext)), 1)
            self.assertIn("/tmp/other.ts", data["extensions"])
            self.assertIn(sibling, data["extensions"])
            self.assertNotIn("mcpServers", data)

    def test_pi_merge_strips_existing_mcpservers(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text(
                json.dumps(
                    {
                        "extensions": [],
                        "mcpServers": {"knowledge-based-search": {"command": "old"}},
                    }
                ),
                encoding="utf-8",
            )
            ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
            run_script(ROOT / "pi" / "merge-pi-settings.py", cfg, ext)
            data = read_json(cfg)
            self.assertNotIn("mcpServers", data)

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


def test_install_opencode_creates_instruction_file():
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home = Path(td) / "home"
        repo = Path(td) / "repo"
        home.mkdir()
        repo.mkdir()
        agents_dir = home / ".config" / "opencode"
        agents_dir.mkdir(parents=True)
        (agents_dir / "AGENTS.md").write_text("old instructions\n", encoding="utf-8")
        (repo / "server").mkdir()
        (repo / "bin").mkdir()
        (repo / "bin" / "kbs").write_text(
            "#!/usr/bin/env python3\nprint('stub')\n", encoding="utf-8"
        )
        (repo / "install.sh").write_text(
            (ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8"
        )
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["KBS_BIN_DIR"] = str(Path(td) / "bin")

        subprocess.run(
            ["bash", str(repo / "install.sh"), "--opencode", "-y"],
            check=True,
            cwd=repo,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        agents_md = home / ".config" / "opencode" / "AGENTS.md"
        backups = list(agents_md.parent.glob("AGENTS.md.kbs.*.bak"))
        assert agents_md.exists()
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "old instructions\n"
        content = agents_md.read_text(encoding="utf-8")
        assert "kbs quick" in content
        assert "kbs search" in content
        assert "kbs doctor" in content


def test_installer_stdout_includes_all_six_examples():
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home = Path(td) / "home"
        repo = Path(td) / "repo"
        home.mkdir()
        repo.mkdir()
        (repo / "server").mkdir()
        (repo / "bin").mkdir()
        (repo / "bin" / "kbs").write_text(
            "#!/usr/bin/env python3\nprint('stub')\n", encoding="utf-8"
        )
        (repo / "install.sh").write_text(
            (ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8"
        )
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["KBS_BIN_DIR"] = str(Path(td) / "bin")

        result = subprocess.run(
            ["bash", str(repo / "install.sh"), "--opencode", "-y"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        for cmd in [
            "kbs quick",
            "kbs search",
            "kbs get",
            "kbs deep",
            "kbs context",
            "kbs doctor",
        ]:
            assert cmd in result.stdout, f"missing '{cmd}' in installer output"


def test_smoke_checklist_artifact_exists():
    checklist = ROOT / "outputs" / "e4-s1-smoke-checklist.md"
    assert checklist.exists()
    text = checklist.read_text(encoding="utf-8")
    assert "Pi" in text
    assert "Codex" in text
    assert "OpenCode" in text
    assert "which kbs" in text
    assert "kbs doctor" in text


def test_claude_smoke_checklist_artifact_exists():
    checklist = ROOT / "outputs" / "e4-s2-smoke-checklist.md"
    assert checklist.exists()
    text = checklist.read_text(encoding="utf-8")
    assert "Claude Code" in text
    assert "mcpServers.knowledge-based-search" in text
    assert "which kbs" in text
    assert "kbs doctor" in text


if __name__ == "__main__":
    unittest.main()
