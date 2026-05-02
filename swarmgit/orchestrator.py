import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

from swarmgit.config import load_config
from swarmgit.models import AgentRun, AgentStatus, SwarmTask, Worktree
from swarmgit.adapters import get_adapter, list_adapters
from swarmgit.git.worktree import (
    create_worktree,
    remove_worktree,
    list_worktrees,
    has_uncommitted_changes,
)
from swarmgit.git.merge import merge_branch, delete_branch, MergeResult
from swarmgit.monitor.agent_monitor import AgentMonitor
from swarmgit.ui.status import display_status


def _ensure_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _write_state(repo_root: Path, task: SwarmTask | None) -> None:
    swarm_dir = repo_root / ".swarm"
    swarm_dir.mkdir(exist_ok=True)
    state_path = swarm_dir / "state.json"

    if task is None:
        if state_path.exists():
            state_path.unlink()
        return

    data = {
        "project": repo_root.name,
        "task": task.description,
        "created_at": datetime.now().isoformat(),
        "agents": [],
    }
    for agent in task.agents:
        data["agents"].append(
            {
                "name": agent.name,
                "tool": agent.tool,
                "task": agent.task,
                "branch": agent.worktree.branch,
                "worktree_path": str(agent.worktree.path.relative_to(repo_root)),
                "status": agent.status.value,
                "pid": agent.pid,
                "started_at": agent.started_at.isoformat() if agent.started_at else None,
                "finished_at": agent.finished_at.isoformat() if agent.finished_at else None,
                "last_commit": agent.last_commit,
                "error": agent.error,
            }
        )

    with open(state_path, "w") as f:
        json.dump(data, f, indent=2)


def _read_state(repo_root: Path) -> SwarmTask | None:
    state_path = repo_root / ".swarm" / "state.json"
    if not state_path.exists():
        return None

    with open(state_path) as f:
        data = json.load(f)

    task = SwarmTask(description=data.get("task", ""))
    for a in data.get("agents", []):
        worktree = Worktree(
            path=repo_root / a["worktree_path"],
            branch=a["branch"],
            agent_name=a["name"],
        )
        agent = AgentRun(
            name=a["name"],
            tool=a["tool"],
            task=a["task"],
            worktree=worktree,
            status=AgentStatus(a["status"]),
            pid=a.get("pid"),
            last_commit=a.get("last_commit"),
            error=a.get("error"),
        )
        if a.get("started_at"):
            agent.started_at = datetime.fromisoformat(a["started_at"])
        if a.get("finished_at"):
            agent.finished_at = datetime.fromisoformat(a["finished_at"])
        task.agents.append(agent)

    return task


def _on_status_change(repo_root: Path, task: SwarmTask):
    def callback(agent: AgentRun):
        _write_state(repo_root, task)

    return callback


def _split_task(task: str, config, max_agents: int = 4) -> list[str]:
    provider = config.splitter.get("provider", "anthropic")
    model = config.splitter.get("model", "claude-sonnet-4-5")
    api_key_env = config.splitter.get("api_key_env", "ANTHROPIC_API_KEY")
    api_key = os.environ.get(api_key_env, "")

    prompt = (
        f"You are a software project manager.\n"
        f"Split this development task into {max_agents} or fewer independent subtasks.\n\n"
        f"Task: {task}\n\n"
        "Rules:\n"
        "- Each subtask must be independently executable by a coding AI agent\n"
        "- Subtasks should be in logical order\n"
        "- Each subtask must be concrete and specific\n"
        "- Do not create subtasks that depend on each other's output if they run in parallel\n\n"
        "Respond ONLY with a JSON array of strings. No explanation. Example:\n"
        '["Setup project structure", "Implement auth system", "Write unit tests"]'
    )

    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    else:
        raise NotImplementedError(f"Provider '{provider}' not yet supported")

    raw = raw.strip("` \n")
    if raw.startswith("json"):
        raw = raw[4:]

    subtasks = json.loads(raw)
    return [s.strip() for s in subtasks if s.strip()]


def _resolve_agent_tool(role: str, role_agents: dict, config) -> str:
    return role_agents.get(role, config.agents.get(role, config.default_agent))


def _next_agent_name(existing: list[AgentRun]) -> str:
    idx = 1
    names = {a.name for a in existing}
    while f"agent-{idx}" in names:
        idx += 1
    return f"agent-{idx}"


