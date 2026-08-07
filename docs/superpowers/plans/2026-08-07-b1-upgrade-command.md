# b1 upgrade Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `b1 upgrade [path]` command that backfills an existing project's `.agents/` scaffolding (e.g. a missing `.agents/local/AGENTS.md`) to match what the current b1CodingTool version expects, without disturbing existing content.

**Architecture:** `upgrade_cmd` guards on `.agents/` already existing (unlike `b1 init`, it does not bootstrap a project from nothing), then delegates all backfill logic to the existing, already-idempotent `setup_context()` from `b1.core.context_manager` — no new backfill logic is written. It finishes by offering the same "Re-pair now to apply updates?" confirmation `b1 pull` uses, so newly-backfilled seed content gets compiled.

**Tech Stack:** Python 3.12+, Typer (CLI), Click (`click.Abort` prompt handling), Rich (console output), pytest + `typer.testing.CliRunner` (tests).

## Global Constraints

- Reuse `b1.core.context_manager.setup_context` unchanged — do not duplicate or reimplement its backfill/migration logic in the new command.
- `b1 upgrade` touches only `.agents/` scaffolding. It must not create `docs/`, `README.md`, or `.gitignore` the way `b1 init`'s `scaffold_project()` does.
- `b1 upgrade` must error out (via `ProjectError`) if `.agents/` does not already exist at the target path, rather than bootstrapping one.
- Command name is `upgrade`, not `sync` — `pair --sync` already means something unrelated (regenerate the full agent matrix), so the vocabulary is reserved.
- Follow existing sibling-command conventions exactly: error handling shape from `src/b1/commands/pull.py`, path-argument shape from `src/b1/commands/init.py`, re-pair confirm/`click.Abort` handling from `src/b1/commands/pull.py`.

---

### Task 1: `upgrade_cmd` core — guard, backfill, CLI registration

**Files:**
- Create: `src/b1/commands/upgrade.py`
- Modify: `src/b1/cli.py` (add import + registration, alongside the existing `init`/`pull` registrations)
- Test: `tests/integration/test_upgrade_cmd.py`

**Interfaces:**
- Consumes: `b1.core.exceptions.ProjectError(message: str, suggestions: Optional[List[str]] = None)` (existing); `b1.core.context_manager.setup_context(root_dir: Path) -> None` (existing, already idempotent — see `src/b1/core/context_manager.py`).
- Produces: `upgrade_cmd(path: Optional[Path] = None) -> None` in `src/b1/commands/upgrade.py`, registered in `src/b1/cli.py` as `app.command(name="upgrade")(upgrade_cmd)`. Task 2 imports this same function to extend it — it does not create a second entry point.

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/test_upgrade_cmd.py`:

```python
# tests/integration/test_upgrade_cmd.py
from typer.testing import CliRunner
from b1.cli import app
from b1.core.exceptions import ProjectError

runner = CliRunner()


def test_upgrade_errors_when_agents_dir_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ProjectError)


