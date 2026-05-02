from pathlib import Path
from swarmgit.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    name = "codex"
    requires_no_git = False

    def build_command(self, task: str, worktree_path: Path, config: dict) -> list[str]:
        prompt = (
            f"{task}\n\n"
            "When completely done, run git commit with a descriptive message."
        )

        cmd = [
            "codex",
            prompt,
            "--approval-mode",
            "auto-edit",
        ]

        if model := config.get("model"):
            cmd += ["--model", model]

        cmd += config.get("extra_flags", [])
        return cmd

    def is_done(self, output_line: str, exit_code: int | None) -> bool:
        if "All changes applied" in output_line:
            return True
        if exit_code is not None:
            return exit_code == 0
        return False
