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
    assert "- hand added guardrail" in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_reconcile_promotes_root_edit_to_local_seed(make_project):
    project = make_project(agents=["CLAUDE"])
    _seed_and_snapshot(project)
    # hand-edit the committed root AGENTS.md
    root = project / "AGENTS.md"
    root.write_text(root.read_text(encoding="utf-8") + "\n- hand added local guardrail\n", encoding="utf-8")
    result = _run(project, ["reconcile"], input="l\n")   # promote to local
    assert result.exit_code == 0
    local_seed = (project / ".agents" / "local" / "AGENTS.md").read_text(encoding="utf-8")
    assert "- hand added local guardrail" in local_seed
    proj_seed = (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "- hand added local guardrail" not in proj_seed
    # after regenerate, no drift remains
    from b1.core.snapshots import check_drift
    assert check_drift(project) == []
    assert "- hand added local guardrail" in (project / "CLAUDE.local.md").read_text(encoding="utf-8")


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


def test_reconcile_reports_honest_message_when_regen_is_empty(make_project):
    """When every context source is removed after the initial snapshot (no project
    seed, no local seed, no modules), the post-loop run_pair() compiles to zero
    items and returns False. reconcile must not claim success — it should print a
    distinct message and leave the pre-existing drift in place, since nothing was
    actually regenerated."""
    project = make_project(agents=["CLAUDE"])
    _seed_and_snapshot(project)
    root = project / "AGENTS.md"
    root.write_text(root.read_text(encoding="utf-8") + "\n- drift after seeds emptied\n", encoding="utf-8")
    # Remove the only context source (no local seed or modules exist in this fixture)
    # so the compile is genuinely empty when reconcile's run_pair(force=True) runs.
    (project / ".agents" / "project" / "AGENTS.md").unlink()
    result = _run(project, ["reconcile"], input="d\n")
    assert result.exit_code == 0
    assert "no context to regenerate" in result.output.lower()
    assert "reconcile complete" not in result.output.lower()
    from b1.core.snapshots import check_drift
    # run_pair returned False (empty compile) so nothing was regenerated -- the
    # drift introduced above must still be present.
    assert check_drift(project) != []
