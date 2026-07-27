# b1CodingTool

**b1CodingTool** is an agent-agnostic development environment manager. It standardizes AI coding assistant workflows by organizing project context and guidelines into installable **modules**, then compiling them into the configuration files each assistant expects (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`).

## How it works

1. **`b1 init`** — scaffolds an `.agents/` directory in your project with a layered `AGENTS.md` hierarchy.
2. **`b1 install <module>`** — installs a module (local path or git URL), injecting its context docs and skills into `.agents/`.
3. **`b1 pair`** — compiles the full `AGENTS.md` hierarchy and writes identical content to `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md`.

> **Note:** `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md` are auto-generated. Edit `AGENTS.md` or `.agents/project/AGENTS.md` instead, then re-run `b1 pair`.

## Installation

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd b1CodingTool
uv sync
```

## Commands

| Command | Description |
|---------|-------------|
| `uv run b1 init [path]` | Bootstrap a project with `.agents/` structure |
| `uv run b1 install <source>` | Install a module (local path or git URL) |
| `uv run b1 pull` | Sync modules from upstream repo |
| `uv run b1 push` | Draft a PR to contribute generalized rules upstream |
| `uv run b1 pair` | Regenerate `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` |
| `uv run b1 dashboard` | Launch the React dashboard on localhost |

## Module system

Modules encapsulate framework- or domain-specific context for your AI agent. Each module is a directory containing a manifest, context guidelines, and optional skills, commands, and hooks.

See the **[Module Authoring Guide](docs/MODULE_GUIDE.md)** for detailed instructions on creating your own modules.

### Directory structure
A typical module directory contains:

```
my-module/
├── b1-module.yaml     # Module manifest (name, version, type, description)
└── context/           # Markdown files compiled into agent context
    ├── best-practices.md
    ├── conventions.md
    └── directory-structure.md
```

**Install from a local path:**
```bash
uv run b1 install ./modules/flutter
```

**Install from a git URL:**
```bash
uv run b1 install https://github.com/org/b1-modules#flutter
```

**Available built-in modules:**

| Module | Type | Description |
|--------|------|-------------|
| `flutter` | development | Coding conventions, best practices, and project structure for Flutter/Dart |
| `django` | development | Best practices, conventions, and directory structure for Django |
| `react-web` | development | React web development guidelines |
| `react-native` | development | React Native guidelines |
| `fastapi` | development | FastAPI guidelines |

## Project structure

```
.agents/
├── AGENTS.md              # Root context: project-agnostic practices
├── project/
│   └── AGENTS.md          # Project-specific context: app logic, tasks, decisions
└── modules/
    └── flutter/          # Installed module files
        └── context/
```

The `ContextCompiler` assembles these in order — root `AGENTS.md` → project `AGENTS.md` → installed module context files — and `b1 pair` writes the result to all agent-specific files.

## Architecture

```
src/b1/
  cli.py               # Typer entry point — registers all commands
  commands/            # One file per CLI command
  core/
    compiler.py        # Compiles AGENTS.md hierarchy into a single string
    translator.py      # Writes compiled string to CLAUDE.md, GEMINI.md, AGENTS.md
    context_manager.py # Scaffolds AGENTS.md files on b1 init
    installer.py       # Copies module files into .agents/modules/
    fetcher.py         # Resolves module source: local path or git clone
    scaffolder.py      # Scaffolds .agents/ directory structure
    schema.py          # Pydantic models: ModuleConfig, SkillConfig
    config.py          # Reads/writes .agents/config.yaml
  server/main.py       # FastAPI server for the React dashboard
dashboard/             # React frontend (Vite + TypeScript)
modules/               # Built-in module library
```

## Development

```bash
uv run pytest                      # Run tests
uv run pytest -m slow              # Include slow real-git/network tests
uv run b1 --help                   # Verify CLI is working
```

## License

MIT
