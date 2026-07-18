# Phase 2 — Slash Commands (`b1 rule` / `b1 edge-case`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `b1 rule` and `b1 edge-case` CLI commands that append a note to the correct `.agents/` seed and fan it out to every agent's eager context, plus Claude/Antigravity slash-command shims.

**Architecture:** A pure `append_note` persistence helper + a non-interactive `run_pair` core (extracted from `pair_cmd`) compose into two thin Typer commands. `b1 pair` also emits static slash-command shim files that delegate to these CLI commands.

**Tech Stack:** Python 3.12, Typer, Rich, pytest, `uv`.

## Global Constraints

- Run all Python commands from `b1CodingTool/` using `uv` only. Tests: `uv run pytest`.
- `kind` → heading: `"rule"` → `## Guardrails`; `"edge-case"` → `## Edge cases`.
- `scope` → file: `"project"` → `.agents/project/AGENTS.md`; `"local"` → `.agents/local/AGENTS.md`.
- `b1 rule` default `--scope project`. `b1 edge-case` **prompts** for scope when `--scope` is omitted.
- Auto-pair after append targets the **full matrix** `["CLAUDE","CODEX","ANTIGRAVITY"]`; `--no-pair` skips it.
- Append is **deduplicated**: an exact-duplicate `- <text>` bullet is not appended again.
- Shims are **gitignored** generated artifacts: `.claude/commands/b1-*.md` (via existing `.claude/`) and `.agents/skills/b1-*.md`.

---

## File Structure

**New files:**
- `src/b1/core/notes.py` — `append_note()` persistence helper.
- `src/b1/core/shims.py` — `write_agent_shims()` generator for Claude/Antigravity slash-command shims.
- `src/b1/commands/rule.py` — `rule_cmd`.
- `src/b1/commands/edge_case.py` — `edge_case_cmd`.
- Tests: `tests/unit/test_notes.py`, `tests/unit/test_shims.py`, `tests/integration/test_rule_cmd.py`, `tests/integration/test_edge_case_cmd.py`.

**Modified files:**
- `src/b1/commands/pair.py` — extract `run_pair(project_dir, agents, config=None)`; `pair_cmd` delegates to it.
- `src/b1/cli.py` — register `rule` and `edge-case` commands.
- `src/b1/core/translator.py` — call `write_agent_shims()` from `generate_files`; add the two `.agents/skills/b1-*.md` gitignore entries; remove the stale "added in Task 5" comment.
- `src/b1/core/context_manager.py` — add `## Guardrails` / `## Edge cases` headings to `PROJECT_AGENT_MD`.
- `src/b1/core/scaffolder.py` — add `.agents/skills/b1-*.md` to `GITIGNORE_CONTENT`.

---

### Task 1: `append_note` persistence helper + project-seed headings

**Files:**
- Create: `src/b1/core/notes.py`
- Modify: `src/b1/core/context_manager.py:6-15` (`PROJECT_AGENT_MD`)
- Test: `tests/unit/test_notes.py`, `tests/unit/test_context_manager.py` (add one assertion)

**Interfaces:**
- Produces: `append_note(project_dir: Path, kind: str, text: str, scope: str) -> tuple[Path, bool]`. Returns `(destination_path, appended)` where `appended` is `False` when the exact bullet already existed. `kind` ∈ {`"rule"`,`"edge-case"`}; `scope` ∈ {`"project"`,`"local"`}.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_notes.py
from pathlib import Path
from b1.core.notes import append_note


def _seed(project, scope):
    return project / ".agents" / scope / "AGENTS.md"


def _mk(tmp_path):
    for scope in ("project", "local"):
        (tmp_path / ".agents" / scope).mkdir(parents=True, exist_ok=True)
        _seed(tmp_path, scope).write_text("# Seed\n\n## Guardrails\n\n## Edge cases\n", encoding="utf-8")
    return tmp_path


