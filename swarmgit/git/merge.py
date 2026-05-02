import subprocess
from pathlib import Path
from enum import Enum
from swarmgit.models import AgentRun


class MergeResult(Enum):
    SUCCESS = "success"
    CONFLICT = "conflict"
    SKIPPED = "skipped"


def merge_branch(
    repo_root: Path,
    agent: AgentRun,
    on_conflict: str = "ask",
) -> MergeResult:
    branch = agent.worktree.branch

    result = subprocess.run(
        ["git", "merge", "--no-ff", branch, "-m",
         f"Merge {branch}: {agent.task}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return MergeResult.SUCCESS

    conflict_detected = "CONFLICT" in result.stdout or "CONFLICT" in result.stderr
    if conflict_detected:
        if on_conflict == "abort":
            subprocess.run(["git", "merge", "--abort"], cwd=repo_root)
            return MergeResult.CONFLICT

        elif on_conflict == "auto-resolve":
            subprocess.run(["git", "checkout", "--theirs", "."], cwd=repo_root)
            subprocess.run(["git", "add", "-A"], cwd=repo_root)
            subprocess.run(
                ["git", "commit", "-m",
                 f"Merge {branch} (auto-resolved conflicts)"],
                cwd=repo_root,
            )
            return MergeResult.SUCCESS

        elif on_conflict == "ask":
            print(f"\n⚠️  Conflict merging {branch}")
            print("Resolve conflicts manually in the repo root, then run:")
            print("  git add -A && git commit")
            print("Or abort with: git merge --abort")
            input("\nPress Enter when you have resolved and committed...")
            return MergeResult.SUCCESS

    return MergeResult.SKIPPED


def delete_branch(repo_root: Path, branch: str) -> None:
    subprocess.run(
        ["git", "branch", "-d", branch],
        cwd=repo_root,
        check=False,
    )
