from .claudecode import ClaudeCodeAdapter
from .opencode import OpenCodeAdapter
from .codex import CodexAdapter
from .aider import AiderAdapter
from .custom import CustomAdapter
from .base import BaseAdapter

BUILTIN_ADAPTERS: dict[str, type[BaseAdapter]] = {
    "claudecode": ClaudeCodeAdapter,
    "opencode": OpenCodeAdapter,
    "codex": CodexAdapter,
    "aider": AiderAdapter,
}


def get_adapter(name: str, custom_agents: dict | None = None) -> BaseAdapter:
    if custom_agents is None:
        custom_agents = {}

    if name in BUILTIN_ADAPTERS:
        return BUILTIN_ADAPTERS[name]()

    if name in custom_agents:
        return CustomAdapter(name=name, agent_def=custom_agents[name])

    available = list(BUILTIN_ADAPTERS.keys()) + list(custom_agents.keys())
    raise ValueError(
        f"Unknown agent: '{name}'. Available: {', '.join(available)}"
    )


def list_adapters() -> list[str]:
    return list(BUILTIN_ADAPTERS.keys())
