# b1CodingTool - Project Specification (`SPEC.md`)

## 1. Project Overview
**b1CodingTool** is an agent-agnostic development environment manager designed to standardize, modularize, and enhance the workflows of AI coding assistants (e.g., Gemini CLI, Claude Code, Codex). 

The system provides a CLI tool and a localized React dashboard to manage agent context, skill integrations, and project-specific tooling. By organizing knowledge into "modules" (cross-cutting, framework-specific, and deployment-specific), the tool ensures agents have highly contextualized guidelines, `/` commands, and capabilities without overwhelming their context windows.

## 2. Core Architecture

### 2.1 Tech Stack
* **CLI Framework:** Python with **Typer** (for type-hinted command routing) and **Rich** (for formatted terminal UI, progress bars, and markdown rendering).
* **Dependency Management & Packaging:** `uv`
* **Dashboard Frontend:** React (served on a localhost port)
* **License:** MIT

### 2.2 System Components
1.  **The CLI Tool:** The primary interface for scaffolding, module management, and context synchronization, utilizing Typer for its command structure.
2.  **The Module Registry:** A curated collection of guidelines, skills (including community skills from *skillsmp.com*), and hooks.
3.  **The React Dashboard:** A local web UI for visualizing installed modules, managing API keys, monitoring agent usage sessions, and exploring available skills.
4.  **Context Manager (`AGENTS.md` system):** A hierarchical file management system that structures instructions for the AI agent, mapping standardized data to agent-specific formats.

---

## 3. Module System
Modules encapsulate framework-specific or domain-specific context and agent tooling. They are categorized as follows:

* **Cross-Cutting Modules:** General full-stack development guidelines, software engineering best practices, and project management notes.
* **Development Modules:** Framework-specific guidelines, skills, and commands (e.g., React, Flutter, Django, FastAPI).
* **Deployment Modules:** Cloud infrastructure and deployment targets (e.g., AWS, Apple App Store), providing the agent with the necessary scripts and documentation to assist in deployment.

**Module Anatomy:**
Each module contains:
* `skills/`: Reusable agent tasks or functions.
* `commands/`: Custom slash commands (e.g., `/setup-flutter-bloc`).
* `hooks/`: Scripts executed before/after specific agent actions.
* `context/`: Markdown files injected into the agent's knowledge base.

---

## 4. CLI Feature Specifications

The Python CLI (managed via `uv`, built with Typer and Rich) will support the following primary commands. All terminal outputs, statuses, and warnings should be beautifully rendered using Rich.

### `b1 init`
* **Purpose:** Bootstraps a new or existing project with the `b1CodingTool` architecture.
* **Behavior:**
    * Scaffolds the `.agents/` and `docs/` directories at the project root.
    * Generates a standardized `.gitignore` and `README.md` if they do not exist.
    * Establishes the hierarchical context structure:
        * **Root `AGENTS.md`:** Project-agnostic software development practices and general notes.
        * **Project-Specific `project/AGENTS.md`:** App logic, directory structures, and active tasks.
    * *Constraint:* Must safely merge or append to existing `AGENTS.md` files in pre-existing projects without destroying current data.

### `b1 install <module-name>`
* **Purpose:** Equips the current project workspace with a specific development or deployment module.
* **Behavior:**
    * Downloads the specified module's skills, commands, and context.
    * Runs any post-install scripts required to set up the project environment for that module.
    * Updates the local configuration to reflect the installed tools, which syncs with the React dashboard.
    * Displays a Rich progress bar during module fetching and installation.

### `b1 pull`
* **Purpose:** Syncs local modules with the upstream version control.
* **Behavior:** Fetches and applies any updated module files, skills, or generalized guidelines to keep the local agent context up to date.

### `b1 push`
* **Purpose:** Contributes generalized learnings back to the central repository.
* **Behavior:** * Scans the project-specific agent files for any new, universally applicable cross-cutting rules or skills.
    * Automatically drafts a Pull Request to the central version control system, allowing the user to share project-agnostic guidelines with all other projects.

### `b1 pair`
* **Purpose:** Ensures cross-agent parity across the workspace.
* **Behavior:** Reads the primary `AGENTS.md` context files and translates/updates them into agent-specific configuration files (e.g., `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`). This guarantees that regardless of which assistant is being utilized, the core instructions and context remain uniform.

---

## 5. React Dashboard Specifications
* **Launch Mechanism:** Bootstrapped via the Python CLI (e.g., `b1 dashboard`) running on a local port.
* **Core Views:**
    * **Module Explorer:** UI to browse, install, and uninstall Development/Deployment modules.
    * **Skill Inspector:** View details of active skills (both curated and from *skillsmp.com*) and custom agent commands.
    * **Resource Manager:** Input and securely store API keys required by the agents.
    * **Telemetry/Session Monitor:** Track agent usage, session limits, and token/API consumption.

---

## 6. Implementation Milestones (For the Agent)

1.  **Phase 1: CLI Foundation & Context Management**
    * Initialize the Python project using `uv`.
    * Install **Typer** and **Rich** as core dependencies.
    * Implement the `b1 init` logic for new and existing directories using Typer commands.
    * Establish the safe creation/merging of `.agents/`, `docs/`, and the layered `AGENTS.md` files.
2.  **Phase 2: Module System & Sourcing**
    * Define the JSON/YAML schema for what constitutes a "Module".
    * Implement the `b1 install` command to fetch and mount a module into the `.agents/` directory, using Rich for UI feedback.
    * Implement the connection to *skillsmp.com* to parse and inject community skills.
3.  **Phase 3: Version Control Syncing**
    * Implement `b1 pull` to update module definitions.
    * Implement `b1 push` utilizing a git library to automate PR creation for generalized rules.
4.  **Phase 4: Cross-Agent Parity Management**
    * Implement the `b1 pair` command.
    * Develop the parsing and translation logic to update all agent-specific files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) from the root `AGENTS.md` guidelines.
5.  **Phase 5: Dashboard Integration**
    * Scaffold the React frontend.
    * Build a local FastAPI or standard Python HTTP server within the CLI to serve data (installed modules, API usage) to the React frontend.
6.  **Phase 6: Model Context Protocol (MCP) Integration**
    * Standardize agent interaction via the official `mcp` SDK.
    * Implement an MCP server in `src/b1/server/mcp_server.py`.
    * Map core `b1` tools and context resources to MCP protocols for dynamic, two-way agent communication.
