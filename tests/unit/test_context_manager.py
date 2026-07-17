# tests/unit/test_context_manager.py
from pathlib import Path
from b1.core.context_manager import setup_context


def _agent_dir(root: Path) -> Path:
    return root / ".agents" / "project"


def test_does_not_create_root_agent_md_when_missing(tmp_path):
    # Root AGENTS.md is now a generated OUTPUT (owned by the translator), not
    # authored by setup_context. If none exists, none should be created here.
    setup_context(tmp_path)
    assert not (tmp_path / "AGENTS.md").exists()


def test_migrates_content_from_existing_root_agent_md_without_marker(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Existing content\n", encoding="utf-8")
    setup_context(tmp_path)
    # Root file is left untouched for the translator to regenerate later.
    root_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert root_content == "# Existing content\n"
    # ...but its content is preserved by migrating it into the project seed.
    project_content = (tmp_path / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Existing content" in project_content


def test_does_not_modify_agent_md_with_marker_already_present(tmp_path):
    original = "# b1CodingTool: Global Context\nAlready configured.\n"
    (tmp_path / "AGENTS.md").write_text(original, encoding="utf-8")
    setup_context(tmp_path)
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == original


def test_creates_project_agent_md(tmp_path):
    setup_context(tmp_path)
    assert (tmp_path / ".agents" / "project" / "AGENTS.md").exists()


def test_project_agent_md_contains_project_context_heading(tmp_path):
    setup_context(tmp_path)
    content = (tmp_path / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Project Context" in content


def test_does_not_overwrite_existing_project_agent_md(tmp_path):
    proj_dir = tmp_path / ".agents" / "project"
    proj_dir.mkdir(parents=True)
    proj_md = proj_dir / "AGENTS.md"
    proj_md.write_text("# Custom project context\n", encoding="utf-8")
    setup_context(tmp_path)
    assert proj_md.read_text(encoding="utf-8") == "# Custom project context\n"


def test_migrates_lowercase_agents_md_to_uppercase(tmp_path):
    def case_sensitive_exists(path: Path) -> bool:
        if not path.exists():
            return False
        return path.name in {p.name for p in path.parent.iterdir()}

    # Pre-create lowercase agents.md files
    (tmp_path / "agents.md").write_text("root context", encoding="utf-8")
    proj_dir = tmp_path / ".agents" / "project"
    proj_dir.mkdir(parents=True)
    (proj_dir / "agents.md").write_text("project context", encoding="utf-8")
    
    setup_context(tmp_path)
    
    # Lowercase files should be renamed/gone
    assert not case_sensitive_exists(tmp_path / "agents.md")
    assert not case_sensitive_exists(proj_dir / "agents.md")
    
    # Uppercase files should exist with their contents
    assert case_sensitive_exists(tmp_path / "AGENTS.md")
    assert case_sensitive_exists(proj_dir / "AGENTS.md")
    
    assert "root context" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "project context" in (proj_dir / "AGENTS.md").read_text(encoding="utf-8")


def test_creates_local_seed(tmp_path):
    (tmp_path / ".agents").mkdir()
    setup_context(tmp_path)
    local_seed = tmp_path / ".agents" / "local" / "AGENTS.md"
    assert local_seed.exists()
    assert "b1CodingTool" in local_seed.read_text(encoding="utf-8")


def test_migrates_existing_root_content_into_project_seed(tmp_path):
    (tmp_path / ".agents").mkdir()
    # user already had authored root content (no b1 marker)
    (tmp_path / "AGENTS.md").write_text("# My Rules\nNever hardcode secrets.", encoding="utf-8")
    setup_context(tmp_path)
    project_seed = (tmp_path / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert "Never hardcode secrets." in project_seed


def test_migration_is_idempotent(tmp_path):
    (tmp_path / ".agents").mkdir()
    # user already had authored root content (no b1 marker)
    (tmp_path / "AGENTS.md").write_text("# My Rules\nNever hardcode secrets.", encoding="utf-8")
    setup_context(tmp_path)
    setup_context(tmp_path)
    project_seed = (tmp_path / ".agents" / "project" / "AGENTS.md").read_text(encoding="utf-8")
    assert project_seed.count("Never hardcode secrets.") == 1

