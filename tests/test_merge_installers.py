# ruff: noqa
"""Tests for merge installers and install.sh."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
LEGACY_CODEX_CONFIG = (
    "[[hooks.SessionStart]]\n"
    'matcher = "startup"\n\n'
    "[[hooks.SessionStart.hooks]]\n"
    'command = "python3 /repo/knowledge-based-search/hooks/session_start.py"\n\n'
    "[[hooks.UserPromptSubmit]]\n\n"
    "[[hooks.UserPromptSubmit.hooks]]\n"
    'command = "python3 /repo/knowledge-based-search/hooks/prompt_inject.py"\n\n'
    "[[hooks.SessionStart]]\n"
    'matcher = "startup"\n\n'
    "[[hooks.SessionStart.hooks]]\n"
    'command = "python3 /other/hooks/start.py"\n'
)
LEGACY_ZED_INSTRUCTIONS = """Keyless web search via kbs CLI:
  kbs quick <query>      one fast fact, ranked links and snippets
  kbs plan <query>       method plan with reference notes before OSINT/fact checks
  kbs search <query>     full pipeline, cited summary
  kbs get <url>          open one source in full
  kbs deep <query>       bounded multi-round cited report
  kbs context <query>    context-aware search with session memory
  kbs doctor             check daemon health and PATH
