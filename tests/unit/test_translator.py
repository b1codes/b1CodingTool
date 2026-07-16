# tests/unit/test_translator.py
from pathlib import Path
from b1.core.translator import AgentTranslator

COMPILED = """
<!-- b1CodingTool: Root Context -->
# Global Context
Some content here.

<!-- b1CodingTool: Project Context -->
# Project specific
App logic.

<!-- b1CodingTool: Module Capabilities [fastapi] -->
Fastapi capabilities here.

<!-- b1CodingTool: Module Context [react-native] - SKILL.md -->
React native skill content here.
"""


def test_generates_filemap_and_hidden_dirs(tmp_path):
    AgentTranslator(tmp_path).generate_files(["CLAUDE", "GEMINI"], COMPILED)
    
    # Root filemaps should exist
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "GEMINI.md").exists()
    
    # Hidden dirs should exist
    assert (tmp_path / ".claude" / "context").is_dir()
    assert (tmp_path / ".gemini" / "context").is_dir()
    
    # Module subdirectories should exist
    assert (tmp_path / ".claude" / "context" / "fastapi").is_dir()
    assert (tmp_path / ".claude" / "context" / "react-native").is_dir()
    
    # Individual context files should exist
    assert (tmp_path / ".claude" / "context" / "root_context.md").exists()
    assert (tmp_path / ".claude" / "context" / "project_context.md").exists()
    assert (tmp_path / ".claude" / "context" / "fastapi" / "capabilities.md").exists()
    assert (tmp_path / ".claude" / "context" / "react-native" / "SKILL.md").exists()
    
    assert (tmp_path / ".gemini" / "context" / "root_context.md").exists()
    assert (tmp_path / ".gemini" / "context" / "project_context.md").exists()
    assert (tmp_path / ".gemini" / "context" / "fastapi" / "capabilities.md").exists()
    assert (tmp_path / ".gemini" / "context" / "react-native" / "SKILL.md").exists()



def test_claude_filemap_and_content(tmp_path):
    AgentTranslator(tmp_path).generate_files(["CLAUDE"], COMPILED)
    
    # Filemap check
    root_content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert ".claude/context/root_context.md" in root_content
    assert ".claude/context/project_context.md" in root_content
    assert ".claude/context/fastapi/capabilities.md" in root_content
    assert ".claude/context/react-native/SKILL.md" in root_content
    assert "instructions" in root_content.lower() or "read" in root_content.lower()
    
    # Content check
    section_content = (tmp_path / ".claude" / "context" / "root_context.md").read_text(encoding="utf-8")
    assert "<root_context>" in section_content
    assert "# Global Context" in section_content

    # Module content check
    react_native_content = (tmp_path / ".claude" / "context" / "react-native" / "SKILL.md").read_text(encoding="utf-8")
    assert "<module_context_react_native___skill_md>" in react_native_content
    assert "React native skill content here." in react_native_content


def test_gemini_filemap_and_content(tmp_path):
    AgentTranslator(tmp_path).generate_files(["GEMINI"], COMPILED)
    
    # Filemap check
    root_content = (tmp_path / "GEMINI.md").read_text(encoding="utf-8")
    assert ".gemini/context/root_context.md" in root_content
    assert ".gemini/context/project_context.md" in root_content
    
    # Content check
    section_content = (tmp_path / ".gemini" / "context" / "root_context.md").read_text(encoding="utf-8")
    assert "You are a Gemini CLI agent" in section_content
    assert "## Root Context" in section_content


def test_gitignore_is_updated(tmp_path):
    # Pre-create gitignore with existing stuff
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("node_modules/\n", encoding="utf-8")
    
    AgentTranslator(tmp_path).generate_files(["CLAUDE", "GEMINI"], COMPILED)
    
    content = gitignore.read_text(encoding="utf-8")
    assert "CLAUDE.md" in content
    assert "GEMINI.md" in content
    assert ".claude/" in content
    assert ".gemini/" in content
    assert "node_modules/" in content  # untouched
    
def test_gitignore_creates_if_not_exists(tmp_path):
    AgentTranslator(tmp_path).generate_files(["CLAUDE"], COMPILED)
    
    gitignore = tmp_path / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    assert "CLAUDE.md" in content
    assert ".claude/" in content
