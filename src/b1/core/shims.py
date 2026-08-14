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

    b1 edge-case "<the edge case>" --scope project

Use `--scope local` instead if the edge case is personal to you rather than the \
whole team. After it runs, confirm where it was saved.
"""

_RECONCILE_BODY = """Some generated agent files were edited by hand and are now out of \
sync with the b1 sources. Run:

    b1 reconcile

For each changed file it shows the added lines and asks whether to promote them to the \
project seed (team) or local seed (personal), or discard them. Help me decide based on \
whether each change is a shared team rule or a personal note, then confirm the result.
"""

_UPDATE_PROJECT_BODY = """Keep this project's coding-agent tooling current: refresh Claude Code, \
Antigravity, and Codex CLI plugin marketplaces and installed plugins (whichever of those CLIs are \
on PATH), then check for skill updates.

Run:

    b1 update-project

Pass `--claude`, `--agy`, or `--codex` to target a single CLI instead of auto-detecting, `--all` to \
force all three, or `--skip-skills` to skip the `npx skills update` step. After it runs, summarize \
what got updated (or skipped, and why).
"""

_SHIMS = {
    "b1-rule.md": _RULE_BODY,
    "b1-edge-case.md": _EDGE_BODY,
    "b1-reconcile.md": _RECONCILE_BODY,
    "b1-update-project.md": _UPDATE_PROJECT_BODY,
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
