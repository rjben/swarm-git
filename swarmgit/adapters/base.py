from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AdapterResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str


class BaseAdapter(ABC):
    name: str = "base"
    requires_no_git: bool = False

    @abstractmethod
    def build_command(self, task: str, worktree_path: Path, config: dict) -> list[str]:
        pass

    @abstractmethod
    def is_done(self, output_line: str, exit_code: int | None) -> bool:
        pass

    def get_env(self, config: dict) -> dict:
        return {}

    def pre_run(self, worktree_path: Path, config: dict) -> None:
        pass

    def post_run(self, worktree_path: Path, result: AdapterResult) -> None:
        pass
