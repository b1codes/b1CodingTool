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