def test_rule_appends_under_guardrails_in_project(tmp_path):
    _mk(tmp_path)
    dest, appended = append_note(tmp_path, "rule", "Never call prod API in tests", "project")
    assert appended is True
    assert dest == _seed(tmp_path, "project")
    body = dest.read_text(encoding="utf-8")
    assert "## Guardrails\n- Never call prod API in tests" in body


def test_edge_case_appends_under_edge_cases_in_local(tmp_path):
    _mk(tmp_path)
    dest, appended = append_note(tmp_path, "edge-case", "Redis must be running", "local")
    assert dest == _seed(tmp_path, "local")
    assert "## Edge cases\n- Redis must be running" in dest.read_text(encoding="utf-8")


def test_creates_heading_when_missing(tmp_path):
    (tmp_path / ".agents" / "project").mkdir(parents=True)
    _seed(tmp_path, "project").write_text("# Seed\n", encoding="utf-8")
    append_note(tmp_path, "rule", "Use 2-space indent", "project")
    assert "## Guardrails\n- Use 2-space indent" in _seed(tmp_path, "project").read_text(encoding="utf-8")


def test_dedup_exact_duplicate(tmp_path):
    _mk(tmp_path)
    append_note(tmp_path, "rule", "No force push", "project")
    dest, appended = append_note(tmp_path, "rule", "No force push", "project")
    assert appended is False
    assert dest.read_text(encoding="utf-8").count("- No force push") == 1
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/unit/test_notes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b1.core.notes'`

- [ ] **Step 3: Implement `append_note`**