def cmd_init(project_path: Path, no_git: bool = False) -> None:
    project_path.mkdir(parents=True, exist_ok=True)

    if not no_git and not _ensure_git_repo(project_path):
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=project_path, check=False)

    swarm_dir = project_path / ".swarm"
    swarm_dir.mkdir(exist_ok=True)

    config_path = project_path / "swarm.yml"
    if not config_path.exists():
        config_content = f"""project: {project_path.name}

splitter:
  provider: anthropic
  model: claude-sonnet-4-5
  api_key_env: ANTHROPIC_API_KEY

max_agents: 4
worktree_dir: .swarm
branch_prefix: swarm/

auto_merge: false
merge_strategy: sequential
on_conflict: ask
on_done: notify

default_agent: claudecode

agents:
  architect: claudecode
  coder: opencode
  tester: codex
  reviewer: aider

agent_config:
  claudecode:
    model: claude-sonnet-4-5
    extra_flags: []

  opencode:
    model: gpt-4o
    extra_flags: []

  codex:
    model: o4-mini
    extra_flags:
      - --approval-mode
      - auto-edit

  aider:
    model: gpt-4o
    extra_flags:
      - --yes
      - --no-git
"""
        with open(config_path, "w") as f:
            f.write(config_content)

    gitignore = project_path / ".gitignore"
    gitignore_entries = [".swarm/"]
    if gitignore.exists():
        content = gitignore.read_text()
        if ".swarm/" not in content:
            with open(gitignore, "a") as f:
                f.write("\n.swarm/\n")
    else:
        with open(gitignore, "w") as f:
            f.write("\n".join(gitignore_entries) + "\n")

    print(f"Initialized SwarmGit project at {project_path}")
    print("Run 'swarm task \"your task\"' to get started")


def cmd_task(repo_root: Path, task_str: str) -> SwarmTask:
    config = load_config(repo_root)
    subtasks = _split_task(task_str, config, max_agents=config.max_agents)

    print("Analyzing task...\n")
    print("Proposed subtasks:")
    for i, st in enumerate(subtasks, 1):
        print(f"  {i}. {st}")

    print(f"\n{len(subtasks)} agents will be spawned.")
    accept = input("Accept? [Y/n]: ").strip().lower()
    if accept and accept not in ("y", "yes"):
        print("Aborted.")
        return SwarmTask(description=task_str)

    swarm_task = SwarmTask(description=task_str, subtasks=subtasks)
    _write_state(repo_root, swarm_task)
    return swarm_task


def cmd_spawn(
    repo_root: Path,
    task: SwarmTask | None = None,
    role_agents: dict | None = None,
    max_agents: int | None = None,
) -> SwarmTask:
    config = load_config(repo_root)
    if role_agents is None:
        role_agents = {}
    if max_agents is None:
        max_agents = config.max_agents

    if task is None:
        task = _read_state(repo_root)
        if task is None:
            print("No active task. Run 'swarm task' first.")
            return SwarmTask(description="")

    existing = task.agents
    config = load_config(repo_root)
    monitor = AgentMonitor(on_status_change=_on_status_change(repo_root, task))

    roles = ["architect", "coder", "tester", "reviewer"]
    spawned = 0

    for i, subtask in enumerate(task.subtasks):
        if spawned >= max_agents:
            break

        role = roles[i % len(roles)]
        tool = _resolve_agent_tool(role, role_agents, config)
        agent_name = _next_agent_name(existing)
        branch_name = f"{config.branch_prefix}{agent_name}"
        worktree_path = config.worktree_dir / agent_name

        try:
            worktree = create_worktree(repo_root, worktree_path, branch_name, agent_name)
        except subprocess.CalledProcessError as e:
            print(f"Failed to create worktree for {agent_name}: {e}")
            continue

        agent = AgentRun(
            name=agent_name,
            tool=tool,
            task=subtask,
            worktree=worktree,
        )
        existing.append(agent)
        _write_state(repo_root, task)

        adapter = get_adapter(tool, config.custom_agents)
        agent_config = config.agent_config.get(tool, {})
        monitor.launch(agent, adapter, agent_config)
        spawned += 1
        print(f"Spawned {agent_name} ({tool}) -> {branch_name}")

    return task


