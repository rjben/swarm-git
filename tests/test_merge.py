import pytest
import subprocess
from pathlib import Path
from swarmgit.models import AgentRun, Worktree
from swarmgit.git.merge import merge_branch, delete_branch, MergeResult


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "main.txt").write_text("main content")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    return repo


class TestMerge:
    def test_merge_success(self, temp_repo):
        subprocess.run(["git", "checkout", "-b", "feature"], cwd=temp_repo, check=True)
        (temp_repo / "feature.txt").write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
        subprocess.run(["git", "commit", "-m", "feature commit"], cwd=temp_repo, check=True)
        subprocess.run(["git", "checkout", "main"], cwd=temp_repo, check=True)

        agent = AgentRun(
            name="agent-1",
            tool="claudecode",
            task="add feature",
            worktree=Worktree(path=temp_repo, branch="feature", agent_name="agent-1"),
        )
        result = merge_branch(temp_repo, agent, on_conflict="abort")
        assert result == MergeResult.SUCCESS

    def test_delete_branch(self, temp_repo):
        subprocess.run(["git", "branch", "to-delete"], cwd=temp_repo, check=True)
        delete_branch(temp_repo, "to-delete")
        result = subprocess.run(
            ["git", "branch", "--list", "to-delete"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )
        assert "to-delete" not in result.stdout