def test_upgrade_backfills_missing_local_seed_without_touching_project_seed(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    project_seed = project / ".agents" / "project" / "AGENTS.md"
    original_content = project_seed.read_text(encoding="utf-8")

    result = runner.invoke(app, ["upgrade"])

    assert result.exit_code == 0
    assert (project / ".agents" / "local" / "AGENTS.md").exists()
    assert project_seed.read_text(encoding="utf-8") == original_content


def test_upgrade_does_not_create_init_only_scaffolding(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    runner.invoke(app, ["upgrade"])
    assert not (project / "docs").exists()
    assert not (project / "README.md").exists()
    assert not (project / ".gitignore").exists()


def test_upgrade_with_path_argument_targets_that_directory(make_project, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = make_project()
    result = runner.invoke(app, ["upgrade", str(project)])
    assert result.exit_code == 0
    assert (project / ".agents" / "local" / "AGENTS.md").exists()


def test_upgrade_is_idempotent(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    runner.invoke(app, ["upgrade"])
    local_seed = project / ".agents" / "local" / "AGENTS.md"
    local_seed.write_text("custom local notes", encoding="utf-8")
    runner.invoke(app, ["upgrade"])
    assert local_seed.read_text(encoding="utf-8") == "custom local notes"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_upgrade_cmd.py -v`
Expected: FAIL — `No such command 'upgrade'` (Typer/Click usage error) for every test, since neither `src/b1/commands/upgrade.py` nor the CLI registration exist yet.

- [ ] **Step 3: Implement `upgrade_cmd`**

Create `src/b1/commands/upgrade.py`:

```python
import typer
from typing import Optional, Annotated
from pathlib import Path
from rich.console import Console

from b1.core.exceptions import ProjectError
from b1.core.context_manager import setup_context

console = Console()


def upgrade_cmd(
    path: Annotated[Optional[Path], typer.Argument(help="The project directory to upgrade (default: current directory)")] = None,
):
    """
    Backfills an existing project's .agents/ scaffolding (e.g. a missing
    .agents/local/AGENTS.md) to match what the current b1CodingTool version
    expects, without touching existing content.
    """
    project_dir = (path or Path.cwd()).resolve()

    if not (project_dir / ".agents").exists():
        raise ProjectError(
            "Not a b1CodingTool project.",
            suggestions=[
                "Run `b1 init` to bootstrap the project structure.",
                "Ensure you are in the project root directory.",
            ],
        )

    setup_context(project_dir)

    console.print("[bold green]Upgrade complete![/bold green]")
```

- [ ] **Step 4: Register the command in the CLI**

Modify `src/b1/cli.py`:

```python
from b1.commands.pull import pull_cmd
from b1.commands.upgrade import upgrade_cmd
```

(add the `upgrade_cmd` import line directly after the existing `pull_cmd` import), and:

```python
app.command(name="pull")(pull_cmd)
app.command(name="upgrade")(upgrade_cmd)
```

(add the `upgrade` registration line directly after the existing `pull` registration).

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_upgrade_cmd.py -v`
Expected: PASS (all 5 tests).

- [ ] **Step 6: Run full test suite to check for regressions**

Run: `uv run pytest`
Expected: PASS, no regressions in `test_init_cmd.py`, `test_pull_cmd.py`, `test_context_manager.py`, or elsewhere.

- [ ] **Step 7: Commit**

```bash
git add src/b1/commands/upgrade.py src/b1/cli.py tests/integration/test_upgrade_cmd.py
git commit -m "feat: add b1 upgrade command to backfill .agents/ scaffolding"
```

---

### Task 2: Re-pair confirmation prompt

**Files:**
- Modify: `src/b1/commands/upgrade.py`
- Test: `tests/integration/test_upgrade_cmd.py`

**Interfaces:**
- Consumes: `upgrade_cmd` from Task 1 (extends it in place — same function, same file); `b1.commands.pair.pair_cmd(sync: bool = False) -> None` (existing, already used the same way by `src/b1/commands/pull.py`).
- Produces: `upgrade_cmd` now prompts for re-pair after backfilling, identical in behavior to `pull_cmd`'s re-pair prompt.

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_upgrade_cmd.py`:

```python
from unittest.mock import patch


def test_upgrade_offers_repair_and_runs_it_on_yes(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"], input="y\n")
    assert result.exit_code == 0
    mock_pair.assert_called_once_with(sync=False)


def test_upgrade_declines_repair_on_no(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"], input="n\n")
    assert result.exit_code == 0
    mock_pair.assert_not_called()


def test_upgrade_treats_no_input_as_decline(make_project, monkeypatch):
    """Simulates non-interactive/EOF stdin (no input= given): the re-pair
    confirm prompt should be treated as "no" instead of raising click.Abort
    and exiting non-zero."""
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0
    mock_pair.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_upgrade_cmd.py -v`
Expected: FAIL on the 3 new tests — `mock_pair.assert_called_once_with(...)` / `assert_not_called()` fail because `b1.commands.upgrade` has no `pair_cmd` attribute to patch yet (`AttributeError: <module 'b1.commands.upgrade'> does not have the attribute 'pair_cmd'`).

- [ ] **Step 3: Implement the re-pair prompt**

Modify `src/b1/commands/upgrade.py` — add imports at the top:

```python
import click
```

and:

```python
from b1.commands.pair import pair_cmd
```

Then extend the end of `upgrade_cmd` (after the existing `console.print("[bold green]Upgrade complete![/bold green]")` line):

```python
    try:
        do_repair = typer.confirm("Re-pair now to apply updates?", default=False)
    except click.Abort:
        do_repair = False
    if do_repair:
        pair_cmd(sync=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_upgrade_cmd.py -v`
Expected: PASS (all 8 tests, including the 5 from Task 1 — they still pass because `click.Abort` on missing/declined input is caught and treated as "no", matching `pull_cmd`'s existing behavior).

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `uv run pytest`
Expected: PASS, no regressions.

- [ ] **Step 6: Commit**

```bash
git add src/b1/commands/upgrade.py tests/integration/test_upgrade_cmd.py
git commit -m "feat: offer re-pair confirmation after b1 upgrade backfills scaffolding"
```
