# tests/unit/test_scaffolder.py
from pathlib import Path
from b1.core.scaffolder import scaffold_project


def test_creates_agent_directory(tmp_path):
    scaffold_project(tmp_path)
    assert (tmp_path / ".agents").is_dir()


def test_creates_docs_directory(tmp_path):
    scaffold_project(tmp_path)
    assert (tmp_path / "docs").is_dir()


def test_creates_gitignore(tmp_path):
    scaffold_project(tmp_path)
    assert (tmp_path / ".gitignore").exists()


def test_gitignore_contains_python_entries(tmp_path):
    scaffold_project(tmp_path)
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in content
    assert ".venv/" in content


def test_creates_readme(tmp_path):
    scaffold_project(tmp_path)
    assert (tmp_path / "README.md").exists()


def test_is_idempotent_does_not_overwrite_existing_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("custom content", encoding="utf-8")
    scaffold_project(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "custom content"


def test_is_idempotent_does_not_overwrite_existing_readme(tmp_path):
    (tmp_path / "README.md").write_text("# My Project", encoding="utf-8")
    scaffold_project(tmp_path)
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "# My Project"


def test_safe_to_call_twice(tmp_path):
    scaffold_project(tmp_path)
    scaffold_project(tmp_path)  # should not raise
    assert (tmp_path / ".agents").is_dir()


def test_gitignore_has_generated_entries(tmp_path):
    scaffold_project(tmp_path)
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    for entry in ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.override.md",
                  ".claude/", ".agents/local/", ".agents/rules/local.md"]:
        assert entry in gitignore
