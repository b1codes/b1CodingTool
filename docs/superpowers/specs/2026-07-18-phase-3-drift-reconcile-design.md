# Phase 3 — Drift-Safety + `b1 reconcile` (Reverse Sync) — Design Spec

**Date:** 2026-07-18
**Status:** Approved design
**Parent spec:** `2026-07-16-agent-file-management-design.md` (§7). Phases 1 (fan-out) and 2 (slash commands) are merged.

---

## 1. Goal

Make the generated agent files **safe to hand-edit**. Today any `b1 pair` (directly or via `b1 rule`/`b1 edge-case`/`b1 pull`) overwrites the generated files wholesale — a hand-edit to `CLAUDE.md` or the committed root `AGENTS.md` is silently lost. Phase 3 adds:
1. A **drift-safety invariant**: no write path may silently overwrite a generated file that was hand-edited since b1 last wrote it.
2. **`b1 reconcile`**: a guided reverse-sync that promotes a hand-edit back into the correct seed (or discards it), then re-generates.

## 2. Core invariant

**No write path overwrites a drifted file.** `run_pair` (the single fan-out choke point — `pair`, `pull`, `rule`, `edge-case` all call it) checks drift **before** generating; if any tracked file drifted, it **halts the entire operation** (writes nothing) and raises `DriftError`. After a successful generate it **records fresh snapshots**.

## 3. Components

### 3.1 `core/snapshots.py` (new)
- Snapshots live under **`.agents/.b1-snapshots/`** (gitignored), one full copy per tracked file (mangled path → snapshot file). Full copies (not hashes) so `b1 reconcile` can diff.
- **Drift-tracked set (v1):** `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.override.md`, `.agents/rules/local.md`. (The volatile `.claude/context/`, `.claude/commands/`, `.agents/skills/` are excluded — module-derived or static; promotion to a seed is meaningless. Documented as a future extension.)
- API:
  - `tracked_files(project_dir) -> list[Path]` — the subset of the 5 tracked paths that currently exist.
  - `record_snapshots(project_dir) -> None` — copy each existing tracked file into the snapshot dir.
  - `check_drift(project_dir) -> list[Path]` — tracked files that exist AND have a snapshot AND differ from it (a file with no snapshot yet is NOT drift — it's newly generated).
  - `snapshot_for(project_dir, path) -> Optional[str]` — the snapshot content for a given tracked file (for diffing).

### 3.2 Drift-halt in `run_pair` (`commands/pair.py`)
- New signature: `run_pair(project_dir, agents, config=None, force=False) -> bool`.
- If `not force`: `drifted = check_drift(project_dir)`; if `drifted`, raise `DriftError(drifted)` (writes nothing).
- Generate as before, then `record_snapshots(project_dir)`.
- `DriftError` (new, in `core/exceptions.py`, subclass of `B1Error`) carries the drifted file list.

### 3.3 Command-layer halt handling
`pair_cmd`, `rule_cmd`, `edge_case_cmd`, and `pull`'s re-pair catch `DriftError` and print a clear message: the drifted files + "Run `b1 reconcile` to resolve." Exit non-zero. (A small shared helper avoids duplicating the catch/print.)

### 3.4 `b1 reconcile` (`commands/reconcile.py`, new)
- `drifted = check_drift(project_dir)`. If empty: "Nothing to reconcile." and exit 0.
- For each drifted file:
  - Compute the **added lines** via `difflib` (on-disk vs snapshot) and show them.
  - Prompt: **promote to project seed (shared)** / **promote to local seed (personal)** / **discard (revert to generated)**.
  - On promote: append the added lines as a block to the chosen seed (`.agents/project/AGENTS.md` or `.agents/local/AGENTS.md`).
  - On discard: do nothing (the regenerate below overwrites the file).
- After all files decided: `run_pair(project_dir, FULL_MATRIX, force=True)` (bypasses the halt, records fresh snapshots), then confirm.
- `--discard-all` flag: skip prompts, discard every drift (revert to generated).

### 3.5 `/b1-reconcile` agent shim (`core/shims.py`)
Add a third shim (`b1-reconcile.md`) for Claude (`.claude/commands/`) and Antigravity (`.agents/skills/`) that tells the agent to run `b1 reconcile` and help the user classify each drifted file's changes (shared vs personal vs discard). Gitignored like the others.

### 3.6 Snapshot bootstrapping
`record_snapshots` runs after every generate, so a normal `b1 pair` establishes snapshots. A project that has generated files but no snapshots yet (upgrading to Phase 3) has no drift on first check (files without a snapshot are not drift) — the first successful `run_pair` records them. No migration step needed.

## 4. Files to touch
- New: `src/b1/core/snapshots.py`, `src/b1/commands/reconcile.py`.
- Modify: `src/b1/commands/pair.py` (`run_pair` force + drift check + snapshot), `src/b1/core/exceptions.py` (`DriftError`), `src/b1/commands/rule.py` / `edge_case.py` / `pull.py` (catch `DriftError`), `src/b1/cli.py` (register `reconcile`), `src/b1/core/shims.py` (`/b1-reconcile` shim), `src/b1/core/scaffolder.py` + `translator._ensure_gitignore` (gitignore `.agents/.b1-snapshots/`).

## 5. Decisions (locked)
- Halt the **whole** operation on any drift (never partial-clobber).
- Reconcile is **file-level** (promote/discard the whole added block; no per-hunk parsing in v1).
- Snapshots are **full copies** under gitignored `.agents/.b1-snapshots/`.
- Drift-tracked set is the **5 seed-derived files**; volatile filemap/shim dirs excluded in v1.
- `b1 reconcile` CLI + `/b1-reconcile` shim (both).

## 6. Non-goals / follow-ups
- Per-hunk / per-line reconcile classification.
- Drift-tracking the filemap/shim directories.
- Auto-classifying promoted content by heading (v1 appends the block; user picks the seed).