```python
# src/b1/core/notes.py
from pathlib import Path

_HEADINGS = {"rule": "## Guardrails", "edge-case": "## Edge cases"}
_FILES = {"project": ("project", "AGENTS.md"), "local": ("local", "AGENTS.md")}


def append_note(project_dir: Path, kind: str, text: str, scope: str) -> tuple[Path, bool]:
    """Append a bullet under the section for `kind` in the seed for `scope`.

    Returns (destination_path, appended). `appended` is False if the exact
    bullet already existed (dedup). Creates the heading if missing.
    """
    if kind not in _HEADINGS:
        raise ValueError(f"Unknown kind: {kind!r}")
    if scope not in _FILES:
        raise ValueError(f"Unknown scope: {scope!r}")

    heading = _HEADINGS[kind]
    sub, name = _FILES[scope]
    dest = project_dir / ".agents" / sub / name
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = dest.read_text(encoding="utf-8") if dest.exists() else ""
    bullet = f"- {text.strip()}"

    lines = content.splitlines()
    if bullet in lines:
        return dest, False

    if heading in lines:
        idx = lines.index(heading)
        # insert the bullet on the line directly after the heading (newest-first)
        lines.insert(idx + 1, bullet)
        new_content = "\n".join(lines) + "\n"
    else:
        prefix = content.rstrip("\n")
        joiner = "\n\n" if prefix else ""
        new_content = f"{prefix}{joiner}{heading}\n{bullet}\n"

    dest.write_text(new_content, encoding="utf-8")
    return dest, True
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/unit/test_notes.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Add project-seed headings**

In `src/b1/core/context_manager.py`, replace `PROJECT_AGENT_MD` (lines 6-15) with:

```python
PROJECT_AGENT_MD = """# b1CodingTool: Project Context
This is the project-specific `AGENTS.md` context file.
It contains app logic, directory structures, and active tasks.

## Architecture Notes
- Follow the guidelines specified in the root `AGENTS.md`.

## Guardrails

## Edge cases
"""
```

Add to `tests/unit/test_context_manager.py`:

```python
def test_project_seed_has_note_headings(tmp_path):
    from b1.core.context_manager import setup_context
    (tmp_path / ".agents").mkdir()
    setup_context(tmp_path)
    seed = (tmp_path / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Guardrails" in seed and "## Edge cases" in seed
```

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/unit/test_notes.py tests/unit/test_context_manager.py -v`
Expected: PASS. If a pre-existing `test_context_manager` test asserted the old `## Active Tasks` heading in the project seed, update it (that heading was removed).

- [ ] **Step 7: Commit**

```bash
git add src/b1/core/notes.py src/b1/core/context_manager.py tests/unit/test_notes.py tests/unit/test_context_manager.py
git commit -m "feat(notes): add append_note helper and project-seed note headings"
```

---

### Task 2: Extract `run_pair` from `pair_cmd`

**Files:**
- Modify: `src/b1/commands/pair.py`
- Test: `tests/integration/test_pair_cmd.py` (add one), existing pair tests must still pass.

**Interfaces:**
- Produces: `run_pair(project_dir: Path, agents: list[str], config: Optional[B1Config] = None) -> bool`. Runs pre-pair hook → compile → (return `False` if `compiled.is_empty()`) → `generate_files(agents, compiled)` → post-pair hook → return `True`. No prompts, no printing of the agent-resolution flow.
- Consumes: nothing new. `pair_cmd` keeps its signature and now delegates to `run_pair`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_pair_cmd.py  (append)
def test_run_pair_generates_without_prompting(make_project):
    from b1.commands.pair import run_pair
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule one", encoding="utf-8")
    ok = run_pair(project, ["CLAUDE", "CODEX", "ANTIGRAVITY"])
    assert ok is True
    assert (project / "AGENTS.md").exists()
    assert (project / "CLAUDE.md").exists()


def test_run_pair_returns_false_when_empty(tmp_path):
    from b1.commands.pair import run_pair
    (tmp_path / ".agents").mkdir()
    assert run_pair(tmp_path, ["CLAUDE"]) is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/integration/test_pair_cmd.py::test_run_pair_generates_without_prompting -v`
Expected: FAIL with `ImportError: cannot import name 'run_pair'`

- [ ] **Step 3: Refactor `pair.py`**

Replace the body of `src/b1/commands/pair.py` from the `console = Console()` line down with:

```python
console = Console()

FULL_MATRIX = ["CLAUDE", "CODEX", "ANTIGRAVITY"]


def run_pair(project_dir: Path, agents: list[str], config: Optional[B1Config] = None) -> bool:
    """Non-interactive compile -> translate core. Returns True if files were generated,
    False if there was no context to compile. No prompts, no agent-resolution."""
    if config is None:
        config = B1Config.load(project_dir)
    hook_engine = HookEngine(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)

    hook_engine.run_hooks("pre-pair")
    compiled = compiler.compile()
    if compiled.is_empty():
        return False
    translator.generate_files(agents, compiled)
    hook_engine.run_hooks("post-pair")
    return True


def pair_cmd(
    sync: Annotated[bool, typer.Option("--sync", help="Regenerate the full agent matrix (Claude, Codex, Antigravity) regardless of active_agents.")] = False,
):
    """Compile the .agents/ sources into each agent's native files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    config = B1Config.load(project_dir)

    if sync:
        agents = FULL_MATRIX
    else:
        if not config.active_agents:
            agent_input = typer.prompt(
                "Which agents do you want to target? (comma separated: CLAUDE,CODEX,ANTIGRAVITY)",
                default="CLAUDE,CODEX,ANTIGRAVITY",
            )
            agents = [a.strip().upper() for a in agent_input.split(",") if a.strip()]
            config.active_agents = agents
            config.save(project_dir)
        else:
            agents = config.active_agents

    console.print("[bold blue]Compiling contexts...[/bold blue]")
    if not run_pair(project_dir, agents, config=config):
        console.print("[yellow]No context found to compile.[/yellow]")
        return
    console.print(f"[blue]Writing configurations for:[/blue] {', '.join(agents)}")
    console.print("\n[bold green]Cross-agent parity synchronization complete![/bold green] \U0001f504")
```

Add `Optional` to the typing import at the top: change `from typing import Annotated` to `from typing import Annotated, Optional`.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/integration/test_pair_cmd.py -v`
Expected: PASS (existing pair tests + the 2 new ones). The observable `pair` behavior is unchanged.

- [ ] **Step 5: Commit**

```bash
git add src/b1/commands/pair.py tests/integration/test_pair_cmd.py
git commit -m "refactor(pair): extract non-interactive run_pair core"
```

---

### Task 3: `b1 rule` and `b1 edge-case` commands

**Files:**
- Create: `src/b1/commands/rule.py`, `src/b1/commands/edge_case.py`
- Modify: `src/b1/cli.py`
- Test: `tests/integration/test_rule_cmd.py`, `tests/integration/test_edge_case_cmd.py`

**Interfaces:**
- Consumes: `append_note` (Task 1); `run_pair`, `FULL_MATRIX` (Task 2).
- Produces: `rule_cmd(text, scope, no_pair)` and `edge_case_cmd(text, scope, no_pair)`; CLI names `rule` and `edge-case`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/integration/test_rule_cmd.py
import os
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def _run(project, args, **kw):
    cwd = os.getcwd()
    os.chdir(project)
    try:
        return runner.invoke(app, args, **kw)
    finally:
        os.chdir(cwd)


def test_rule_appends_to_project_and_pairs(make_project):
    project = make_project(agents=["CLAUDE"])
    result = _run(project, ["rule", "Never call prod API in tests"])
    assert result.exit_code == 0
    seed = (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "- Never call prod API in tests" in seed
    # fanned out to the committed root AGENTS.md (eager, shared)
    assert "Never call prod API in tests" in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_rule_local_scope_goes_to_local_seed(make_project):
    project = make_project(agents=["CLAUDE"])
    result = _run(project, ["rule", "My sandbox is localhost:9000", "--scope", "local"])
    assert result.exit_code == 0
    assert "- My sandbox is localhost:9000" in (project / ".agents" / "local" / "AGENTS.md").read_text(encoding="utf-8")
    # personal content must NOT reach the committed root AGENTS.md
    assert "localhost:9000" not in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_rule_no_pair_appends_without_generating(make_project):
    project = make_project(agents=["CLAUDE"])
    # remove any AGENTS.md the fixture created so we can prove --no-pair didn't regenerate it
    (project / "AGENTS.md").unlink(missing_ok=True)
    result = _run(project, ["rule", "Skip the fan-out", "--no-pair"])
    assert result.exit_code == 0
    assert "- Skip the fan-out" in (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert not (project / "AGENTS.md").exists()
```

```python
# tests/integration/test_edge_case_cmd.py
import os
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def _run(project, args, **kw):
    cwd = os.getcwd()
    os.chdir(project)
    try:
        return runner.invoke(app, args, **kw)
    finally:
        os.chdir(cwd)


def test_edge_case_explicit_scope(make_project):
    project = make_project(agents=["CLAUDE"])
    result = _run(project, ["edge-case", "Redis must be running", "--scope", "project"])
    assert result.exit_code == 0
    seed = (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Edge cases" in seed and "- Redis must be running" in seed


def test_edge_case_prompts_for_scope_when_omitted(make_project):
    project = make_project(agents=["CLAUDE"])
    # answer the scope prompt with "local"
    result = _run(project, ["edge-case", "Flaky on ARM"], input="local\n")
    assert result.exit_code == 0
    assert "- Flaky on ARM" in (project / ".agents" / "local" / "AGENTS.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/integration/test_rule_cmd.py tests/integration/test_edge_case_cmd.py -v`
Expected: FAIL — `No such command 'rule'` / `'edge-case'`.

- [ ] **Step 3: Implement the commands**

```python
# src/b1/commands/rule.py
import typer
from typing import Optional, Annotated
from pathlib import Path
from rich.console import Console

from b1.core.notes import append_note
from b1.commands.pair import run_pair, FULL_MATRIX

console = Console()


def rule_cmd(
    text: Annotated[str, typer.Argument(help="The recurring-bug rule to record.")],
    scope: Annotated[str, typer.Option("--scope", help="project (team) or local (personal).")] = "project",
    no_pair: Annotated[bool, typer.Option("--no-pair", help="Append only; don't regenerate agent files.")] = False,
):
    """Record a recurring-bug/behavior guardrail and fan it out to every agent."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)
    if scope not in ("project", "local"):
        console.print("[bold red]--scope must be 'project' or 'local'.[/bold red]")
        raise typer.Exit(1)

    dest, appended = append_note(project_dir, "rule", text, scope)
    rel = dest.relative_to(project_dir)
    if not appended:
        console.print(f"[yellow]Already recorded in {rel}; nothing to do.[/yellow]")
        return
    console.print(f"[green]✔ Recorded guardrail in[/green] {rel}")
    if not no_pair:
        run_pair(project_dir, FULL_MATRIX)
        console.print("[green]Now loaded for every agent (Claude, Codex, Antigravity).[/green]")
```

```python
# src/b1/commands/edge_case.py
import typer
from typing import Optional, Annotated
from pathlib import Path
from rich.console import Console

from b1.core.notes import append_note
from b1.commands.pair import run_pair, FULL_MATRIX

console = Console()


def edge_case_cmd(
    text: Annotated[str, typer.Argument(help="The project-specific edge case to record.")],
    scope: Annotated[Optional[str], typer.Option("--scope", help="project (team) or local (personal).")] = None,
    no_pair: Annotated[bool, typer.Option("--no-pair", help="Append only; don't regenerate agent files.")] = False,
):
    """Record a project-specific edge case and fan it out to every agent."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    if scope is None:
        scope = typer.prompt("Scope? (project = team, local = personal)", default="project")
    if scope not in ("project", "local"):
        console.print("[bold red]--scope must be 'project' or 'local'.[/bold red]")
        raise typer.Exit(1)

    dest, appended = append_note(project_dir, "edge-case", text, scope)
    rel = dest.relative_to(project_dir)
    if not appended:
        console.print(f"[yellow]Already recorded in {rel}; nothing to do.[/yellow]")
        return
    console.print(f"[green]✔ Recorded edge case in[/green] {rel}")
    if not no_pair:
        run_pair(project_dir, FULL_MATRIX)
        console.print("[green]Now loaded for every agent (Claude, Codex, Antigravity).[/green]")
```

Register in `src/b1/cli.py`: add imports after the other command imports —

```python
from b1.commands.rule import rule_cmd
from b1.commands.edge_case import edge_case_cmd
```

and register after `app.command(name="pair")(pair_cmd)` —

```python
app.command(name="rule")(rule_cmd)
app.command(name="edge-case")(edge_case_cmd)
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/integration/test_rule_cmd.py tests/integration/test_edge_case_cmd.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b1/commands/rule.py src/b1/commands/edge_case.py src/b1/cli.py tests/integration/test_rule_cmd.py tests/integration/test_edge_case_cmd.py
git commit -m "feat(cli): add b1 rule and b1 edge-case commands"
```

---

### Task 4: Cross-agent slash-command shims

**Files:**
- Create: `src/b1/core/shims.py`
- Modify: `src/b1/core/translator.py` (call `write_agent_shims`; gitignore entries; remove stale comment), `src/b1/core/scaffolder.py` (gitignore entry)
- Test: `tests/unit/test_shims.py`

**Interfaces:**
- Consumes: called from `AgentTranslator.generate_files`.
- Produces: `write_agent_shims(project_dir: Path) -> None` — writes `.claude/commands/b1-rule.md`, `.claude/commands/b1-edge-case.md`, `.agents/skills/b1-rule.md`, `.agents/skills/b1-edge-case.md` (idempotent).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_shims.py
from b1.core.shims import write_agent_shims


def test_writes_claude_and_antigravity_shims(tmp_path):
    write_agent_shims(tmp_path)
    for p in [
        ".claude/commands/b1-rule.md",
        ".claude/commands/b1-edge-case.md",
        ".agents/skills/b1-rule.md",
        ".agents/skills/b1-edge-case.md",
    ]:
        f = tmp_path / p
        assert f.exists(), p
        body = f.read_text(encoding="utf-8")
        assert "b1 rule" in body or "b1 edge-case" in body   # delegates to the CLI


def test_shims_are_idempotent(tmp_path):
    write_agent_shims(tmp_path)
    write_agent_shims(tmp_path)  # must not raise or duplicate
    assert (tmp_path / ".claude" / "commands" / "b1-rule.md").exists()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/unit/test_shims.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b1.core.shims'`

- [ ] **Step 3: Implement `write_agent_shims`**

```python
# src/b1/core/shims.py
from pathlib import Path

_RULE_BODY = """Summarize the recurring bug or behavior we should avoid in future \
sessions as ONE concise, imperative rule (for example: "Never call the production \
API from tests").

Then record it by running:

    b1 rule "<the rule>"

Add `--scope local` if the rule is personal to me rather than the whole team. \
After it runs, confirm where it was saved and that it is now loaded for every agent.
"""

_EDGE_BODY = """Summarize the project-specific edge case or gotcha we just hit as ONE \
concise line (for example: "The integration tests require a local Redis instance").

Then record it by running:

    b1 edge-case "<the edge case>"

You will be asked whether it is a team (project) or personal (local) note if you do \
not pass `--scope`. After it runs, confirm where it was saved.
"""

_SHIMS = {
    "b1-rule.md": _RULE_BODY,
    "b1-edge-case.md": _EDGE_BODY,
}


def write_agent_shims(project_dir: Path) -> None:
    """Write idempotent slash-command shims for Claude (.claude/commands/) and
    Antigravity (.agents/skills/). Each shim tells the agent to summarize the note
    and invoke the corresponding b1 CLI command."""
    targets = [
        project_dir / ".claude" / "commands",
        project_dir / ".agents" / "skills",
    ]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)
        for name, body in _SHIMS.items():
            (target / name).write_text(body, encoding="utf-8")
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/unit/test_shims.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Wire into `generate_files` + gitignore**

In `src/b1/core/translator.py`:

Add the import at the top (with the other imports):
```python
from b1.core.shims import write_agent_shims
```

In `generate_files`, replace the stale comment line `# Codex + Antigravity renderers are added in Task 5.` with nothing, and add a shim call before `self._ensure_gitignore()`:

```python
        write_agent_shims(self.project_dir)
        self._ensure_gitignore()
```

In `_ensure_gitignore`, extend the `entries` list to include the Antigravity shims:
```python
        entries = ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.override.md",
                   ".claude/", ".agents/local/", ".agents/rules/local.md",
                   ".agents/skills/b1-rule.md", ".agents/skills/b1-edge-case.md"]
```

In `src/b1/core/scaffolder.py`, add the same two lines to `GITIGNORE_CONTENT` after `.agents/rules/local.md`:
```
.agents/skills/b1-rule.md
.agents/skills/b1-edge-case.md
```

- [ ] **Step 6: Run the suite**

Run: `uv run pytest -q`
Expected: PASS — 0 failures. (Pair/translator tests now also emit shims; confirm none assert on an exact set of generated files that would exclude the new shim dirs — if one does, update it to allow them.)

- [ ] **Step 7: Commit**

```bash
git add src/b1/core/shims.py src/b1/core/translator.py src/b1/core/scaffolder.py tests/unit/test_shims.py
git commit -m "feat(shims): generate Claude/Antigravity slash-command shims during pair"
```

---

## Self-Review

**Spec coverage:**
- §3.1 `append_note` (headings, create-if-missing, dedup) → Task 1. ✅
- §3.2 `run_pair` extraction → Task 2. ✅
- §3.3 `b1 rule` (default project) / `b1 edge-case` (prompt), full-matrix auto-pair, `--no-pair` → Task 3. ✅
- §3.4 Claude + Antigravity shims, gitignored, "agent formulates" content → Task 4. ✅
- §3.5 project-seed headings → Task 1. ✅
- Gitignore entries (`.agents/skills/b1-*.md`) → Task 4. ✅

**Placeholder scan:** none.

**Type consistency:** `append_note(...) -> tuple[Path, bool]` (Task 1) consumed by Task 3; `run_pair(project_dir, agents, config=None) -> bool` and `FULL_MATRIX` (Task 2) consumed by Task 3; `write_agent_shims(project_dir)` (Task 4) consumed by `generate_files`. Names consistent across tasks.
