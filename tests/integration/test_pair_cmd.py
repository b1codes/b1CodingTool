# tests/integration/test_pair_cmd.py
import os
from pathlib import Path
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def test_pair_writes_agent_files(cd_project):
    result = runner.invoke(app, ["pair"])
    assert result.exit_code == 0
    assert (cd_project / "AGENTS.md").exists()
    assert (cd_project / "CLAUDE.md").exists()
    # GEMINI is no longer part of the supported agent matrix.
    assert not (cd_project / "GEMINI.md").exists()


def test_pair_content_includes_project_context_in_root_agents(cd_project):
    runner.invoke(app, ["pair"])
    content = (cd_project / "AGENTS.md").read_text(encoding="utf-8")
    assert "Project-specific context." in content


def test_pair_content_includes_project_context_in_claude(cd_project):
    runner.invoke(app, ["pair"])
    content = (cd_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Project-specific context." in content


def test_pair_content_includes_installed_module_context(make_project, make_module, monkeypatch):
    module = make_module(name="django", context_files={"best-practices.md": "# Django best practices\n"})
    project = make_project()
    monkeypatch.chdir(project)

    from unittest.mock import patch
    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        MockFetcher.return_value.fetch.return_value = module
        runner.invoke(app, ["install", str(module)])

    runner.invoke(app, ["pair"])

    # Lazy shared module context files are copied into .claude/context/ and
    # referenced from CLAUDE.md as a pointer, rather than being inlined.
    matches = list((project / ".claude" / "context").glob("*best-practices.md"))
    assert matches, "expected a copied context file for the django module"
    assert "Django best practices" in matches[0].read_text(encoding="utf-8")

    claude_content = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "best-practices.md" in claude_content


def test_pair_files_contain_auto_generation_warning(cd_project):
    runner.invoke(app, ["pair"])
    content = (cd_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AUTO-GENERATED" in content


def test_pair_exits_with_error_outside_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["pair"])
    assert result.exit_code != 0


def test_pair_sync_generates_full_matrix(make_project):
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# Project\nNever push to main.", encoding="utf-8")
    (project / ".agents" / "local" / "AGENTS.md").parent.mkdir(parents=True, exist_ok=True)
    (project / ".agents" / "local" / "AGENTS.md").write_text("# Local\nMy token is in .env.local", encoding="utf-8")

    cwd = os.getcwd()
    os.chdir(project)
    try:
        result = runner.invoke(app, ["pair", "--sync"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert (project / "AGENTS.md").exists()                 # root output
    assert (project / "CLAUDE.md").exists()
    assert (project / "CLAUDE.local.md").exists()
    assert (project / "AGENTS.override.md").exists()        # Codex personal (has local content)
    assert (project / ".agents" / "rules" / "local.md").exists()  # Antigravity personal
    assert "Never push to main." in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_run_pair_generates_without_prompting(make_project):
    from b1.commands.pair import run_pair
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# P\nrule one", encoding="utf-8")
    ok = run_pair(project, ["CLAUDE", "CODEX", "ANTIGRAVITY"])
    assert ok is True
    assert (project / "AGENTS.md").exists()
    assert (project / "CLAUDE.md").exists()


def test_run_pair_returns_false_when_empty(tmp_path):
    from b1.commands.pair import run_pair
    (tmp_path / ".agents").mkdir()
    assert run_pair(tmp_path, ["CLAUDE"]) is False


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
