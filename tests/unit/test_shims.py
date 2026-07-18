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
