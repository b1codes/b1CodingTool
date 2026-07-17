from b1.core.translator import AgentTranslator
from b1.core.compiled import ContextItem, CompiledContext, SHARED


def _compiled_dart():
    return CompiledContext([
        ContextItem("dart: conventions.md", "# Dart Rules\nUse camelCase.",
                    ".agents/modules/dart/context/conventions.md", eager=False, visibility=SHARED),
    ])


def test_claude_dart_context_lazy_item_copied_to_filemap(tmp_path):
    AgentTranslator(tmp_path).generate_files(["CLAUDE"], _compiled_dart())

    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "dart: conventions.md" in claude

    context_dir = tmp_path / ".claude" / "context"
    assert context_dir.is_dir()
    copied = list(context_dir.glob("*conventions.md"))
    assert len(copied) == 1
    assert "Use camelCase." in copied[0].read_text(encoding="utf-8")
