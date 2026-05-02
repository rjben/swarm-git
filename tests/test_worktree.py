import pytest
import subprocess
from pathlib import Path
from swarmgit.git.worktree import create_worktree, remove_worktree, list_worktrees


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)
    return repo


class TestWorktree:
    def test_create_and_list(self, temp_repo):
        wt_path = temp_repo / ".swarm" / "agent-1"
        wt = create_worktree(temp_repo, wt_path, "swarm/agent-1", "agent-1")
        assert wt.branch == "swarm/agent-1"
        assert wt_path.exists()

        wts = list_worktrees(temp_repo)
        paths = [w["path"] for w in wts]
        assert str(wt_path) in paths

    def test_remove_worktree(self, temp_repo):
        wt_path = temp_repo / ".swarm" / "agent-2"
        create_worktree(temp_repo, wt_path, "swarm/agent-2", "agent-2")
        assert wt_path.exists()
        remove_worktree(temp_repo, wt_path)
        assert not wt_path.exists()
