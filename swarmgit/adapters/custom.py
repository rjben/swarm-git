import os
from pathlib import Path
from swarmgit.adapters.base import BaseAdapter


class CustomAdapter(BaseAdapter):
    def __init__(self, name: str, agent_def: dict):
        self.name = name
        self._command_template = agent_def["command"]
        self._done_signal = agent_def.get("done_signal", "")
        self._workdir_flag = agent_def.get("workdir_flag", None)
        self._env_template = agent_def.get("env", {})

    def build_command(self, task: str, worktree_path: Path, config: dict) -> list[str]:
        command_str = self._command_template.replace("{task}", task)
        cmd = command_str.split()
        if self._workdir_flag:
            cmd += [self._workdir_flag, str(worktree_path)]
        return cmd

    def is_done(self, output_line: str, exit_code: int | None) -> bool:
        if self._done_signal and self._done_signal in output_line:
            return True
        if exit_code is not None:
            return exit_code == 0
        return False

    def get_env(self, config: dict) -> dict:
        env = {}
        for key, value_template in self._env_template.items():
            if value_template.startswith("{") and value_template.endswith("}"):
                env_var = value_template[1:-1]
                env[key] = os.environ.get(env_var, "")
            else:
                env[key] = value_template
        return env
