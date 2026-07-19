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
