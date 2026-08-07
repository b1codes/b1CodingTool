# `b1 upgrade` — Design

## Problem

Older projects bootstrapped with earlier versions of b1CodingTool are missing `.agents/`
scaffolding that newer versions of `b1 init` create by default — most commonly
`.agents/local/AGENTS.md`. There is currently no non-destructive way to bring an
*existing* project's `.agents/` markdown scaffolding up to date short of re-running
`b1 init`, whose name and framing ("bootstraps a new or existing project") don't read
as a maintenance operation for a project someone is already actively using.

## Non-goals

- Not module syncing. `b1 pull` already re-fetches installed modules from upstream —
  unrelated to `.agents/` scaffolding shape.
- Not agent-file regeneration. `pair --sync` already regenerates the full compiled
  agent matrix (CLAUDE/CODEX/ANTIGRAVITY) — unrelated to scaffolding shape. The name
  `sync` was considered for this new command and rejected specifically because of the
  vocabulary collision with `pair --sync`, which does something unrelated.
- Not drift reconciliation. `b1 reconcile` already handles hand-edits to *generated*
  files — this command only concerns the hand-authored seed files that feed compilation.
- No new backfill logic. All backfill behavior already exists in
  `b1.core.context_manager.setup_context` (used today by `b1 init`) and is reused as-is.

## Command: `b1 upgrade [path]`

Reconciles an existing project's `.agents/` scaffolding against what the current
b1CodingTool version expects, without touching unrelated scaffolding (`docs/`,
`README.md`, `.gitignore`) that `b1 init` also creates for brand-new projects.

### Flow

1. Resolve target path — optional positional argument, defaults to `Path.cwd()`
   (mirrors `b1 init`'s signature).
2. Guard: if `<path>/.agents` does not exist, raise `ProjectError("Not a b1CodingTool
   project.")` with suggestion `"Run \`b1 init\` to bootstrap the project structure."`
   — same error shape `b1 pull` uses. `upgrade` assumes a project already exists to
   reconcile; it does not bootstrap one from nothing.
3. Call `setup_context(path)` unchanged (no new logic). This already, idempotently:
   - migrates lowercase `agents.md` → `AGENTS.md` at project root and in
     `.agents/project/`
   - creates `.agents/project/AGENTS.md` seed if missing
   - creates `.agents/local/AGENTS.md` seed if missing
   - migrates a hand-authored root `AGENTS.md` into the project seed if the root file
     isn't yet a generated one
   - generates root `AGENTS.md` via `ContextCompiler`/`AgentTranslator` if it doesn't
     exist yet
   - `setup_context` already prints a line per action taken ("Created ...", "...
     already exists, skipping") — this is the command's change summary; no separate
     reporting is added.
4. Print `"Upgrade complete!"` (style consistent with `init_cmd`'s completion message).
5. Prompt `"Re-pair now to apply updates?"` via `typer.confirm(..., default=False)`,
   catching `click.Abort` and treating it as "no" — identical pattern to `pull_cmd`.
   If confirmed, call `pair_cmd(sync=False)` so newly-backfilled seed content is
   compiled into `CLAUDE.md`/`GEMINI.md`/`AGENTS.md`.

### Error handling

Matches existing sibling commands:
- `ProjectError` (with `suggestions`) when `.agents/` is missing — same shape as
  `pull_cmd`'s guard.
- `click.Abort` on the re-pair confirm prompt is caught and treated as declining.

### Files

- New: `src/b1/commands/upgrade.py` — `upgrade_cmd`, structured directly after
  `src/b1/commands/pull.py`.
- Modified: `src/b1/cli.py` — register `app.command(name="upgrade")(upgrade_cmd)`.
- New: `tests/integration/test_upgrade_cmd.py`, following the conventions in
  `tests/integration/test_pull_cmd.py` and `tests/integration/test_init_cmd.py`.
  Cases:
  - missing `.agents/` → raises/errors out, no files written.
  - project with `.agents/project/AGENTS.md` present but no `.agents/local/` →
    `.agents/local/AGENTS.md` is created; existing `.agents/project/AGENTS.md`
    content is left byte-for-byte unchanged.
  - re-pair prompt: confirmed → `pair_cmd` invoked; declined → not invoked; aborted
    (`click.Abort`) → treated as declined.

## Testing

Integration-level, matching the existing test style for `init`/`pull` (real temp
project directories, no mocking of `setup_context` internals — exercise the real
idempotent behavior it already has test coverage for in
`tests/unit/test_context_manager.py`).
