from b1.core.compiled import (
    ContextItem, CompiledContext, SHARED, PERSONAL, PROPRIETARY,
)


def _items():
    return [
        ContextItem("Project", "rules", ".agents/project/AGENTS.md", eager=True, visibility=SHARED),
        ContextItem("Local", "notes", ".agents/local/AGENTS.md", eager=True, visibility=PERSONAL),
        ContextItem("react-web", "big docs", ".agents/modules/react-web/context/a.md", eager=False, visibility=SHARED),
        ContextItem("llc-react", "secret", ".agents/modules/llc-react/context/a.md", eager=False, visibility=PROPRIETARY),
    ]


def test_filter_by_visibility():
    ctx = CompiledContext(_items())
    assert [i.title for i in ctx.filter(visibility=SHARED)] == ["Project", "react-web"]
    assert [i.title for i in ctx.filter(visibility=PROPRIETARY)] == ["llc-react"]


def test_filter_by_eager():
    ctx = CompiledContext(_items())
    assert [i.title for i in ctx.filter(eager=True)] == ["Project", "Local"]


def test_filter_combined():
    ctx = CompiledContext(_items())
    assert [i.title for i in ctx.filter(visibility=SHARED, eager=False)] == ["react-web"]


def test_is_empty():
    assert CompiledContext([]).is_empty() is True
    assert CompiledContext(_items()).is_empty() is False


def test_render_preview_is_string_covering_all_items():
    from b1.core.compiled import ContextItem, CompiledContext, SHARED, PERSONAL
    ctx = CompiledContext([
        ContextItem("Project", "never push to main", ".agents/project/AGENTS.md", eager=True, visibility=SHARED),
        ContextItem("react-web", "docs", ".agents/modules/react-web/context/a.md", eager=False, visibility=SHARED),
        ContextItem("Local", "my token", ".agents/local/AGENTS.md", eager=True, visibility=PERSONAL),
    ])
    preview = ctx.render_preview()
    assert isinstance(preview, str)
    assert "never push to main" in preview                      # eager body inlined
    assert ".agents/modules/react-web/context/a.md" in preview  # lazy shown as reference
    assert "my token" in preview                                # all visibilities included
