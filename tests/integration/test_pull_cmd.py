# tests/integration/test_pull_cmd.py
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def test_pull_exits_zero_with_no_modules_installed(make_project, monkeypatch):
    project = make_project()
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["pull"], input="n\n")
    assert result.exit_code == 0


def test_pull_exits_zero_when_modules_dir_missing(tmp_path, monkeypatch):
    # Initialized project but no modules dir at all
    (tmp_path / ".agents").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["pull"], input="n\n")
    assert result.exit_code == 0


def test_pull_skips_module_not_in_cache(make_project, monkeypatch):
    project = make_project(modules=["django"])
    monkeypatch.chdir(project)

    with patch("b1.commands.pull.ModuleFetcher") as MockFetcher:
        instance = MockFetcher.return_value
        instance.cache_dir = project / "fake_cache"  # empty dir — django not present
        instance.cache_dir.mkdir()
        result = runner.invoke(app, ["pull"], input="n\n")

    assert result.exit_code == 0
    assert "Skipping" in result.output or "not found" in result.output.lower()


def test_pull_fetches_and_reinstalls_each_cached_module(make_project, make_module, monkeypatch):
    project = make_project(modules=["django"])
    monkeypatch.chdir(project)
    django_src = make_module(name="django")

    with patch("b1.commands.pull.ModuleFetcher") as MockFetcher:
        instance = MockFetcher.return_value
        fake_cache = project / "fake_cache"
        fake_cache.mkdir()
        (fake_cache / "django").mkdir()  # simulate django in cache
        instance.cache_dir = fake_cache
        instance.fetch.return_value = django_src

        with patch("b1.commands.pull.ModuleInstaller") as MockInstaller:
            result = runner.invoke(app, ["pull"], input="n\n")
            MockInstaller.return_value.install.assert_called_once_with(django_src)

    assert result.exit_code == 0


def test_pull_offers_repair_and_runs_it_on_yes(make_project):
    project = make_project(agents=["CLAUDE"])
    import os
    cwd = os.getcwd()
    os.chdir(project)
    try:
        with patch("b1.commands.pull.pair_cmd") as mock_pair:
            result = runner.invoke(app, ["pull"], input="y\n")
    finally:
        os.chdir(cwd)
    assert result.exit_code == 0
    mock_pair.assert_called_once()


def test_pull_exits_zero_when_no_input(make_project, monkeypatch):
    """Simulates non-interactive/EOF stdin (no input= given): the re-pair
    confirm prompt should be treated as "no" instead of raising click.Abort
    and exiting 1."""
    project = make_project()
    monkeypatch.chdir(project)
    with patch("b1.commands.pull.pair_cmd") as mock_pair:
        result = runner.invoke(app, ["pull"])
    assert result.exit_code == 0
    mock_pair.assert_not_called()
