import yaml
from pathlib import Path
from dataclasses import dataclass

DEFAULTS = {
    "max_agents": 4,
    "worktree_dir": ".swarm",
    "branch_prefix": "swarm/",
    "auto_merge": False,
    "merge_strategy": "sequential",
    "on_conflict": "ask",
    "on_done": "notify",
    "default_agent": "claudecode",
}


@dataclass
class SwarmConfig:
    project: str
    max_agents: int
    worktree_dir: Path
    branch_prefix: str
    auto_merge: bool
    merge_strategy: str
    on_conflict: str
    on_done: str
    default_agent: str
    agents: dict
    agent_config: dict
    custom_agents: dict
    splitter: dict


def load_config(project_root: Path, overrides: dict | None = None) -> SwarmConfig:
    if overrides is None:
        overrides = {}

    config_path = project_root / "swarm.yml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"swarm.yml not found in {project_root}. Run: swarm init"
        )

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    merged = {**DEFAULTS, **raw, **overrides}

    return SwarmConfig(
        project=merged.get("project", project_root.name),
        max_agents=merged["max_agents"],
        worktree_dir=project_root / merged["worktree_dir"],
        branch_prefix=merged["branch_prefix"],
        auto_merge=merged["auto_merge"],
        merge_strategy=merged["merge_strategy"],
        on_conflict=merged["on_conflict"],
        on_done=merged["on_done"],
        default_agent=merged["default_agent"],
        agents=merged.get("agents", {}),
        agent_config=merged.get("agent_config", {}),
        custom_agents=merged.get("custom_agents", {}),
        splitter=merged.get(
            "splitter",
            {
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
                "api_key_env": "ANTHROPIC_API_KEY",
            },
        ),
    )
