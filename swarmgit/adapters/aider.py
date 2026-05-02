import subprocess
from pathlib import Path
from swarmgit.adapters.base import BaseAdapter, AdapterResult


class AiderAdapter(BaseAdapter):
    name = "aider"
    requires_no_git = True

    def build_command(self, task: str, worktree_path: Path, config: dict) -> list[str]:
        cmd = [
            "aider",
            "--message",
            task,
            "--yes",
            "--no-git",
        ]

        if model := config.get("model"):
            cmd += ["--model", model]

        cmd += config.get("extra_flags", [])
        return cmd

    def is_done(self, output_line: str, exit_code: int | None) -> bool:
        if "Tokens:" in output_line:
            return True
        if exit_code is not None:
            return exit_code == 0
        return False

    def post_run(self, worktree_path: Path, result: AdapterResult) -> None:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=worktree_path,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "aider: task complete"],
            cwd=worktree_path,
            check=False,
        )
