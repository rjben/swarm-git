# SwarmGit — Multi-Agent Git Worktree Orchestrator for AI Coding Agents

> Run multiple AI coding agents in parallel using native `git worktree`. Each agent gets an isolated branch and working directory. Zero conflicts, maximum velocity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/swarmgit/)
[![GitHub Stars](https://img.shields.io/github/stars/rjben/swarm-git?style=social)](https://github.com/rjben/swarm-git)

**SwarmGit** is an open-source multi-agent orchestration CLI that solves the biggest pain point in AI-assisted software development: **AI coding agents can't work in parallel on the same codebase without overwriting each other.**

By leveraging native `git worktree`, SwarmGit gives every agent its own isolated workspace and branch. When agents finish, their changes are merged back into `main` automatically. It's like Kubernetes for AI coding agents — but for Git.

---

## Table of Contents

- [What is SwarmGit?](#what-is-swarmgit)
- [The Problem (With a Real Example)](#the-problem-with-a-real-example)
- [Supported AI Coding Agents](#supported-ai-coding-agents)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Real-World Walkthrough](#real-world-walkthrough)
- [CLI Reference with Examples](#cli-reference-with-examples)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Agent Adapters](#agent-adapters)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is SwarmGit?

SwarmGit is a **Git worktree orchestrator** designed specifically for the era of AI coding agents. It enables:

- **Parallel agent execution** — Run Claude Code, Aider, Codex, and OpenCode simultaneously on different parts of your project
- **Automatic branch isolation** — Each agent works in its own Git worktree linked to a dedicated branch
- **Smart merge coordination** — Completed agent branches are merged into `main` sequentially with conflict resolution
- **Zero directory switching** — Agents never run `git checkout`; each worktree is permanently bound to its branch
- **LLM-powered task splitting** — Automatically decompose large tasks into parallel subtasks using Claude or OpenAI

### Use Cases

- **Microservice scaffolding** — Have one agent set up the API, another write auth, and a third write tests — all at the same time
- **Refactoring at scale** — Split a monolith refactor across multiple agents working in parallel
- **Multi-language projects** — Frontend agent builds the React app while the backend agent writes the FastAPI server
- **Test generation** — Spawn dedicated tester agents to write unit tests while the primary agent implements features

---

## The Problem (With a Real Example)

### Before SwarmGit — The Overwrite Nightmare

Imagine you want to build a REST API with authentication and tests. You have Claude Code and Aider installed. Here's what happens without SwarmGit:

```bash
# Terminal 1 — You ask Claude to build the API
$ claude "Build a FastAPI REST API with JWT auth"
# Claude starts editing app.py, models.py, auth.py...

# Terminal 2 — You ask Aider to write tests
$ aider "Write pytest unit tests for the auth module"
# Aider starts editing test_auth.py — but also touches app.py

# Result: Aider's changes to app.py overwrite Claude's changes.
# You lose hours of work and have to start over.
```

**Workarounds people try:**
- **Copy directories manually** — Lose git history, can't merge back easily
- **Switch branches constantly** — Confusing, error-prone, agents hate it
- **Run agents one at a time** — Defeats the purpose of having fast AI agents

### After SwarmGit — Parallel Execution, Zero Conflicts

```bash
# One command. SwarmGit handles everything.
$ swarm run "Build a FastAPI REST API with JWT auth and tests"

# SwarmGit automatically:
# 1. Splits the task into subtasks
# 2. Creates isolated worktrees for each agent
# 3. Launches agents in parallel
# 4. Monitors progress
# 5. Merges results when done
```

**Result:** Claude works in `.swarm/agent-1/`, Aider works in `.swarm/agent-2/`. Both commit to their own branches. SwarmGit merges them into `main` when done. **No overwrites. No lost work.**

---

## Supported AI Coding Agents

SwarmGit includes built-in adapters for the most popular AI coding agents. Adding a new agent requires only ~50 lines of Python.

| Agent | CLI Command | Adapter Status | Git Integration |
|---|---|---|---|
| **Claude Code** | `claude` | ✅ Built-in | Native Git commits |
| **OpenCode** | `opencode` | ✅ Built-in | Native Git commits |
| **OpenAI Codex** | `codex` | ✅ Built-in | Native Git commits |
| **Aider** | `aider` | ✅ Built-in | Managed by SwarmGit (`--no-git`) |
| **Custom Agent** | User-defined | ✅ Configurable | Via `swarm.yml` |

---

## How It Works

```
User runs:
  swarm run "Build a REST API with auth and tests"
        │
        ▼
  1. Orchestrator calls LLM (Claude/OpenAI) to split task into subtasks
        │
        ▼
  2. WorktreeManager creates one git worktree per subtask
     .swarm/agent-1/  →  branch: swarm/agent-1
     .swarm/agent-2/  →  branch: swarm/agent-2
     .swarm/agent-3/  →  branch: swarm/agent-3
        │
        ▼
  3. Each agent launches inside its worktree directory
     claude, opencode, codex, aider — whatever is configured
        │
        ▼
  4. AgentMonitor watches each agent process for completion
        │
        ▼
  5. MergeCoordinator merges DONE branches into main sequentially
        │
        ▼
  6. WorktreeManager cleans up worktrees
```

### Directory Layout

```
/my-project/              ← main repo, always on branch: main
/my-project/.swarm/
    agent-1/              ← permanently on branch: swarm/agent-1
    agent-2/              ← permanently on branch: swarm/agent-2
    agent-3/              ← permanently on branch: swarm/agent-3
```

**Critical principle:** Agents never run `git checkout`. Each worktree is permanently mapped to its branch via `git worktree`. Your main repo stays on `main` at all times.

---

## Installation

### Requirements

- Python 3.10 or higher
- Git 2.30 or higher (for worktree support)
- At least one supported AI coding agent installed

### Install from PyPI

```bash
pip install swarmgit
```

### Install from Source

```bash
git clone https://github.com/rjben/swarm-git.git
cd swarm-git
pip install -e ".[dev]"
```

### Verify Installation

```bash
$ swarm --version
swarm, version 0.1.0

$ swarm doctor
SwarmGit Doctor
────────────────────────────────────────
✅ Git 2.43.0 (worktree supported)
✅ Python 3.12.3
✅ claudecode found at /usr/local/bin/claude
✅ opencode found at /usr/local/bin/opencode
⚠️  codex not found (install: npm install -g @openai/codex)
⚠️  aider not found (install: pip install aider-chat)
────────────────────────────────────────
2 agents ready · 1 warning · 1 missing
```

---

## Real-World Walkthrough

Let's build a real project together. We'll create a Python CLI tool with auth, tests, and documentation — all in parallel using 3 agents.

### Step 1: Initialize the Project

```bash
$ mkdir url-shortener && cd url-shortener
$ swarm init .
Initialized empty Git repository in /home/user/url-shortener/.git/
Initialized SwarmGit project at /home/user/url-shortener
Run 'swarm task "your task"' to get started

$ ls -la
total 24
drwxr-xr-x 4 user user 4096 May  3 10:00 .
drwxr-xr-x 6 user user 4096 May  3 10:00 ..
drwxr-xr-x 8 user user 4096 May  3 10:00 .git
-rw-r--r--r-- 1 user user  655 May  3 10:00 swarm.yml
drwxr-xr-xr-x 2 user user 4096 May  3 10:00 .swarm
-rw-r--r--r-- 1 user user    8 May  3 10:00 .gitignore
```

### Step 2: Configure Agents

Edit `swarm.yml` and set your API key:

```yaml
splitter:
  provider: anthropic
  model: claude-sonnet-4-5
  api_key_env: ANTHROPIC_API_KEY

default_agent: claudecode
max_agents: 3
```

### Step 3: Preview Task Splitting

```bash
$ swarm task "Build a URL shortener CLI in Python with Click, SQLite storage, unit tests, and a README"
Analyzing task...

Proposed subtasks:
  1. Create project structure, setup.py, and Click CLI skeleton with add/list/delete commands
  2. Implement SQLite database layer and URL shortening logic with hash generation
  3. Write pytest unit tests for database operations and CLI commands

3 agents will be spawned.
Accept? [Y/n]: y
```

### Step 4: Run the Swarm

```bash
$ swarm run "Build a URL shortener CLI in Python with Click, SQLite storage, unit tests, and a README"
Task: Build a URL shortener CLI in Python with Click, SQLite storage, unit tests, and a README
Split into 3 subtasks

Spawned agent-1 (claudecode) -> swarm/agent-1
Spawned agent-2 (opencode) -> swarm/agent-2
Spawned agent-3 (codex) -> swarm/agent-3

Waiting for agents to complete...
```

### Step 5: Monitor Progress (In Another Terminal)

```bash
$ swarm status --watch

SwarmGit — url-shortener
──────────────────────────────────────────────────────────
AGENT      TOOL          BRANCH              STATUS        LAST COMMIT
agent-1    claudecode    swarm/agent-1       ✅ done       "setup project structure and cli skeleton"
agent-2    opencode      swarm/agent-2       🟡 working    "implemented sqlite storage layer"
agent-3    codex         swarm/agent-3       ⏳ waiting    —
──────────────────────────────────────────────────────────
1 done · 1 working · 1 waiting · 0 failed
```

### Step 6: Inspect Agent Work

```bash
# Check what agent-1 built without switching branches
$ swarm peek agent-1 --tree
.
├── setup.py
├── urlshortener/
│   ├── __init__.py
│   └── cli.py
└── README.md

# Read a specific file
$ swarm peek agent-1 --file urlshortener/cli.py
import click

@click.group()
def cli():
    """URL Shortener CLI"""
    pass

@cli.command()
@click.argument('url')
def add(url):
    """Add a URL and return a short code"""
    pass

# See the diff before merging
$ swarm diff agent-1
diff --git a/setup.py b/setup.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/setup.py
@@ -0,0 +1,15 @@
+from setuptools import setup, find_packages
+
+setup(
+    name='urlshortener',
+    version='0.1.0',
+    packages=find_packages(),
+    install_requires=['click'],
+    entry_points={
+        'console_scripts': [
+            'urlshortener=urlshortener.cli:cli',
+        ],
+    },
+)
```

### Step 7: Merge Results

```bash
$ swarm merge
Merging agent-1 (swarm/agent-1) → main ...  ✅ clean
Merging agent-2 (swarm/agent-2) → main ...  ✅ clean
Merging agent-3 (swarm/agent-3) → main ...  ✅ clean

# Check the final result
$ git log --oneline -5
a1b2c3d Merge swarm/agent-3: Write pytest unit tests for database operations and CLI commands
e4f5g6h Merge swarm/agent-2: Implement SQLite database layer and URL shortening logic
i7j8k9l Merge swarm/agent-1: Create project structure, setup.py, and Click CLI skeleton
m0n1o2p Initial commit

$ ls -la
total 40
drwxr-xr-x 5 user user 4096 May  3 10:15 .
drwxr-xr-x 6 user user 4096 May  3 10:00 ..
drwxr-xr-x 8 user user 4096 May  3 10:15 .git
-rw-r--r--r-- 1 user user  655 May  3 10:00 swarm.yml
drwxr-xr-x 2 user user 4096 May  3 10:15 .swarm
drwxr-xr--r-- 1 user user    8 May  3 10:00 .gitignore
-rw-r--r--r-- 1 user user 1500 May  3 10:15 README.md
-rw-r--r--r-- 1 user user  300 May  3 10:15 setup.py
drwxr-xr-x 3 user user 4096 May  3 10:15 tests/
drwxr-xr-x 3 user user 4096 May  3 10:15 urlshortener/
```

### Step 8: Clean Up

```bash
$ swarm clean
Removed worktree: /home/user/url-shortener/.swarm/agent-1
Deleted branch: swarm/agent-1
Removed worktree: /home/user/url-shortener/.swarm/agent-2
Deleted branch: swarm/agent-2
Removed worktree: /home/user/url-shortener/.swarm/agent-3
Deleted branch: swarm/agent-3
Cleaned up.
```

**Done!** You now have a complete URL shortener project built by 3 agents working in parallel, with zero conflicts.

---

## CLI Reference with Examples

### `swarm init [project-name]`

Initialize a new SwarmGit project.

```bash
$ swarm init my-api
Initialized empty Git repository in /home/user/my-api/.git/
Initialized SwarmGit project at /home/user/my-api
Run 'swarm task "your task"' to get started
```

**Creates:**
- `swarm.yml` — your orchestration config
- `.swarm/` directory — where worktrees live
- `.gitignore` entry for `.swarm/`
- Initializes Git if not already a repo

---

### `swarm task "description"`

Preview how a task will be split into subtasks before spawning agents.

```bash
$ swarm task "Build a REST API with JWT auth and user CRUD"
Analyzing task...

Proposed subtasks:
  1. Setup project structure and dependencies
  2. Implement JWT authentication
  3. Build user CRUD endpoints
  4. Write unit and integration tests

4 agents will be spawned.
Accept? [Y/n]: y
```

---

### `swarm run "description" [options]`

All-in-one command: split, spawn, monitor, and optionally merge.

```bash
# Basic usage
$ swarm run "Build a todo REST API"

# Use a specific agent for all roles
$ swarm run "Build a todo REST API" --agent claudecode

# Auto-merge when agents finish
$ swarm run "Build a todo REST API" --auto-merge

# Assign different agents per role
$ swarm run "Build a todo REST API" --coder opencode --tester codex

# Limit parallel agents
$ swarm run "Build a todo REST API" --agents 2
```

---

### `swarm status [--watch] [--json]`

Show current state of all agents.

```bash
# One-time status
$ swarm status
SwarmGit — my-project
──────────────────────────────────────────────────────────
AGENT      TOOL          BRANCH              STATUS        LAST COMMIT
agent-1    claudecode    swarm/agent-1       ✅ done       "setup project structure"
agent-2    opencode      swarm/agent-2       🟡 working    "added login endpoint"
agent-3    codex         swarm/agent-3       ⏳ waiting    —
agent-4    aider         swarm/agent-4       ⏳ waiting    —
──────────────────────────────────────────────────────────
1 done · 1 working · 2 waiting · 0 failed

# Real-time dashboard (refreshes every 2 seconds)
$ swarm status --watch

# Machine-readable output for scripting
$ swarm status --json
{
  "project": "my-project",
  "task": "Build a REST API with auth and tests",
  "agents": [
    {
      "name": "agent-1",
      "tool": "claudecode",
      "branch": "swarm/agent-1",
      "status": "done",
      "last_commit": "setup project structure"
    }
  ]
}
```

**Status values:**
- `⏳ waiting` — not yet started
- `🟡 working` — agent process running
- `✅ done` — agent finished, ready to merge
- `❌ failed` — agent process exited with error
- `🔀 merged` — branch merged into main

---

### `swarm merge [options]`

Merge finished agent branches into main.

```bash
# Merge all DONE agents
$ swarm merge
Merging agent-1 (swarm/agent-1) → main ...  ✅ clean
Merging agent-2 (swarm/agent-2) → main ...  ⚠️  conflict in src/user.js
  → Opening conflict resolution ...
  Press Enter when you have resolved and committed...

# Merge a specific agent
$ swarm merge --agent agent-2

# Auto-merge as agents finish (keeps running)
$ swarm merge --auto

# Preview what would be merged without doing it
$ swarm merge --dry-run
Dry run — would merge:
  agent-1 (swarm/agent-1)
  agent-2 (swarm/agent-2)
```

---

### `swarm peek <agent> [options]`

Inspect a branch without switching to it.

```bash
# Show agent info
$ swarm peek agent-2
Agent: agent-2
Tool: opencode
Branch: swarm/agent-2
Worktree: /home/user/my-project/.swarm/agent-2
Status: done
Task: Implement JWT authentication

# Show file tree
$ swarm peek agent-2 --tree
.
├── src/
│   ├── auth.py
│   └── models.py
└── requirements.txt

# Read a specific file
$ swarm peek agent-2 --file src/auth.py
def authenticate_user(token: str) -> dict:
    ...

# Show git log for this branch
$ swarm peek agent-2 --log
a1b2c3d added jwt middleware
e4f5g6h implemented login endpoint
```

---

### `swarm diff <agent>`

Show diff between an agent branch and main.

```bash
$ swarm diff agent-2
diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,45 @@
+import jwt
+from datetime import datetime, timedelta
+
+def create_token(user_id: str) -> str:
+    ...
```

---

### `swarm agent <subcommand>`

Manual agent management.

```bash
# Create a custom agent manually
$ swarm agent create --name "auth-agent" --branch "feature/auth" --tool claudecode
Created agent auth-agent on branch feature/auth

# Assign a task
$ swarm agent assign "auth-agent" "implement JWT login and refresh token"
Assigned task to auth-agent

# List all agents
$ swarm agent list
agent-1: claudecode (done) — Setup project structure
agent-2: opencode (working) — Implement JWT authentication
agent-3: codex (waiting) — Build user CRUD endpoints

# Stop a running agent
$ swarm agent kill "agent-2"
Killed agent-2 (pid 12345)
```

---

### `swarm doctor`

Check system requirements.

```bash
$ swarm doctor
SwarmGit Doctor
─────────────────────────────────────
✅ Git 2.43.0 (worktree supported)
✅ Python 3.11.4
✅ claudecode found at /usr/local/bin/claude
✅ opencode found at /usr/local/bin/opencode
⚠️  codex not found (install: npm install -g @openai/codex)
❌ aider not found (install: pip install aider-chat)
─────────────────────────────────────
2 agents ready · 1 warning · 1 missing
```

---

### `swarm clean [options]`

Remove all worktrees and agent branches.

```bash
# Clean up everything
$ swarm clean
Removed worktree: /home/user/my-project/.swarm/agent-1
Deleted branch: swarm/agent-1
Removed worktree: /home/user/my-project/.swarm/agent-2
Deleted branch: swarm/agent-2
Cleaned up.

# Force remove even if agents are running
$ swarm clean --force

# Remove worktrees but keep branches
$ swarm clean --keep-branches
```

---

## Configuration

SwarmGit is configured via `swarm.yml` at your project root.

```yaml
project: my-project

splitter:
  provider: anthropic           # anthropic | openai | ollama
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
  aider:
    model: gpt-4o
    extra_flags:
      - --yes
      - --no-git

custom_agents:
  mytool:
    command: "mytool run {task}"
    done_signal: "Task complete."
    workdir_flag: "--cwd"
    env:
      API_KEY: "{MYTOOL_API_KEY}"
```

See [`swarm.yml.example`](swarm.yml.example) for the full reference.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        CLI Layer                        │
│   swarm init / run / status / merge / peek / agent      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    Orchestrator                         │
│   - Receives task string                                │
│   - Calls LLM to split into subtasks                    │
│   - Coordinates all modules below                       │
└──┬──────────────┬──────────────┬────────────────────────┘
   │              │              │
   ▼              ▼              ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│ Worktree │ │  Agent  │ │    Merge     │
│ Manager  │ │ Monitor │ │ Coordinator  │
│          │ │         │ │              │
│ add      │ │ spawn   │ │ queue        │
│ remove   │ │ watch   │ │ merge        │
│ list     │ │ signal  │ │ conflict     │
└────┬─────┘ └────┬────┘ └──────┬───────┘
     │            │             │
     ▼            ▼             │
┌─────────────────────┐         │
│   Adapter Layer     │         │
│                     │         │
│  ClaudeCodeAdapter  │         │
│  OpenCodeAdapter    │         │
│  CodexAdapter       │         │
│  AiderAdapter       │         │
│  CustomAdapter      │         │
└─────────────────────┘         │
                                │
┌───────────────────────────────▼─┐
│         Git Layer               │
│   git worktree add/remove/list  │
│   git merge / git log           │
│   git status / git diff         │
└─────────────────────────────────┘
```

### Core Modules

| Module | Responsibility |
|---|---|
| `swarmgit/cli.py` | Click CLI entry point and argument parsing |
| `swarmgit/orchestrator.py` | Main coordination logic, state persistence |
| `swarmgit/config.py` | `swarm.yml` loader and validation |
| `swarmgit/models.py` | Data classes: `AgentRun`, `Worktree`, `SwarmTask` |
| `swarmgit/git/worktree.py` | Native `git worktree` subprocess wrappers |
| `swarmgit/git/merge.py` | Merge coordinator with conflict strategies |
| `swarmgit/monitor/agent_monitor.py` | Threaded agent process launcher and watcher |
| `swarmgit/adapters/` | Agent-specific command builders and done-detection |
| `swarmgit/ui/status.py` | Rich terminal dashboard |

---

## Agent Adapters

SwarmGit uses an adapter pattern to support any AI coding agent. Each adapter implements:

- `build_command()` — Construct the agent's CLI invocation
- `is_done()` — Detect when the agent has finished its task
- `pre_run()` / `post_run()` — Lifecycle hooks for setup and cleanup

### Adding a New Agent Adapter

1. Create `swarmgit/adapters/youragent.py`
2. Extend `BaseAdapter`
3. Implement `build_command()` and `is_done()`
4. Register in `swarmgit/adapters/__init__.py`
5. Add tests in `tests/test_adapters.py`

See the [Contributing Guide](#contributing) for details.

---

## Contributing

We welcome contributions from the AI developer tools community!

```bash
git clone https://github.com/rjben/swarm-git.git
cd swarm-git
pip install -e ".[dev]"

# Run tests
pytest

# Format and lint
black swarmgit/
ruff check swarmgit/

# Type check
mypy swarmgit/
```

### Good First Issues

- [ ] Add Ollama support for local LLM task splitting
- [ ] Add `--follow` support to `swarm agent logs`
- [ ] Build a Docker adapter for containerized agents
- [ ] Add `swarm report` to aggregate agent failures
- [ ] Implement parallel merge strategy (advanced)

---

## Roadmap

| Version | Features |
|---|---|
| **v0.1.0** (MVP) | Core worktree orchestration, 4 built-in adapters, sequential merge |
| **v0.2.0** | LLM task splitting, `swarm task` preview, custom agents |
| **v0.3.0** | `swarm peek`, `swarm diff`, enhanced conflict resolution |
| **v0.4.0** | Parallel merge strategy, agent logs, failure reporting |
| **v1.0.0** | Stable API, plugin ecosystem, CI/CD integrations |

---

## License

MIT License — see [LICENSE](LICENSE)

```
Copyright (c) 2025 SwarmGit Contributors
```

---

## Keywords

AI coding agents, multi-agent orchestration, git worktree, parallel coding, Claude Code, Aider, Codex, OpenCode, developer tools, CLI, Python, open source, Git workflow, AI-assisted development, agent swarm, branch management, merge automation, software development automation

---

<p align="center">
  Built with ❤️ for the AI coding community
</p>
