from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime


class AgentStatus(Enum):
    WAITING = "waiting"
    WORKING = "working"
    DONE = "done"
    FAILED = "failed"
    MERGED = "merged"


@dataclass
class Worktree:
    path: Path
    branch: str
    agent_name: str


@dataclass
class AgentRun:
    name: str
    tool: str
    task: str
    worktree: Worktree
    status: AgentStatus = AgentStatus.WAITING
    pid: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_commit: str | None = None
    error: str | None = None


@dataclass
class SwarmTask:
    description: str
    subtasks: list[str] = field(default_factory=list)
    agents: list[AgentRun] = field(default_factory=list)
