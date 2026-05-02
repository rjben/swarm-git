from pathlib import Path
from swarmgit.adapters.base import BaseAdapter


class ClaudeCodeAdapter(BaseAdapter):
    name = "claudecode"
    requires_no_git = False

    def build_command(self, task: str, worktree_path: Path, config: dict) -> list[str]:
        prompt = (
            f"{task}\n\n"
            "When you are completely done, make a git commit with a clear message "
            "summarizing what you did. Do not ask for confirmation."
        )

        cmd = ["claude", "--print", prompt, "--no-verify"]

        if model := config.get("model"):
            cmd += ["--model", model]

        cmd += config.get("extra_flags", [])
        return cmd

    def is_done(self, output_line: str, exit_code: int | None) -> bool:
        if exit_code is not None:
            return exit_code == 0
        return False

    def get_env(self, config: dict) -> dict:
        return {}
