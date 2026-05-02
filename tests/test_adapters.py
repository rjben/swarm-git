import pytest
from pathlib import Path
from swarmgit.adapters.base import BaseAdapter, AdapterResult
from swarmgit.adapters.claudecode import ClaudeCodeAdapter
from swarmgit.adapters.opencode import OpenCodeAdapter
from swarmgit.adapters.codex import CodexAdapter
from swarmgit.adapters.aider import AiderAdapter
from swarmgit.adapters.custom import CustomAdapter


class TestClaudeCodeAdapter:
    def test_build_command(self):
        adapter = ClaudeCodeAdapter()
        cmd = adapter.build_command("hello", Path("/tmp/wt"), {})
        assert cmd[0] == "claude"
        assert "--print" in cmd
        assert any("hello" in part for part in cmd)

    def test_is_done_exit_zero(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.is_done("", 0) is True
        assert adapter.is_done("", 1) is False


class TestOpenCodeAdapter:
    def test_build_command(self):
        adapter = OpenCodeAdapter()
        cmd = adapter.build_command("test", Path("/tmp/wt"), {})
        assert cmd[0] == "opencode"
        assert "run" in cmd

    def test_is_done_signal(self):
        adapter = OpenCodeAdapter()
        assert adapter.is_done("Task complete", None) is True
        assert adapter.is_done("working...", None) is False


class TestCodexAdapter:
    def test_build_command(self):
        adapter = CodexAdapter()
        cmd = adapter.build_command("test", Path("/tmp/wt"), {})
        assert cmd[0] == "codex"

    def test_is_done_signal(self):
        adapter = CodexAdapter()
        assert adapter.is_done("All changes applied", None) is True


class TestAiderAdapter:
    def test_build_command(self):
        adapter = AiderAdapter()
        cmd = adapter.build_command("test", Path("/tmp/wt"), {})
        assert cmd[0] == "aider"
        assert "--no-git" in cmd

    def test_is_done_signal(self):
        adapter = AiderAdapter()
        assert adapter.is_done("Tokens: 1234", None) is True


class TestCustomAdapter:
    def test_build_command(self):
        adapter = CustomAdapter(
            "mytool",
            {"command": "mytool run {task}", "done_signal": "Done"},
        )
        cmd = adapter.build_command("hello", Path("/tmp/wt"), {})
        assert cmd == ["mytool", "run", "hello"]

    def test_is_done(self):
        adapter = CustomAdapter(
            "mytool",
            {"command": "mytool run {task}", "done_signal": "Done"},
        )
        assert adapter.is_done("Done", None) is True
        assert adapter.is_done("working", None) is False

    def test_env_substitution(self):
        import os
        os.environ["MYTOOL_KEY"] = "secret123"
        adapter = CustomAdapter(
            "mytool",
            {
                "command": "mytool run {task}",
                "env": {"API_KEY": "{MYTOOL_KEY}"},
            },
        )
        env = adapter.get_env({})
        assert env["API_KEY"] == "secret123"
