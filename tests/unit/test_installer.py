# tests/unit/test_installer.py
import subprocess
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from b1.core.installer import ModuleInstaller


def _make_module_source(base: Path, name="test-module", skills=None) -> Path:
    mod_dir = base / name
    mod_dir.mkdir(parents=True)
    config = {
        "name": name,
        "version": "1.0.0",
        "type": "development",
        "description": "A test module",
        "skills": skills or [],
        "hooks": {},
    }
    (mod_dir / "b1-module.yaml").write_text(yaml.dump(config), encoding="utf-8")
    (mod_dir / "context").mkdir()
    (mod_dir / "context" / "best-practices.md").write_text("# Best practices\n", encoding="utf-8")
    return mod_dir


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".agents" / "modules").mkdir(parents=True)
    return project


def test_install_copies_files_to_modules_dir(tmp_path):
    src = _make_module_source(tmp_path / "src")
    project = _project(tmp_path)
    ModuleInstaller(project).install(src)
    assert (project / ".agents" / "modules" / "test-module").is_dir()


def test_install_preserves_context_files(tmp_path):
    src = _make_module_source(tmp_path / "src")
    project = _project(tmp_path)
    ModuleInstaller(project).install(src)
    assert (project / ".agents" / "modules" / "test-module" / "context" / "best-practices.md").exists()


def test_install_overwrites_existing_module(tmp_path):
    src = _make_module_source(tmp_path / "src")
    project = _project(tmp_path)
    installer = ModuleInstaller(project)
    installer.install(src)
    # Modify source and install again
    (src / "context" / "new-file.md").write_text("New file\n", encoding="utf-8")
    installer.install(src)
    assert (project / ".agents" / "modules" / "test-module" / "context" / "new-file.md").exists()


def test_install_raises_when_no_yaml_found(tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    project = _project(tmp_path)
    with pytest.raises(FileNotFoundError):
        ModuleInstaller(project).install(bare)


def test_install_runs_skill_command(tmp_path):
    src = _make_module_source(
        tmp_path / "src",
        skills=[{"name": "my-skill", "install_command": "echo hello"}],
    )
    project = _project(tmp_path)
    with patch("b1.core.installer.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        ModuleInstaller(project).install(src)
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs.get("shell") is True


def test_install_continues_when_skill_command_fails(tmp_path):
    src = _make_module_source(
        tmp_path / "src",
        skills=[{"name": "bad-skill", "install_command": "exit 1"}],
    )
    project = _project(tmp_path)
    with patch("b1.core.installer.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "exit 1", stderr="error")
        # Should NOT raise — installation continues despite skill failure
        ModuleInstaller(project).install(src)
    assert (project / ".agents" / "modules" / "test-module").is_dir()


def test_install_adds_proprietary_module_to_gitignore(tmp_path):
    mod_dir = tmp_path / "src" / "proprietary-module"
    mod_dir.mkdir(parents=True)
    config = {
        "name": "proprietary-module",
        "version": "1.0.0",
        "type": "development",
        "proprietary": True,
        "description": "A proprietary test module",
    }
    (mod_dir / "b1-module.yaml").write_text(yaml.dump(config), encoding="utf-8")
    (mod_dir / "context").mkdir()
    (mod_dir / "context" / "secret.md").write_text("# Secret\n", encoding="utf-8")

    project = _project(tmp_path)
    ModuleInstaller(project).install(mod_dir)

    gitignore = project / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    assert ".agents/modules/proprietary-module" in content.splitlines()

