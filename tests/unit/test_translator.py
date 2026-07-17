# tests/unit/test_translator.py
from b1.core.translator import AgentTranslator
from b1.core.compiled import ContextItem, CompiledContext, SHARED, PERSONAL, PROPRIETARY


def _compiled():
    return CompiledContext([
        ContextItem("Project Context", "Never call prod API in tests.",
                    ".agents/project/AGENTS.md", eager=True, visibility=SHARED),
        ContextItem("Local Context", "Sandbox: http://localhost:9000",
                    ".agents/local/AGENTS.md", eager=True, visibility=PERSONAL),
        ContextItem("react-web: a.md", "public module docs",
                    ".agents/modules/react-web/context/a.md", eager=False, visibility=SHARED),
        ContextItem("llc-react: a.md", "SECRET module docs",
                    ".agents/modules/llc-react/context/a.md", eager=False, visibility=PROPRIETARY),
    ])


def test_root_agents_md_has_shared_eager_and_public_pointers_only(tmp_path):
    AgentTranslator(tmp_path).render_root_agents(_compiled())
    root = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Never call prod API in tests." in root                     # shared eager inlined
    assert ".agents/modules/react-web/context/a.md" in root            # public lazy pointer
    assert "localhost:9000" not in root                                # personal excluded
    assert "llc-react" not in root and "SECRET" not in root            # proprietary excluded


def test_claude_inlines_shared_eager_and_personal_goes_to_local(tmp_path):
    AgentTranslator(tmp_path).render_claude(_compiled())
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    local = (tmp_path / "CLAUDE.local.md").read_text(encoding="utf-8")
    assert "Never call prod API in tests." in claude                   # shared eager inlined
    assert "Sandbox: http://localhost:9000" in local                   # personal -> local file
    assert "Sandbox" not in claude                                     # not in shared CLAUDE.md
    # proprietary lazy content is allowed in gitignored .claude/ filemap
    assert (tmp_path / ".claude" / "context").is_dir()
    # collision fixture: two lazy items share basename "a.md" (react-web vs llc-react)
    # but must land as distinct files in the filemap, not overwrite each other.
    file_a = (tmp_path / ".claude" / "context" / "000_a.md")
    file_b = (tmp_path / ".claude" / "context" / "001_a.md")
    assert file_a.exists() and file_b.exists()
    assert file_a.read_text(encoding="utf-8") != file_b.read_text(encoding="utf-8")


def test_claude_includes_proprietary_eager_but_root_excludes_it(tmp_path):
    compiled = CompiledContext([
        ContextItem("Project Context", "Never call prod API in tests.",
                    ".agents/project/AGENTS.md", eager=True, visibility=SHARED),
        ContextItem("llc-react Capabilities", "Use /llc-widget for glass UI",
                    "", eager=True, visibility=PROPRIETARY),
    ])
    translator = AgentTranslator(tmp_path)
    translator.render_claude(compiled)
    translator.render_root_agents(compiled)

    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    root = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")

    assert "Use /llc-widget for glass UI" in claude                    # proprietary eager inlined into CLAUDE.md
    assert "Use /llc-widget for glass UI" not in root                  # excluded from root AGENTS.md
