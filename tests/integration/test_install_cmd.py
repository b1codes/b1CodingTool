# tests/integration/test_install_cmd.py
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def _make_module_source(base: Path, name="django") -> Path:
    mod_dir = base / name
    (mod_dir / "context").mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text(yaml.dump({
        "name": name, "version": "1.0.0", "type": "development",
        "description": "Test", "skills": [], "hooks": {},
    }), encoding="utf-8")
    (mod_dir / "context" / "best-practices.md").write_text("# Tips\n", encoding="utf-8")
    return mod_dir


def test_install_copies_module_to_agent_modules(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)
    src = _make_module_source(tmp_path / "src")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        MockFetcher.return_value.fetch.return_value = src
        result = runner.invoke(app, ["install", str(src)])

    assert result.exit_code == 0
    assert (project / ".agents" / "modules" / "django").is_dir()


def test_install_preserves_context_files(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)
    src = _make_module_source(tmp_path / "src")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        MockFetcher.return_value.fetch.return_value = src
        runner.invoke(app, ["install", str(src)])

    assert (project / ".agents" / "modules" / "django" / "context" / "best-practices.md").exists()


def test_install_exits_with_error_outside_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install", "/some/path"])
    assert result.exit_code != 0


def test_install_link_creates_symlink(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)
    src = _make_module_source(tmp_path / "src")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        MockFetcher.return_value.fetch.return_value = src
        result = runner.invoke(app, ["install", str(src), "--link"])

    assert result.exit_code == 0
    target = project / ".agents" / "modules" / "django"
    assert target.is_symlink()
    assert target.resolve() == src.resolve()


def test_install_exits_with_error_for_invalid_source(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        MockFetcher.return_value.fetch.side_effect = ValueError("not found")
        result = runner.invoke(app, ["install", "/nonexistent/path"])

    assert result.exit_code != 0


def test_install_multiple_modules(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)
    src_django = _make_module_source(tmp_path / "src", "django")
    src_fastapi = _make_module_source(tmp_path / "src", "fastapi")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        def mock_fetch(source):
            if "django" in str(source):
                return src_django
            elif "fastapi" in str(source):
                return src_fastapi
            return Path(source)
        MockFetcher.return_value.fetch.side_effect = mock_fetch
        
        result = runner.invoke(app, ["install", str(src_django), str(src_fastapi)])

    assert result.exit_code == 0
    assert (project / ".agents" / "modules" / "django").is_dir()
    assert (project / ".agents" / "modules" / "fastapi").is_dir()


def test_install_predefined_bundle(tmp_path, monkeypatch, make_project):
    project = make_project()
    monkeypatch.chdir(project)
    src_dart = _make_module_source(tmp_path / "src", "dart")
    src_flutter = _make_module_source(tmp_path / "src", "flutter")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        def mock_fetch(source):
            if source == "dart":
                return src_dart
            elif source == "flutter":
                return src_flutter
            return Path(source)
        MockFetcher.return_value.fetch.side_effect = mock_fetch
        
        result = runner.invoke(app, ["install", "flutter"])

    assert result.exit_code == 0
    assert (project / ".agents" / "modules" / "dart").is_dir()
    assert (project / ".agents" / "modules" / "flutter").is_dir()


def test_install_custom_bundle(tmp_path, monkeypatch, make_project):
    from b1.core.config import B1Config
    project = make_project()
    monkeypatch.chdir(project)
    
    config = B1Config(bundles={"my-custom-bundle": ["django", "fastapi"]})
    config.save(project)
    
    src_django = _make_module_source(tmp_path / "src", "django")
    src_fastapi = _make_module_source(tmp_path / "src", "fastapi")

    with patch("b1.commands.install.ModuleFetcher") as MockFetcher:
        def mock_fetch(source):
            if source == "django":
                return src_django
            elif source == "fastapi":
                return src_fastapi
            return Path(source)
        MockFetcher.return_value.fetch.side_effect = mock_fetch
        
        result = runner.invoke(app, ["install", "my-custom-bundle"])

    assert result.exit_code == 0
    assert (project / ".agents" / "modules" / "django").is_dir()
    assert (project / ".agents" / "modules" / "fastapi").is_dir()

