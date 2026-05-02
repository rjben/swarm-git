from rich.console import Console
from rich.table import Table
from swarmgit.models import AgentRun, AgentStatus

console = Console()


STATUS_ICONS = {
    AgentStatus.WAITING: "⏳",
    AgentStatus.WORKING: "🟡",
    AgentStatus.DONE: "✅",
    AgentStatus.FAILED: "❌",
    AgentStatus.MERGED: "🔀",
}


def display_status(agents: list[AgentRun], project_name: str) -> None:
    table = Table(title=f"SwarmGit — {project_name}")
    table.add_column("Agent", style="cyan")
    table.add_column("Tool", style="magenta")
    table.add_column("Branch", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Last Commit", style="white")

    counts = {status: 0 for status in AgentStatus}

    for agent in agents:
        counts[agent.status] += 1
        icon = STATUS_ICONS.get(agent.status, "❓")
        table.add_row(
            agent.name,
            agent.tool,
            agent.worktree.branch,
            f"{icon} {agent.status.value}",
            agent.last_commit or "—",
        )

    console.print(table)

    summary_parts = []
    if counts[AgentStatus.DONE]:
        summary_parts.append(f"{counts[AgentStatus.DONE]} done")
    if counts[AgentStatus.WORKING]:
        summary_parts.append(f"{counts[AgentStatus.WORKING]} working")
    if counts[AgentStatus.WAITING]:
        summary_parts.append(f"{counts[AgentStatus.WAITING]} waiting")
    if counts[AgentStatus.FAILED]:
        summary_parts.append(f"{counts[AgentStatus.FAILED]} failed")
    if counts[AgentStatus.MERGED]:
        summary_parts.append(f"{counts[AgentStatus.MERGED]} merged")

    if summary_parts:
        console.print(" · ".join(summary_parts))
    else:
        console.print("No agents running.")
