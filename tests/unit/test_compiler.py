# tests/unit/test_compiler.py
from b1.core.compiler import ContextCompiler
from b1.core.compiled import SHARED, PERSONAL, PROPRIETARY


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_compile_returns_structured_context(tmp_path):
    _write(tmp_path / ".agents" / "project" / "AGENTS.md", "# Project\nNever call the prod API in tests.")
    _write(tmp_path / ".agents" / "local" / "AGENTS.md", "# Local\nMy sandbox is http://localhost:9000")

    ctx = ContextCompiler(tmp_path).compile()

    project = ctx.filter(visibility=SHARED, eager=True)
    assert any("Never call the prod API" in i.body for i in project)
    personal = ctx.filter(visibility=PERSONAL, eager=True)
    assert any("localhost:9000" in i.body for i in personal)


def test_compile_ignores_root_agents_md(tmp_path):
    _write(tmp_path / "AGENTS.md", "# ROOT OUTPUT — should never be a source")
    _write(tmp_path / ".agents" / "project" / "AGENTS.md", "# Project\nrule")

    ctx = ContextCompiler(tmp_path).compile()

    assert all("ROOT OUTPUT" not in i.body for i in ctx.items)


def test_compile_classifies_proprietary_modules(tmp_path):
    import yaml
    # public module
    pub = tmp_path / ".agents" / "modules" / "react-web"
    (pub / "context").mkdir(parents=True)
    (pub / "b1-module.yaml").write_text(
        yaml.dump({"name": "react-web", "version": "1.0.0", "type": "development"}), encoding="utf-8")
    (pub / "context" / "a.md").write_text("public docs", encoding="utf-8")
    # proprietary module
    prop = tmp_path / ".agents" / "modules" / "llc-react"
    (prop / "context").mkdir(parents=True)
    (prop / "b1-module.yaml").write_text(
        yaml.dump({"name": "llc-react", "version": "1.0.0", "type": "development", "proprietary": True}),
        encoding="utf-8")
    (prop / "context" / "a.md").write_text("secret docs", encoding="utf-8")

    ctx = ContextCompiler(tmp_path).compile()

    shared_lazy = ctx.filter(visibility=SHARED, eager=False)
    prop_lazy = ctx.filter(visibility=PROPRIETARY, eager=False)
    assert any(i.source_path == ".agents/modules/react-web/context/a.md" for i in shared_lazy)
    assert any(i.source_path == ".agents/modules/llc-react/context/a.md" for i in prop_lazy)
    # proprietary content must never be classified shared
    assert all("secret docs" not in i.body for i in ctx.filter(visibility=SHARED))
