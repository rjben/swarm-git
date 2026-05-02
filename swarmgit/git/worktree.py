import subprocess
from pathlib import Path
from swarmgit.models import Worktree


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def create_worktree(
    repo_root: Path,
    worktree_path: Path,
    branch_name: str,
    agent_name: str,
) -> Worktree:
    worktree_path.mkdir(parents=True, exist_ok=True)
    _git(
        ["worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"],
        cwd=repo_root,
    )
    return Worktree(
        path=worktree_path,
        branch=branch_name,
        agent_name=agent_name,
    )


def remove_worktree(repo_root: Path, worktree_path: Path) -> None:
    _git(["worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)


def list_worktrees(repo_root: Path) -> list[dict]:
    result = _git(["worktree", "list", "--porcelain"], cwd=repo_root)
    worktrees = []
    current: dict = {}
    for line in result.stdout.splitlines():
        if line == "":
            if current:
                worktrees.append(current)
            current = {}
        elif line.startswith("worktree "):
            current["path"] = line[len("worktree "):]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):]
        elif line.startswith("HEAD "):
            current["HEAD"] = line[len("HEAD "):]
    if current:
        worktrees.append(current)
    return worktrees


def get_last_commit_message(worktree_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def has_uncommitted_changes(worktree_path: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())
