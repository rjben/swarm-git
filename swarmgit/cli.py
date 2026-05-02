import click
from pathlib import Path


@click.group()
@click.version_option("0.1.1", prog_name="swarm")
def main():
    """SwarmGit — Multi-agent Git worktree orchestrator for AI coding agents."""
    pass


@main.command()
@click.argument("project_name", default=".")
@click.option("--no-git", is_flag=True, help="Skip git init")
def init(project_name, no_git):
    """Initialize a new SwarmGit project."""
    from swarmgit.orchestrator import cmd_init
    cmd_init(Path(project_name).resolve(), no_git=no_git)


@main.command()
@click.argument("task")
def task(task):
    """Define and preview task splitting."""
    from swarmgit.orchestrator import cmd_task
    cmd_task(Path.cwd(), task)


@main.command()
@click.argument("task")
@click.option("--agent", default=None)
@click.option("--architect", default=None)
@click.option("--coder", default=None)
@click.option("--tester", default=None)
@click.option("--reviewer", default=None)
@click.option("--agents", "max_agents", default=None, type=int)
@click.option("--auto-merge", is_flag=True, default=False)
@click.option("--no-merge", is_flag=True, default=False)
def run(task, agent, architect, coder, tester, reviewer, max_agents, auto_merge, no_merge):
    """Run agents on a task end-to-end."""
    from swarmgit.orchestrator import cmd_run
    role_agents = {
        k: v
        for k, v in {
            "architect": architect or agent,
            "coder": coder or agent,
            "tester": tester or agent,
            "reviewer": reviewer or agent,
        }.items()
        if v
    }
    cmd_run(
        Path.cwd(),
        task,
        role_agents=role_agents,
        max_agents=max_agents,
        auto_merge=auto_merge,
        no_merge=no_merge,
    )


@main.command()
@click.option("--watch", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def status(watch, as_json):
    """Show agent status."""
    from swarmgit.orchestrator import cmd_status
    cmd_status(Path.cwd(), watch=watch, as_json=as_json)


@main.command()
@click.option("--agent", "agent_name", default=None)
@click.option("--auto", is_flag=True)
@click.option("--dry-run", is_flag=True)
def merge(agent_name, auto, dry_run):
    """Merge done agent branches into main."""
    from swarmgit.orchestrator import cmd_merge
    cmd_merge(Path.cwd(), agent_name=agent_name, auto=auto, dry_run=dry_run)


@main.command()
@click.argument("agent_name")
@click.option("--file", "file_path", default=None)
@click.option("--tree", is_flag=True)
@click.option("--log", is_flag=True)
def peek(agent_name, file_path, tree, log):
    """Inspect an agent branch without switching to it."""
    from swarmgit.orchestrator import cmd_peek
    cmd_peek(Path.cwd(), agent_name, file_path=file_path, tree=tree, log=log)


@main.command()
@click.argument("agent_name")
def diff(agent_name):
    """Diff agent branch vs main."""
    from swarmgit.orchestrator import cmd_diff
    cmd_diff(Path.cwd(), agent_name)


@main.command()
def doctor():
    """Check system requirements."""
    from swarmgit.orchestrator import cmd_doctor
    cmd_doctor()


@main.command()
@click.option("--force", is_flag=True)
@click.option("--keep-branches", is_flag=True)
def clean(force, keep_branches):
    """Remove all worktrees and branches."""
    from swarmgit.orchestrator import cmd_clean
    cmd_clean(Path.cwd(), force=force, keep_branches=keep_branches)


@main.group()
def agent():
    """Manual agent management."""
    pass


@agent.command("create")
@click.option("--name", required=True)
@click.option("--branch", required=True)
@click.option("--tool", default=None)
def agent_create(name, branch, tool):
    from swarmgit.orchestrator import cmd_agent_create
    cmd_agent_create(Path.cwd(), name=name, branch=branch, tool=tool)


@agent.command("assign")
@click.argument("agent_name")
@click.argument("task")
def agent_assign(agent_name, task):
    from swarmgit.orchestrator import cmd_agent_assign
    cmd_agent_assign(Path.cwd(), agent_name=agent_name, task=task)


@agent.command("logs")
@click.argument("agent_name")
@click.option("--follow", is_flag=True)
def agent_logs(agent_name, follow):
    from swarmgit.orchestrator import cmd_agent_logs
    cmd_agent_logs(Path.cwd(), agent_name=agent_name, follow=follow)


@agent.command("kill")
@click.argument("agent_name")
def agent_kill(agent_name):
    from swarmgit.orchestrator import cmd_agent_kill
    cmd_agent_kill(Path.cwd(), agent_name=agent_name)


@agent.command("list")
def agent_list():
    from swarmgit.orchestrator import cmd_agent_list
    cmd_agent_list(Path.cwd())


if __name__ == "__main__":
    main()
