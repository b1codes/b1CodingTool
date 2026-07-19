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


def test_rule_halts_on_drift(make_project):
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule", encoding="utf-8")
    _run(project, ["rule", "seed the snapshots"])          # establishes snapshots via run_pair
    (project / "AGENTS.md").write_text("hand edited root\n", encoding="utf-8")
    result = _run(project, ["rule", "another rule"])
    assert result.exit_code == 1
    assert "reconcile" in result.output.lower()
