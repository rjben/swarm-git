import subprocess
import threading
import os
from pathlib import Path
from datetime import datetime
from swarmgit.models import AgentRun, AgentStatus
from swarmgit.adapters.base import BaseAdapter, AdapterResult
from swarmgit.git.worktree import get_last_commit_message


class AgentMonitor:
    def __init__(self, on_status_change=None):
        self._on_status_change = on_status_change
        self._threads: list[threading.Thread] = []

    def launch(self, agent: AgentRun, adapter: BaseAdapter, config: dict) -> None:
        t = threading.Thread(
            target=self._run_agent,
            args=(agent, adapter, config),
            daemon=True,
        )
        self._threads.append(t)
        t.start()

    def wait_all(self) -> None:
        for t in self._threads:
            t.join()

    def _run_agent(self, agent: AgentRun, adapter: BaseAdapter, config: dict) -> None:
        agent.status = AgentStatus.WORKING
        agent.started_at = datetime.now()
        self._notify(agent)

        cmd = adapter.build_command(agent.task, agent.worktree.path, config)
        extra_env = adapter.get_env(config)
        adapter.pre_run(agent.worktree.path, config)

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=agent.worktree.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ, **extra_env},
            )
            agent.pid = proc.pid

            for line in proc.stdout:
                line = line.rstrip()
                if adapter.is_done(line, None):
                    proc.terminate()
                    break

            proc.wait()
            exit_code = proc.returncode

            agent.last_commit = get_last_commit_message(agent.worktree.path)

            adapter.post_run(
                agent.worktree.path,
                AdapterResult(
                    success=(exit_code == 0),
                    exit_code=exit_code,
                    stdout="",
                    stderr="",
                ),
            )

            if exit_code == 0 or adapter.is_done("", exit_code):
                agent.status = AgentStatus.DONE
            else:
                agent.status = AgentStatus.FAILED
                agent.error = f"Exit code {exit_code}"

        except Exception as e:
            agent.status = AgentStatus.FAILED
            agent.error = str(e)

        agent.finished_at = datetime.now()
        self._notify(agent)

    def _notify(self, agent: AgentRun) -> None:
        if self._on_status_change:
            self._on_status_change(agent)
