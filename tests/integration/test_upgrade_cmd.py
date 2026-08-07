# tests/integration/test_upgrade_cmd.py
from typer.testing import CliRunner
from b1.cli import app
from b1.core.exceptions import ProjectError
from unittest.mock import patch

runner = CliRunner()


def test_upgrade_errors_when_agents_dir_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ProjectError)
    assert not any(tmp_path.iterdir())


def test_upgrade_backfills_missing_local_seed_without_touching_project_seed(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    project_seed = project / ".agents" / "project" / "AGENTS.md"
    original_content = project_seed.read_text(encoding="utf-8")

    result = runner.invoke(app, ["upgrade"])

    assert result.exit_code == 0
    assert (project / ".agents" / "local" / "AGENTS.md").exists()
    assert project_seed.read_text(encoding="utf-8") == original_content


def test_upgrade_does_not_create_init_only_scaffolding(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0
    assert not (project / "docs").exists()
    assert not (project / "README.md").exists()
    assert not (project / ".gitignore").exists()


def test_upgrade_with_path_argument_targets_that_directory(make_project, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = make_project()
    result = runner.invoke(app, ["upgrade", str(project)])
    assert result.exit_code == 0
    assert (project / ".agents" / "local" / "AGENTS.md").exists()


def test_upgrade_is_idempotent(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    runner.invoke(app, ["upgrade"])
    local_seed = project / ".agents" / "local" / "AGENTS.md"
    local_seed.write_text("custom local notes", encoding="utf-8")
    runner.invoke(app, ["upgrade"])
    assert local_seed.read_text(encoding="utf-8") == "custom local notes"


def test_upgrade_offers_repair_and_runs_it_on_yes(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"], input="y\n")
    assert result.exit_code == 0
    mock_pair.assert_called_once_with(sync=False)


def test_upgrade_declines_repair_on_no(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"], input="n\n")
    assert result.exit_code == 0
    mock_pair.assert_not_called()


def test_upgrade_treats_no_input_as_decline(make_project, monkeypatch):
    """Simulates non-interactive/EOF stdin (no input= given): the re-pair
    confirm prompt should be treated as "no" instead of raising click.Abort
    and exiting non-zero."""
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.upgrade.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0
    mock_pair.assert_not_called()
