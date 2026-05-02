import pytest
from pathlib import Path
from swarmgit.orchestrator import cmd_init, _read_state


class TestOrchestrator:
    def test_cmd_init_creates_files(self, tmp_path):
        project = tmp_path / "new-project"
        cmd_init(project, no_git=True)
        assert (project / "swarm.yml").exists()
        assert (project / ".gitignore").exists()
        assert (project / ".swarm").exists()

    def test_read_state_none(self, tmp_path):
        project = tmp_path / "empty"
        project.mkdir()
        assert _read_state(project) is None
