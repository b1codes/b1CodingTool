# Phase 3 — Drift-Safety + `b1 reconcile` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated agent files safe to hand-edit — no `b1 pair`/`rule`/`edge-case`/`pull` silently overwrites a hand-edit, and `b1 reconcile` promotes hand-edits back into the seeds.

**Architecture:** A `snapshots` module records a full copy of each seed-derived generated file after every fan-out. `run_pair` checks drift before generating and raises `DriftError` (halting the whole op) unless `force=True`. `b1 reconcile` diffs drifted files against their snapshots and promotes the added lines to a seed (or discards), then force-regenerates.

**Tech Stack:** Python 3.12, Typer, Rich, difflib, pytest, `uv`.

## Global Constraints

- Run all Python from `b1CodingTool/` with `uv`. Tests: `uv run pytest`.
- Drift-tracked set (v1): `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.override.md`, `.agents/rules/local.md`. No others.
- Snapshots: full copies under gitignored `.agents/.b1-snapshots/`.
- Halt the WHOLE operation on any drift (write nothing); never partial-clobber.
- A tracked file with NO snapshot yet is NOT drift (it's newly generated).
- Reconcile is file-level: promote/discard the whole added block; `difflib.ndiff` extracts added lines.
- `run_pair(..., force=True)` bypasses the drift check (used only by `b1 reconcile` after resolving).

---

## File Structure

**New:** `src/b1/core/snapshots.py`, `src/b1/commands/reconcile.py`, `tests/unit/test_snapshots.py`, `tests/integration/test_reconcile_cmd.py`.
**Modified:** `src/b1/core/exceptions.py` (`DriftError`), `src/b1/commands/pair.py` (`run_pair` force+drift+snapshot, `_run_pair_or_halt` helper), `src/b1/commands/rule.py` + `edge_case.py` (use the halt helper), `src/b1/cli.py` (register `reconcile`), `src/b1/core/shims.py` (`/b1-reconcile` shim), `src/b1/core/scaffolder.py` + `src/b1/core/translator.py` (gitignore snapshots + reconcile shim).

---

### Task 1: `snapshots` module

**Files:** Create `src/b1/core/snapshots.py`, `tests/unit/test_snapshots.py`.

**Interfaces:**
- Produces: `TRACKED` (list[str]); `tracked_files(project_dir) -> list[Path]`; `record_snapshots(project_dir) -> None`; `snapshot_for(project_dir, path: Path) -> Optional[str]`; `check_drift(project_dir) -> list[Path]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_snapshots.py
from b1.core.snapshots import record_snapshots, check_drift, snapshot_for


def _write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_no_drift_right_after_record(tmp_path):
    _write(tmp_path / "AGENTS.md", "generated\n")
    _write(tmp_path / "CLAUDE.md", "generated\n")
    record_snapshots(tmp_path)
    assert check_drift(tmp_path) == []


def test_detects_handedit(tmp_path):
    _write(tmp_path / "AGENTS.md", "generated\n")
    record_snapshots(tmp_path)
    (tmp_path / "AGENTS.md").write_text("generated\n- my hand edit\n", encoding="utf-8")
    drifted = check_drift(tmp_path)
    assert [p.name for p in drifted] == ["AGENTS.md"]


def test_file_without_snapshot_is_not_drift(tmp_path):
    # no record_snapshots call -> a freshly generated file is not "drift"
    _write(tmp_path / "AGENTS.md", "generated\n")
    assert check_drift(tmp_path) == []


def test_snapshot_for_returns_recorded_content(tmp_path):
    _write(tmp_path / "CLAUDE.md", "v1\n")
    record_snapshots(tmp_path)
    assert snapshot_for(tmp_path, tmp_path / "CLAUDE.md") == "v1\n"


def test_record_prunes_snapshot_when_file_removed(tmp_path):
    f = tmp_path / "AGENTS.override.md"
    _write(f, "personal\n")
    record_snapshots(tmp_path)
    f.unlink()
    record_snapshots(tmp_path)
    assert snapshot_for(tmp_path, f) is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/unit/test_snapshots.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'b1.core.snapshots'`

- [ ] **Step 3: Implement**

```python
# src/b1/core/snapshots.py
import shutil
from pathlib import Path
from typing import List, Optional

SNAPSHOT_DIR = ".agents/.b1-snapshots"

# Generated files whose content maps to a seed — drift-tracked in v1.
TRACKED = [
    "AGENTS.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "AGENTS.override.md",
    ".agents/rules/local.md",
]


def _snap_name(rel: str) -> str:
    return rel.replace("/", "__")


def _snap_dir(project_dir: Path) -> Path:
    return project_dir / SNAPSHOT_DIR


def tracked_files(project_dir: Path) -> List[Path]:
    return [project_dir / rel for rel in TRACKED if (project_dir / rel).exists()]


def record_snapshots(project_dir: Path) -> None:
    """Copy each existing tracked file into the snapshot dir; prune snapshots
    for tracked files that no longer exist."""
    snap = _snap_dir(project_dir)
    snap.mkdir(parents=True, exist_ok=True)
    for rel in TRACKED:
        f = project_dir / rel
        target = snap / _snap_name(rel)
        if f.exists():
            shutil.copyfile(f, target)
        elif target.exists():
            target.unlink()


def snapshot_for(project_dir: Path, path: Path) -> Optional[str]:
    rel = path.relative_to(project_dir).as_posix()
    target = _snap_dir(project_dir) / _snap_name(rel)
    return target.read_text(encoding="utf-8") if target.exists() else None


def check_drift(project_dir: Path) -> List[Path]:
    """Tracked files that exist, have a snapshot, and differ from it."""
    drifted = []
    for rel in TRACKED:
        f = project_dir / rel
        if not f.exists():
            continue
        snap = snapshot_for(project_dir, f)
        if snap is None:
            continue  # no baseline yet -> not drift
        if f.read_text(encoding="utf-8") != snap:
            drifted.append(f)
    return drifted
```

- [ ] **Step 4: Run it to verify it passes**

Run: `uv run pytest tests/unit/test_snapshots.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/b1/core/snapshots.py tests/unit/test_snapshots.py
git commit -m "feat(snapshots): full-copy snapshots + drift detection for generated files"
```

---

### Task 2: `DriftError` + drift-halt in `run_pair`, wired into pair/rule/edge-case

**Files:** Modify `src/b1/core/exceptions.py`, `src/b1/commands/pair.py`, `src/b1/commands/rule.py`, `src/b1/commands/edge_case.py`. Test: `tests/integration/test_pair_cmd.py`, `tests/integration/test_rule_cmd.py`.

**Interfaces:**
- Consumes: `check_drift`, `record_snapshots` (Task 1).
- Produces: `DriftError(files: list[Path])` with `.files`; `run_pair(project_dir, agents, config=None, force=False) -> bool` (raises `DriftError` when not forced and drift exists; records snapshots after generating); `_run_pair_or_halt(project_dir, agents, config=None) -> bool` (catches `DriftError`, prints, exits 1).

- [ ] **Step 1: Write the failing tests**

```python
# tests/integration/test_pair_cmd.py  (append)
def test_run_pair_raises_drifterror_on_handedit(make_project):
    from b1.commands.pair import run_pair
    from b1.core.exceptions import DriftError
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule", encoding="utf-8")
    run_pair(project, ["CLAUDE"])                      # first run records snapshots
    (project / "CLAUDE.md").write_text("hand edited\n", encoding="utf-8")
    try:
        run_pair(project, ["CLAUDE"])
        assert False, "expected DriftError"
    except DriftError as e:
        assert any(p.name == "CLAUDE.md" for p in e.files)


def test_run_pair_force_bypasses_drift(make_project):
    from b1.commands.pair import run_pair
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule", encoding="utf-8")
    run_pair(project, ["CLAUDE"])
    (project / "CLAUDE.md").write_text("hand edited\n", encoding="utf-8")
    assert run_pair(project, ["CLAUDE"], force=True) is True   # no raise
    # regenerated -> snapshot refreshed -> no drift now
    from b1.core.snapshots import check_drift
    assert check_drift(project) == []
```

```python
# tests/integration/test_rule_cmd.py  (append; reuse the module's _run helper)
def test_rule_halts_on_drift(make_project):
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule", encoding="utf-8")
    _run(project, ["rule", "seed the snapshots"])          # establishes snapshots via run_pair
    (project / "AGENTS.md").write_text("hand edited root\n", encoding="utf-8")
    result = _run(project, ["rule", "another rule"])
    assert result.exit_code == 1
    assert "reconcile" in result.output.lower()
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/integration/test_pair_cmd.py::test_run_pair_raises_drifterror_on_handedit tests/integration/test_rule_cmd.py::test_rule_halts_on_drift -v`
Expected: FAIL (`DriftError` doesn't exist; no drift check).

- [ ] **Step 3: Add `DriftError`**

Append to `src/b1/core/exceptions.py`:

```python
class DriftError(B1Error):
    """Raised when a generated file was hand-edited since b1 last wrote it."""
    def __init__(self, files):
        self.files = files
        names = ", ".join(str(f) for f in files)
        super().__init__(
            f"Hand-edited generated files detected: {names}",
            suggestions=["Run `b1 reconcile` to promote or discard the changes."],
        )
```

- [ ] **Step 4: Update `run_pair` + add the halt helper**

In `src/b1/commands/pair.py`, add imports:

```python
from b1.core.snapshots import check_drift, record_snapshots
from b1.core.exceptions import DriftError
```

Replace `run_pair` with:

```python
def run_pair(project_dir: Path, agents: list[str], config: Optional[B1Config] = None, force: bool = False) -> bool:
    """Non-interactive compile -> translate core. Returns True if files were generated,
    False if there was no context to compile. Raises DriftError when a generated file
    was hand-edited (unless force=True). Records snapshots after generating."""
    if config is None:
        config = B1Config.load(project_dir)
    if not force:
        drifted = check_drift(project_dir)
        if drifted:
            raise DriftError(drifted)
    hook_engine = HookEngine(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)

    hook_engine.run_hooks("pre-pair")
    compiled = compiler.compile()
    if compiled.is_empty():
        return False
    translator.generate_files(agents, compiled)
    hook_engine.run_hooks("post-pair")
    record_snapshots(project_dir)
    return True


def _run_pair_or_halt(project_dir: Path, agents: list[str], config: Optional[B1Config] = None) -> bool:
    """run_pair, but on drift print a clear halt message and exit non-zero."""
    try:
        return run_pair(project_dir, agents, config=config)
    except DriftError as e:
        console.print("[bold red]Hand-edited generated files detected:[/bold red]")
        for f in e.files:
            console.print(f"  - {f.relative_to(project_dir)}")
        console.print("Run [bold]b1 reconcile[/bold] to resolve, then retry.")
        raise typer.Exit(1)
```

In `pair_cmd`, replace the line `if not run_pair(project_dir, agents, config=config):` with `if not _run_pair_or_halt(project_dir, agents, config=config):` (leave the rest of `pair_cmd` unchanged).

- [ ] **Step 5: Wire the helper into rule/edge-case**

In `src/b1/commands/rule.py`: change the import `from b1.commands.pair import run_pair, FULL_MATRIX` to `from b1.commands.pair import _run_pair_or_halt, FULL_MATRIX`, and change `run_pair(project_dir, FULL_MATRIX)` to `_run_pair_or_halt(project_dir, FULL_MATRIX)`.

In `src/b1/commands/edge_case.py`: the same two changes.

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/integration/test_pair_cmd.py tests/integration/test_rule_cmd.py tests/integration/test_edge_case_cmd.py -q`
Expected: PASS. Existing pair/rule/edge tests still pass (first fan-out records snapshots; no drift on a clean run). If any existing test hand-edits a generated file between two `run_pair`/command calls, it will now correctly need a `force=True` or a re-snapshot — none should, but fix by matching the new contract if one does.

- [ ] **Step 7: Commit**

```bash
git add src/b1/core/exceptions.py src/b1/commands/pair.py src/b1/commands/rule.py src/b1/commands/edge_case.py tests/integration/test_pair_cmd.py tests/integration/test_rule_cmd.py
git commit -m "feat(pair): halt fan-out on hand-edited generated files (DriftError)"
```

---

### Task 3: `b1 reconcile` command

**Files:** Create `src/b1/commands/reconcile.py`; modify `src/b1/cli.py`. Test: `tests/integration/test_reconcile_cmd.py`.

**Interfaces:**
- Consumes: `check_drift`, `snapshot_for` (Task 1); `run_pair`, `FULL_MATRIX` (Task 2).
- Produces: `reconcile_cmd(discard_all: bool = False)`; CLI name `reconcile`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/integration/test_reconcile_cmd.py
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


def _seed_and_snapshot(project):
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nbase rule", encoding="utf-8")
    _run(project, ["pair", "--sync"])   # generates + records snapshots


def test_reconcile_promotes_root_edit_to_project_seed(make_project):
    project = make_project(agents=["CLAUDE"])
    _seed_and_snapshot(project)
    # hand-edit the committed root AGENTS.md
    root = project / "AGENTS.md"
    root.write_text(root.read_text(encoding="utf-8") + "\n- hand added guardrail\n", encoding="utf-8")
    result = _run(project, ["reconcile"], input="p\n")   # promote to project
    assert result.exit_code == 0
    proj_seed = (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "- hand added guardrail" in proj_seed
    # after regenerate, no drift remains
    from b1.core.snapshots import check_drift
    assert check_drift(project) == []


def test_reconcile_discard_all_reverts(make_project):
    project = make_project(agents=["CLAUDE"])
    _seed_and_snapshot(project)
    root = project / "AGENTS.md"
    root.write_text(root.read_text(encoding="utf-8") + "\n- throwaway\n", encoding="utf-8")
    result = _run(project, ["reconcile", "--discard-all"])
    assert result.exit_code == 0
    assert "- throwaway" not in (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "- throwaway" not in (project / "AGENTS.md").read_text(encoding="utf-8")  # reverted


def test_reconcile_nothing_to_do(make_project):
    project = make_project(agents=["CLAUDE"])
    _seed_and_snapshot(project)
    result = _run(project, ["reconcile"])
    assert result.exit_code == 0
    assert "nothing to reconcile" in result.output.lower()
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/integration/test_reconcile_cmd.py -v`
Expected: FAIL — `No such command 'reconcile'`.

- [ ] **Step 3: Implement**

```python
# src/b1/commands/reconcile.py
import difflib
import typer
from typing import Annotated, List
from pathlib import Path
from rich.console import Console

from b1.core.snapshots import check_drift, snapshot_for
from b1.commands.pair import run_pair, FULL_MATRIX

console = Console()


def _added_lines(old: str, new: str) -> List[str]:
    added = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("+ "):
            added.append(line[2:])
    return added


def _append_block(project_dir: Path, scope: str, lines: List[str]) -> None:
    seed = project_dir / ".agents" / scope / "AGENTS.md"
    seed.parent.mkdir(parents=True, exist_ok=True)
    existing = seed.read_text(encoding="utf-8") if seed.exists() else ""
    block = "\n".join(lines).strip()
    prefix = existing.rstrip("\n")
    joiner = "\n\n" if prefix else ""
    seed.write_text(f"{prefix}{joiner}{block}\n", encoding="utf-8")


def reconcile_cmd(
    discard_all: Annotated[bool, typer.Option("--discard-all", help="Discard every hand-edit (revert to generated).")] = False,
):
    """Promote or discard hand-edits made directly to generated agent files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    drifted = check_drift(project_dir)
    if not drifted:
        console.print("[green]Nothing to reconcile — no hand-edits detected.[/green]")
        return

    for f in drifted:
        rel = f.relative_to(project_dir)
        old = snapshot_for(project_dir, f) or ""
        added = _added_lines(old, f.read_text(encoding="utf-8"))
        if discard_all:
            console.print(f"[yellow]Discarding hand-edits in {rel}.[/yellow]")
            continue
        console.print(f"\n[bold]{rel}[/bold] — your added lines:")
        for line in added:
            console.print(f"  [green]+ {line}[/green]")
        choice = typer.prompt("Promote to (p)roject seed, (l)ocal seed, or (d)iscard?", default="d")
        c = choice.strip().lower()[:1]
        if c == "p":
            _append_block(project_dir, "project", added)
            console.print("[green]Promoted to .agents/project/AGENTS.md[/green]")
        elif c == "l":
            _append_block(project_dir, "local", added)
            console.print("[green]Promoted to .agents/local/AGENTS.md[/green]")
        else:
            console.print("[yellow]Discarding.[/yellow]")

    run_pair(project_dir, FULL_MATRIX, force=True)   # regenerate past the drift, refresh snapshots
    console.print("\n[bold green]Reconcile complete — agent files regenerated.[/bold green]")
```

Register in `src/b1/cli.py`: add `from b1.commands.reconcile import reconcile_cmd` with the other imports, and `app.command(name="reconcile")(reconcile_cmd)` after the `edge-case` registration.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/integration/test_reconcile_cmd.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/b1/commands/reconcile.py src/b1/cli.py tests/integration/test_reconcile_cmd.py
git commit -m "feat(cli): add b1 reconcile to promote/discard hand-edits"
```

---

### Task 4: `/b1-reconcile` shim + gitignore snapshots

**Files:** Modify `src/b1/core/shims.py`, `src/b1/core/scaffolder.py`, `src/b1/core/translator.py`. Test: `tests/unit/test_shims.py`.

**Interfaces:** Consumes/extends `write_agent_shims` (adds a third shim). Adds gitignore entries `.agents/.b1-snapshots/` and `.agents/skills/b1-reconcile.md`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_shims.py  (append)
def test_writes_reconcile_shim(tmp_path):
    from b1.core.shims import write_agent_shims
    write_agent_shims(tmp_path)
    for p in [".claude/commands/b1-reconcile.md", ".agents/skills/b1-reconcile.md"]:
        f = tmp_path / p
        assert f.exists(), p
        assert "b1 reconcile" in f.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/test_shims.py::test_writes_reconcile_shim -v`
Expected: FAIL — the reconcile shim files aren't written.

- [ ] **Step 3: Add the reconcile shim body + entry**

In `src/b1/core/shims.py`, add the body constant after `_EDGE_BODY`:

```python
_RECONCILE_BODY = """Some generated agent files were edited by hand and are now out of \
sync with the b1 sources. Run:

    b1 reconcile

For each changed file it shows the added lines and asks whether to promote them to the \
project seed (team) or local seed (personal), or discard them. Help me decide based on \
whether each change is a shared team rule or a personal note, then confirm the result.
"""
```

and add it to the `_SHIMS` dict:

```python
_SHIMS = {
    "b1-rule.md": _RULE_BODY,
    "b1-edge-case.md": _EDGE_BODY,
    "b1-reconcile.md": _RECONCILE_BODY,
}
```

- [ ] **Step 4: Gitignore snapshots + reconcile shim**

In `src/b1/core/scaffolder.py`, add to `GITIGNORE_CONTENT` after the `.agents/skills/b1-edge-case.md` line:

```
.agents/skills/b1-reconcile.md
.agents/.b1-snapshots/
```

In `src/b1/core/translator.py` `_ensure_gitignore`, extend the `entries` list with:

```python
                   ".agents/skills/b1-reconcile.md", ".agents/.b1-snapshots/"
```

(append these two to the existing list literal).

- [ ] **Step 5: Run the suite**

Run: `uv run pytest -q`
Expected: PASS — 0 failures.

- [ ] **Step 6: Commit**

```bash
git add src/b1/core/shims.py src/b1/core/scaffolder.py src/b1/core/translator.py tests/unit/test_shims.py
git commit -m "feat(shims): add /b1-reconcile shim; gitignore snapshots"
```

---

## Self-Review

**Spec coverage:**
- §3.1 snapshots module (record/check/snapshot_for, prune, no-snapshot-not-drift) → Task 1. ✅
- §3.2 drift-halt in run_pair (force, DriftError, record after) → Task 2. ✅
- §3.3 command-layer halt (pair/rule/edge-case via `_run_pair_or_halt`) → Task 2. ✅
- §3.4 `b1 reconcile` (per-file promote/discard, difflib added lines, --discard-all, force regenerate) → Task 3. ✅
- §3.5 `/b1-reconcile` shim → Task 4. ✅
- §4 gitignore `.agents/.b1-snapshots/` → Task 4. ✅

**Placeholder scan:** none.

**Type consistency:** `check_drift/record_snapshots/snapshot_for` (Task 1) consumed by Tasks 2–3; `DriftError(files).files` (Task 2) consumed by `_run_pair_or_halt` and reconcile's halt message; `run_pair(..., force=False)` (Task 2) consumed by Task 3 (`force=True`). `_run_pair_or_halt` (Task 2) consumed by rule/edge-case. Names consistent across tasks.

**Note (accepted v1 behavior):** `b1 rule`/`edge-case` append to the seed *before* the fan-out; if a DIFFERENT generated file has drifted, the note is saved to the seed but the fan-out halts (exit 1, "run b1 reconcile"). After reconcile + regenerate, the already-saved note is fanned out. Acceptable for v1.
