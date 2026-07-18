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


def test_edge_case_explicit_scope(make_project):
    project = make_project(agents=["CLAUDE"])
    result = _run(project, ["edge-case", "Redis must be running", "--scope", "project"])
    assert result.exit_code == 0
    seed = (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Edge cases" in seed and "- Redis must be running" in seed


def test_edge_case_prompts_for_scope_when_omitted(make_project):
    project = make_project(agents=["CLAUDE"])
    # answer the scope prompt with "local"
    result = _run(project, ["edge-case", "Flaky on ARM"], input="local\n")
    assert result.exit_code == 0
    assert "- Flaky on ARM" in (project / ".agents" / "local" / "AGENTS.md").read_text(encoding="utf-8")


def test_edge_case_defaults_to_project_without_input(make_project):
    project = make_project(agents=["CLAUDE"])
    # No input= provided: simulates a non-interactive (slash-command shim) invocation,
    # where stdin is not a TTY and typer.prompt hits EOF -> click.Abort.
    result = _run(project, ["edge-case", "No TTY here"])
    assert result.exit_code == 0
    assert "- No TTY here" in (project / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