def cmd_run(
    repo_root: Path,
    task_str: str,
    role_agents: dict | None = None,
    max_agents: int | None = None,
    auto_merge: bool = False,
    no_merge: bool = False,
) -> None:
    config = load_config(repo_root)
    if max_agents is None:
        max_agents = config.max_agents

    print(f"Task: {task_str}")
    subtasks = _split_task(task_str, config, max_agents=max_agents)
    print(f"Split into {len(subtasks)} subtasks\n")

    task = SwarmTask(description=task_str, subtasks=subtasks)
    _write_state(repo_root, task)

    task = cmd_spawn(repo_root, task=task, role_agents=role_agents, max_agents=max_agents)

    if not task.agents:
        print("No agents were spawned.")
        return

    print("\nWaiting for agents to complete...")
    monitor = AgentMonitor(on_status_change=_on_status_change(repo_root, task))
    monitor.wait_all()

    done = [a for a in task.agents if a.status == AgentStatus.DONE]
    failed = [a for a in task.agents if a.status == AgentStatus.FAILED]

    print(f"\n{len(done)} done, {len(failed)} failed")

    if no_merge:
        print("Skipping merge (--no-merge)")
        return

    if auto_merge or config.auto_merge:
        print("\nMerging done agents into main...")
        for agent in done:
            result = merge_branch(repo_root, agent, on_conflict=config.on_conflict)
            if result == MergeResult.SUCCESS:
                agent.status = AgentStatus.MERGED
                delete_branch(repo_root, agent.worktree.branch)
                print(f"  ✅ {agent.name} merged")
            else:
                print(f"  ❌ {agent.name} merge failed")
        _write_state(repo_root, task)
    else:
        print("\nRun 'swarm merge' to merge completed agents.")


def cmd_status(repo_root: Path, watch: bool = False, as_json: bool = False) -> None:
    task = _read_state(repo_root)
    if task is None:
        print("No active task. Run 'swarm task' first.")
        return

    if as_json:
        print(json.dumps({
            "project": repo_root.name,
            "task": task.description,
            "agents": [
                {
                    "name": a.name,
                    "tool": a.tool,
                    "branch": a.worktree.branch,
                    "status": a.status.value,
                    "last_commit": a.last_commit,
                }
                for a in task.agents
            ],
        }, indent=2))
        return

    if watch:
        try:
            while True:
                print("\033[H\033[J", end="")
                task = _read_state(repo_root)
                display_status(task.agents, repo_root.name)
                time.sleep(2)
        except KeyboardInterrupt:
            pass
    else:
        display_status(task.agents, repo_root.name)


def cmd_merge(
    repo_root: Path,
    agent_name: str | None = None,
    auto: bool = False,
    dry_run: bool = False,
) -> None:
    config = load_config(repo_root)
    task = _read_state(repo_root)
    if task is None:
        print("No active task.")
        return

    done_agents = [a for a in task.agents if a.status == AgentStatus.DONE]

    if agent_name:
        done_agents = [a for a in done_agents if a.name == agent_name]

    if not done_agents:
        print("No agents ready to merge.")
        return

    if dry_run:
        print("Dry run — would merge:")
        for agent in done_agents:
            print(f"  {agent.name} ({agent.worktree.branch})")
        return

    for agent in done_agents:
        result = merge_branch(repo_root, agent, on_conflict=config.on_conflict)
        if result == MergeResult.SUCCESS:
            agent.status = AgentStatus.MERGED
            delete_branch(repo_root, agent.worktree.branch)
            print(f"✅ {agent.name} merged cleanly")
        elif result == MergeResult.CONFLICT:
            print(f"❌ {agent.name} conflicted — skipped")
        else:
            print(f"⚠️  {agent.name} merge skipped")

    _write_state(repo_root, task)


def cmd_peek(
    repo_root: Path,
    agent_name: str,
    file_path: str | None = None,
    tree: bool = False,
    log: bool = False,
) -> None:
    task = _read_state(repo_root)
    if task is None:
        print("No active task.")
        return

    agent = next((a for a in task.agents if a.name == agent_name), None)
    if agent is None:
        print(f"Agent '{agent_name}' not found.")
        return

    wt_path = agent.worktree.path

    if file_path:
        target = wt_path / file_path
        if target.exists():
            print(target.read_text())
        else:
            print(f"File not found: {target}")
        return

    if tree:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            cwd=wt_path,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return

    if log:
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=wt_path,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return

    print(f"Agent: {agent.name}")
    print(f"Tool: {agent.tool}")
    print(f"Branch: {agent.worktree.branch}")
    print(f"Worktree: {agent.worktree.path}")
    print(f"Status: {agent.status.value}")
    print(f"Task: {agent.task}")