Load the knowledge-based-search skill before searching.
Reach for kbs search first, escalate to kbs deep when needed.
Verify any fact that can change since training before stating it.
"""


def read_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise AssertionError(f"failed to parse {path}: {exc}") from exc


def run_script(*args, env=None) -> None:
    subprocess.run([PYTHON, *map(str, args)], check=True, cwd=ROOT, env=env)


def write_installer_stub(path: Path, marker: str) -> None:
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
    def test_codex_merge_is_idempotent(self) -> None:
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
            self.assertEqual(text.count("[[hooks.PreToolUse]]"), 1)
            self.assertEqual(text.count("skill_gate.py"), 1)
            self.assertIn('matcher = "Bash|WebSearch|web_search|websearch"', text)
            self.assertNotIn("session_start.py", text)
            self.assertNotIn("prompt_inject.py", text)

    def test_codex_merge_quotes_hook_path_with_space(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            repo = Path(td) / "repo with space"
            run_script(
                ROOT / "codex" / "merge-codex-config.py",
                cfg,
                ROOT / "codex" / "codex-config.snippet.toml",
                repo,
            )
            hook = shlex.quote(str(repo.resolve() / "hooks" / "skill_gate.py"))
            assert f'command = "python3 {hook}"' in cfg.read_text(encoding="utf-8")

    def test_codex_merge_removes_legacy_kbs_hooks(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            cfg.write_text(LEGACY_CODEX_CONFIG, encoding="utf-8")
            run_script(
                ROOT / "codex" / "merge-codex-config.py",
                cfg,
                ROOT / "codex" / "codex-config.snippet.toml",
                ROOT,
            )
            text = cfg.read_text(encoding="utf-8")
            self.assertNotIn("session_start.py", text)
            self.assertNotIn("prompt_inject.py", text)
            self.assertIn("/other/hooks/start.py", text)
            self.assertIn("skill_gate.py", text)

    def test_pi_merge_is_idempotent(self) -> None:
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

    def test_pi_merge_rejects_malformed_json_without_changes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            original = b'{"extensions": [}\n'
            cfg.write_bytes(original)
            extension = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
            result = subprocess.run(
                [PYTHON, str(ROOT / "pi" / "merge-pi-settings.py"), str(cfg), str(extension)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0
            assert cfg.read_bytes() == original
            assert "malformed JSON" in result.stderr

    def test_pi_merge_strips_existing_mcpservers(self) -> None:
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

    def test_pi_extension_gates_actual_tool_calls(self) -> None:
        ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
        text = ext.read_text(encoding="utf-8")

        self.assertIn('pi.on("tool_call"', text)
        self.assertIn("WEB_SEARCH_TOOLS", text)
        self.assertIn("KBS_COMMAND", text)

    def test_codex_merge_strips_stale_unfenced_kbs_mcp_table(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            cfg.write_text(
                "[mcp_servers.knowledge-based-search]\n"
                'command = "python3"\n'
                'args = ["/old/server/mcp_server.py"]\n'
                "\n"
                "[mcp_servers.other]\n"
                'command = "x"\n',
                encoding="utf-8",
            )
            args = [
                ROOT / "codex" / "merge-codex-config.py",
                cfg,
                ROOT / "codex" / "codex-config.snippet.toml",
                ROOT,
            ]
            run_script(*args)
            text = cfg.read_text(encoding="utf-8")
            self.assertNotIn("[mcp_servers.knowledge-based-search]", text)
            self.assertNotIn("mcp_server.py", text)
            self.assertIn("[mcp_servers.other]", text)
            self.assertIn('command = "x"', text)

    def test_codex_merge_strips_stale_quoted_kbs_mcp_table(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "config.toml"
            cfg.write_text(
                '[mcp_servers."knowledge-based-search"]\n'
                'command = "python3"\n'
                'args = ["/old/server/mcp_server.py"]\n'
                "\n"
                "[mcp_servers.other]\n"
                'command = "x"\n',
                encoding="utf-8",
            )
            args = [
                ROOT / "codex" / "merge-codex-config.py",
                cfg,
                ROOT / "codex" / "codex-config.snippet.toml",
                ROOT,
            ]
            run_script(*args)
            text = cfg.read_text(encoding="utf-8")
            self.assertNotIn('mcp_servers."knowledge-based-search"', text)
            self.assertNotIn("mcp_server.py", text)
            self.assertIn("[mcp_servers.other]", text)

    def test_pi_merge_preserves_unrelated_mcp_servers(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text(
                json.dumps(
                    {
                        "extensions": [],
                        "mcpServers": {
                            "knowledge-based-search": {"command": "old"},
                            "other": {"command": "x"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            ext = ROOT / "pi" / "extensions" / "knowledge-based-search" / "index.ts"
            run_script(ROOT / "pi" / "merge-pi-settings.py", cfg, ext)
            data = read_json(cfg)
            self.assertNotIn("knowledge-based-search", data["mcpServers"])
            self.assertEqual(data["mcpServers"], {"other": {"command": "x"}})


def _write_ready_venv(path: Path, owned: bool = True) -> None:
    python = path / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python.chmod(0o755)
    (path / "pyvenv.cfg").write_text("home = /tmp\n", encoding="utf-8")
    if owned:
        (path / ".kbs-owned-venv").touch()


def _copy_shell_lib(repo: Path) -> None:
    scripts = repo / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "lib.sh").write_text(
        (ROOT / "scripts" / "lib.sh").read_text(encoding="utf-8"), encoding="utf-8"
    )


def _run_remove(home: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOME": str(home),
        "KBS_BIN_DIR": str(home / "bin"),
        "KBS_VENV_DIR": str(home / "missing-venv"),
    }
    return subprocess.run(
        ["bash", str(ROOT / "remove.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _setup_explicit_codex_install(
    directory: str,
) -> tuple[Path, Path, dict[str, str]]:
    root = Path(directory)
    repo, home = root / "repo", root / "home"
    for path in (
        home / ".claude",
        home / ".codex",
        repo / "server",
        repo / "skills" / "knowledge-based-search",
        repo / "codex",
        repo / "pi" / "extensions" / "knowledge-based-search",
    ):
        path.mkdir(parents=True, exist_ok=True)
    (repo / "codex" / "codex-config.snippet.toml").write_text("", encoding="utf-8")
    write_installer_stub(repo / "codex" / "merge-codex-config.py", "codex")
    write_installer_stub(repo / "pi" / "merge-pi-settings.py", "pi")
    (repo / "install.sh").write_text((ROOT / "install.sh").read_text(), encoding="utf-8")
    _copy_shell_lib(repo)
    env = {**os.environ, "HOME": str(home)}
    return repo, home, env


def _setup_opencode_install(
    directory: str,
) -> tuple[Path, Path, Path, dict[str, str]]:
    root = Path(directory)
    home, repo = root / "home", root / "repo"
    agents_dir = home / ".config" / "opencode"
    for path in (agents_dir, repo / "server", repo / "bin", repo / "skills" / "knowledge-based-search", repo / "opencode" / "plugins"):
        path.mkdir(parents=True, exist_ok=True)
    (agents_dir / "AGENTS.md").write_text("old instructions\n", encoding="utf-8")
    files = {
        repo / "bin" / "kbs": "#!/usr/bin/env python3\nprint('stub')\n",
        repo / "opencode" / "plugins" / "knowledge-based-search.ts": "export {};\n",
        repo / "opencode" / "AGENTS.md": "Built-in Web Search is blocked.\n",
        repo / "install.sh": (ROOT / "install.sh").read_text(encoding="utf-8"),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    _copy_shell_lib(repo)
    venv = root / "venv"
    _write_ready_venv(venv)
    env = {**os.environ, "HOME": str(home), "KBS_BIN_DIR": str(root / "bin"), "KBS_VENV_DIR": str(venv)}
    return home, repo, agents_dir, env


def test_install_explicit_codex_target_skips_claude_auto_detection() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        repo, home, env = _setup_explicit_codex_install(td)
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


def test_install_opencode_creates_instruction_file() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home, repo, agents_dir, env = _setup_opencode_install(td)
        assert (agents_dir / "AGENTS.md").read_text(encoding="utf-8") == "old instructions\n"
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
        assert "old instructions" in content
        assert content.count("<!-- kbs:start -->") == 1
        assert "Web Search" in content and "blocked" in content
        assert (agents_dir / "plugins" / "knowledge-based-search.ts").exists()
        assert (agents_dir / "skills" / "knowledge-based-search").is_symlink()


def test_install_refuses_unowned_existing_venv() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        _, repo, _, env = _setup_opencode_install(td)
        marker = Path(env["KBS_VENV_DIR"]) / ".kbs-owned-venv"
        marker.unlink()
        result = subprocess.run(
            ["bash", str(repo / "install.sh"), "--opencode", "-y"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert not marker.exists()
        assert "refusing unowned venv" in result.stderr


def test_setup_refuses_home_as_venv() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home = Path(td) / "home"
        home.mkdir()
        env = {
            **os.environ,
            "HOME": str(home),
            "KBS_VENV_DIR": str(home),
            "KBS_BIN_DIR": str(Path(td) / "bin"),
        }
        result = subprocess.run(
            ["bash", str(ROOT / "scripts" / "setup.sh")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "refusing unsafe KBS_VENV_DIR" in result.stderr
        assert not (home / ".kbs-owned-venv").exists()


def test_reinstall_recognizes_escaped_wrapper_path() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        _, repo, _, env = _setup_opencode_install(td)
        spaced_repo = repo.with_name("repo with space")
        repo.rename(spaced_repo)
        command = ["bash", str(spaced_repo / "install.sh"), "--opencode", "-y"]
        subprocess.run(command, check=True, cwd=spaced_repo, env=env, capture_output=True)
        subprocess.run(command, check=True, cwd=spaced_repo, env=env, capture_output=True)
        wrapper = Path(env["KBS_BIN_DIR"]) / "kbs"
        assert not list(wrapper.parent.glob("kbs.kbs.*.bak"))


def test_install_refreshes_fenced_content_with_backslashes() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home, repo, _, env = _setup_opencode_install(td)
        source = repo / "opencode" / "AGENTS.md"
        command = ["bash", str(repo / "install.sh"), "--opencode", "-y"]
        source.write_text("literal \\1 content\n", encoding="utf-8")
        subprocess.run(command, check=True, cwd=repo, env=env, capture_output=True)
        source.write_text("literal \\2 content\n", encoding="utf-8")
        subprocess.run(command, check=True, cwd=repo, env=env, capture_output=True)
        content = (home / ".config" / "opencode" / "AGENTS.md").read_text(encoding="utf-8")
        assert "literal \\2 content" in content
        assert content.count("<!-- kbs:start -->") == 1


def test_remove_keeps_file_with_unclosed_fence() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home = Path(td) / "home"
        agents = home / ".config" / "zed" / "AGENTS.md"
        agents.parent.mkdir(parents=True)
        original = b"user instructions\n<!-- kbs:start -->\nkbs instructions\n"
        agents.write_bytes(original)
        result = _run_remove(home)
        assert result.returncode == 0, result.stderr
        assert agents.read_bytes() == original
        assert "malformed kbs fence markers" in result.stdout


def test_remove_deletes_legacy_zed_instructions() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home = Path(td) / "home"
        agents = home / ".config" / "zed" / "AGENTS.md"
        agents.parent.mkdir(parents=True)
        agents.write_text(LEGACY_ZED_INSTRUCTIONS, encoding="utf-8")
        result = _run_remove(home)
        assert result.returncode == 0, result.stderr
        assert not agents.exists()


def test_installer_stdout_includes_all_six_examples() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        _, repo, _, env = _setup_opencode_install(td)
        assert repo.exists()
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


def test_installer_binds_wrapper_to_kbs_virtual_environment() -> None:
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "python_has_requirements" not in text
    assert 'printf \'%s\\n\' "$VENV_DIR/bin/python"' in text


def _setup_zed_install(
    td: str, existing_agents: bool = True
) -> tuple[Path, Path, dict[str, str]]:
    home, repo = Path(td) / "home", Path(td) / "repo"
    for path in (home, repo):
        path.mkdir()
    if existing_agents:
        agents_dir = home / ".config" / "zed"
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
    _copy_shell_lib(repo)
    venv = Path(td) / "venv"
    _write_ready_venv(venv)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["KBS_BIN_DIR"] = str(Path(td) / "bin")
    env["KBS_VENV_DIR"] = str(venv)
    return home, repo, env


def test_install_zed_creates_instruction_file() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home, repo, env = _setup_zed_install(td)
        subprocess.run(
            ["bash", str(repo / "install.sh"), "--zed", "-y"],
            check=True,
            cwd=repo,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        agents_md = home / ".config" / "zed" / "AGENTS.md"
        backups = list(agents_md.parent.glob("AGENTS.md.kbs.*.bak"))
        assert agents_md.exists()
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "old instructions\n"
        content = agents_md.read_text(encoding="utf-8")
        assert "kbs quick" in content
        assert "kbs search" in content
        assert "kbs doctor" in content


def test_install_zcode_alias_writes_zed_instructions() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        home, repo, env = _setup_zed_install(td, existing_agents=False)
        subprocess.run(
            ["bash", str(repo / "install.sh"), "--zcode", "-y"],
            check=True,
            cwd=repo,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        agents_md = home / ".config" / "zed" / "AGENTS.md"
        assert agents_md.exists()
        content = agents_md.read_text(encoding="utf-8")
        assert "kbs quick" in content
        assert "kbs search" in content


if __name__ == "__main__":
    unittest.main()
