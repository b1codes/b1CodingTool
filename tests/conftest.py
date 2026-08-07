# tests/conftest.py
import shutil
import pytest
import yaml
from pathlib import Path


@pytest.fixture
def make_module(tmp_path):
    """
    Factory fixture. Returns a callable that creates a valid module source directory.

    Usage:
        module_dir = make_module()
        module_dir = make_module(name="django", context_files={"best-practices.md": "# tips"})
    """
    def _make(name="test-module", version="1.0.0", context_files=None):
        module_dir = tmp_path / "src_modules" / name
        module_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "name": name,
            "version": version,
            "type": "development",
            "description": f"Test module: {name}",
            "skills": [],
            "hooks": {},
        }
        (module_dir / "b1-module.yaml").write_text(yaml.dump(config), encoding="utf-8")

        if context_files:
            ctx_dir = module_dir / "context"
            ctx_dir.mkdir(exist_ok=True)
            for filename, content in context_files.items():
                (ctx_dir / filename).write_text(content, encoding="utf-8")

        return module_dir

    return _make


@pytest.fixture
def make_project(tmp_path):
    """
    Factory fixture. Returns a callable that creates a fully scaffolded project directory.

    Usage:
        project = make_project()
        project = make_project(modules=["django"])
        project = make_project(agents=["CLAUDE"], upstream_repo="org/repo")
    """
    def _make(agents=None, upstream_repo=None, modules=None):
        project_dir = tmp_path / "project"
        project_dir.mkdir(exist_ok=True)

        # .agents/ structure
        (project_dir / ".agents" / "project").mkdir(parents=True)
        (project_dir / ".agents" / "modules").mkdir(parents=True)
        (project_dir / ".agents" / "local").mkdir(parents=True, exist_ok=True)

        # AGENTS.md files
        (project_dir / "AGENTS.md").write_text(
            "# b1CodingTool: Global Context\nRoot agent context.\n",
            encoding="utf-8",
        )
        (project_dir / ".agents" / "project" / "AGENTS.md").write_text(
            "# b1CodingTool: Project Context\nProject-specific context.\n",
            encoding="utf-8",
        )

        # config.yaml
        config_data = {
            "upstream_repo": upstream_repo or "",
            "active_agents": agents or ["CLAUDE"],
        }
        (project_dir / ".agents" / "config.yaml").write_text(
            yaml.dump(config_data), encoding="utf-8"
        )

        # Install named modules
        if modules:
            for name in modules:
                mod_dir = project_dir / ".agents" / "modules" / name
                (mod_dir / "context").mkdir(parents=True)
                (mod_dir / "b1-module.yaml").write_text(
                    yaml.dump({
                        "name": name,
                        "version": "1.0.0",
                        "type": "development",
                        "description": f"Test {name} module",
                        "skills": [],
                        "hooks": {},
                    }),
                    encoding="utf-8",
                )

        return project_dir

    return _make


@pytest.fixture
def cd_project(make_project, monkeypatch):
    """
    Creates a default scaffolded project and chdirs into it.
    The original working directory is restored automatically after the test.

    Usage:
        def test_something(cd_project):
            # Path.cwd() is now the temp project dir
            result = runner.invoke(app, ["pair"])
    """
    project_dir = make_project()
    monkeypatch.chdir(project_dir)
    return project_dir
