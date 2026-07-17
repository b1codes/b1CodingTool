# tests/integration/test_init_cmd.py
from pathlib import Path
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def case_sensitive_exists(path: Path) -> bool:
    if not path.exists():
        return False
    return path.name in {p.name for p in path.parent.iterdir()}


def test_init_creates_agent_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / ".agents").is_dir()


def test_init_creates_docs_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert (tmp_path / "docs").is_dir()


def test_init_does_not_create_root_agent_md(tmp_path, monkeypatch):
    # Root AGENTS.md is a generated OUTPUT owned by `b1 pair` / the translator,
    # not authored by `b1 init`.
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert not case_sensitive_exists(tmp_path / "AGENTS.md")


def test_init_creates_local_agent_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert case_sensitive_exists(tmp_path / ".agents" / "local" / "AGENTS.md")


def test_init_creates_project_agent_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert case_sensitive_exists(tmp_path / ".agents" / "project" / "AGENTS.md")


def test_init_creates_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert (tmp_path / ".gitignore").exists()


def test_init_creates_readme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    assert (tmp_path / "README.md").exists()


def test_init_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("custom", encoding="utf-8")
    runner.invoke(app, ["init"])
    runner.invoke(app, ["init"])
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "custom"


def test_init_with_path_argument_creates_subdirectory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "my-project"
    target.mkdir()
    result = runner.invoke(app, ["init", str(target)])
    assert result.exit_code == 0
    assert (target / ".agents").is_dir()


def test_init_creates_directory_if_it_does_not_exist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    new_dir = tmp_path / "brand-new"
    result = runner.invoke(app, ["init", str(new_dir)])
    assert result.exit_code == 0
    assert new_dir.is_dir()
