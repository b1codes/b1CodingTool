# Phase 2 — `b1 rule` / `b1 edge-case` Slash Commands — Design Spec

**Date:** 2026-07-18
**Status:** Approved design
**Parent spec:** `2026-07-16-agent-file-management-design.md` (§6). This is the sub-project that implements the command surface. Phase 1 (the fan-out pipeline) is merged.

---

## 1. Goal

Give users an ergonomic front door to the **eager guardrail tier** built in Phase 1: capturing a recurring-bug rule or a project edge case should be one command that persists the note to the right seed **and** fans it out to every agent's always-loaded context. `b1 rule` is the centerpiece — "record a recurring-bug rule" == "get this into the always-loaded context of all three agents."

## 2. Scope (v1)

- CLI subcommands `b1 rule` and `b1 edge-case` (the real work).
- Cross-agent slash-command **shims** for **Claude** (`.claude/commands/`) and **Antigravity** (`.agents/skills/`). Codex users invoke the CLI directly (Codex custom prompts are deprecated/home-scoped).
- **Out of scope (later):** a Codex Skill shim; Phase 3 drift-safety/reverse-sync.

## 3. Components

### 3.1 `append_note(project_dir, kind, text, scope)` — `src/b1/core/notes.py` (new)
- `kind`: `"rule"` → section `## Guardrails`; `"edge-case"` → section `## Edge cases`.
- `scope`: `"project"` → `.agents/project/AGENTS.md`; `"local"` → `.agents/local/AGENTS.md`.
- Appends `- <text>` under the matching heading, **creating the heading if absent**.
- **Dedup:** if the exact bullet (`- <text>`) already exists in the file, do not append again (return a "already recorded" signal).
- Returns the destination path (for the confirm message).

### 3.2 `run_pair(project_dir, agents)` — extracted from `pair_cmd`
- The **non-interactive** compile→translate core: `pre-pair` hooks → `ContextCompiler.compile()` → `AgentTranslator.generate_files(agents, compiled)` → `post-pair` hooks.
- `pair_cmd` keeps agent resolution (`--sync` / `active_agents` / prompt) and delegates to `run_pair`. The note commands call `run_pair` directly with a resolved agent list — **no interactive agent prompt** fires from a rule capture.

### 3.3 CLI subcommands — `src/b1/commands/rule.py`, `edge_case.py`; registered in `cli.py`
- `b1 rule "<text>" [--scope project|local] [--no-pair]`
  - **Default `--scope project`** (team guardrail).
  - Flow: `append_note(kind="rule", ...)` → unless `--no-pair`, `run_pair(FULL_MATRIX)` → confirm where it landed and that it's now eager in Claude, Codex, and Antigravity.
- `b1 edge-case "<text>" [--scope project|local] [--no-pair]`
  - If `--scope` omitted, **prompt** (local vs project). Otherwise identical flow with `kind="edge-case"`.
- **Auto-pair targets the full matrix** (`["CLAUDE","CODEX","ANTIGRAVITY"]`) so a guardrail lands in every agent regardless of `active_agents`. `--no-pair` skips the fan-out (append only).

### 3.4 Cross-agent shims — generated during `b1 pair` (idempotent)
Written by a shim generator invoked from `AgentTranslator.generate_files` (or a small `core/shims.py`):
- **Claude:** `.claude/commands/b1-rule.md`, `.claude/commands/b1-edge-case.md`. Gitignored via the existing `.claude/` entry.
- **Antigravity:** `.agents/skills/b1-rule.md`, `.agents/skills/b1-edge-case.md`. **Gitignore the specific `b1-*` files** (users own the rest of `.agents/skills/`).
- **Shim content — the "agent formulates" model:** each shim instructs the agent to summarize the recurring behavior / edge case from the current conversation into ONE concise imperative line, then run `b1 rule "<line>"` (adding `--scope local` if it is personal). The agent authors the wording; the CLI persists and fans out.

### 3.5 Seed headings — `src/b1/core/context_manager.py`
Add `## Guardrails` and `## Edge cases` headings to the **project** seed template (`PROJECT_AGENT_MD`) — today only the local seed has them — so project-scoped appends have a stable home.

## 4. Files to touch
- New: `src/b1/core/notes.py`, `src/b1/core/shims.py` (or fold shims into `translator.py`), `src/b1/commands/rule.py`, `src/b1/commands/edge_case.py`.
- Modify: `src/b1/commands/pair.py` (extract `run_pair`), `src/b1/cli.py` (register commands), `src/b1/core/translator.py` (call shim generator + gitignore the `b1-*` skills), `src/b1/core/context_manager.py` (project-seed headings), `src/b1/core/scaffolder.py` (gitignore `.agents/skills/b1-*.md`).

## 5. Decisions (locked)
- Auto-pair after append → **full matrix**; `--no-pair` to skip.
- `b1 rule` default scope **project**; `b1 edge-case` **prompts** when scope omitted.
- **Dedup** exact-duplicate bullets.
- Shims are **gitignored generated artifacts**, regenerated each `b1 pair`.

## 6. Non-goals / follow-ups
- Codex slash shim (Skill-based) — deferred.
- Phase 3: drift snapshots + `/b1-reconcile` reverse sync (separate spec/plan).
- Editing/removing existing notes via CLI (v1 is append-only).