def cmd_diff(repo_root: Path, agent_name: str) -> None:
    task = _read_state(repo_root)
    if task is None:
        print("No active task.")
        return

    agent = next((a for a in task.agents if a.name == agent_name), None)
    if agent is None:
        print(f"Agent '{agent_name}' not found.")
        return

    result = subprocess.run(
        ["git", "diff", "main..." + agent.worktree.branch],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    print(result.stdout or result.stderr or "No diff.")


def cmd_doctor() -> None:
    print("SwarmGit Doctor")
    print("─" * 40)

    git_ok = False
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        version = result.stdout.strip().replace("git version ", "")
        major, minor = map(int, version.split(".")[:2])
        if major > 2 or (major == 2 and minor >= 30):
            print(f"✅ Git {version} (worktree supported)")
            git_ok = True
        else:
            print(f"⚠️  Git {version} (2.30+ required)")
    except FileNotFoundError:
        print("❌ Git not found")

    try:
        import sys
        print(f"✅ Python {sys.version.split()[0]}")
    except Exception:
        print("❌ Python check failed")

    available = []
    for name in list_adapters():
        try:
            result = subprocess.run([name, "--version"], capture_output=True, text=True)
            if result.returncode in (0, 1):
                print(f"✅ {name} found")
                available.append(name)
            else:
                print(f"⚠️  {name} not found")
        except FileNotFoundError:
            print(f"⚠️  {name} not found")

    print("─" * 40)
    print(f"{len(available)} agents ready")


def cmd_clean(repo_root: Path, force: bool = False, keep_branches: bool = False) -> None:
    task = _read_state(repo_root)
    if task is not None:
        running = [a for a in task.agents if a.status == AgentStatus.WORKING]
        if running and not force:
            print(f"{len(running)} agents still working. Use --force to clean anyway.")
            return

    config = load_config(repo_root)
    for wt in list_worktrees(repo_root):
        path = Path(wt["path"])
        branch = wt.get("branch", "")
        if str(config.worktree_dir) in str(path):
            try:
                remove_worktree(repo_root, path)
                print(f"Removed worktree: {path}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to remove {path}: {e}")

            if not keep_branches and branch:
                delete_branch(repo_root, branch)
                print(f"Deleted branch: {branch}")

    _write_state(repo_root, None)
    print("Cleaned up.")


def cmd_agent_create(repo_root: Path, name: str, branch: str, tool: str | None = None) -> None:
    config = load_config(repo_root)
    if tool is None:
        tool = config.default_agent

    worktree_path = config.worktree_dir / name
    try:
        worktree = create_worktree(repo_root, worktree_path, branch, name)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create worktree: {e}")
        return

    task = _read_state(repo_root) or SwarmTask(description="manual")
    agent = AgentRun(name=name, tool=tool, task="", worktree=worktree)
    task.agents.append(agent)
    _write_state(repo_root, task)
    print(f"Created agent {name} on branch {branch}")


def cmd_agent_assign(repo_root: Path, agent_name: str, task_str: str) -> None:
    task = _read_state(repo_root)
    if task is None:
        print("No active task.")
        return

    agent = next((a for a in task.agents if a.name == agent_name), None)
    if agent is None:
        print(f"Agent '{agent_name}' not found.")
        return

    agent.task = task_str
    _write_state(repo_root, task)
    print(f"Assigned task to {agent_name}")


def cmd_agent_logs(repo_root: Path, agent_name: str, follow: bool = False) -> None:
    print("Agent logs not yet implemented (agents log to stdout/stderr)")


def cmd_agent_kill(repo_root: Path, agent_name: str) -> None:
    import psutil

    task = _read_state(repo_root)
    if task is None:
        print("No active task.")
        return

    agent = next((a for a in task.agents if a.name == agent_name), None)
    if agent is None:
        print(f"Agent '{agent_name}' not found.")
        return

    if agent.pid:
        try:
            p = psutil.Process(agent.pid)
            p.terminate()
            agent.status = AgentStatus.FAILED
            agent.error = "Killed by user"
            _write_state(repo_root, task)
            print(f"Killed {agent_name} (pid {agent.pid})")
        except psutil.NoSuchProcess:
            print(f"Process {agent.pid} not found.")
    else:
        print(f"No running process for {agent_name}")


def cmd_agent_list(repo_root: Path) -> None:
    task = _read_state(repo_root)
    if task is None or not task.agents:
        print("No agents.")
        return

    for agent in task.agents:
        print(f"{agent.name}: {agent.tool} ({agent.status.value}) — {agent.task}")
