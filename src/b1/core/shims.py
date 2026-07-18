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
