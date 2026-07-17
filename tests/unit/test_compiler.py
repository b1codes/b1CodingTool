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


def test_compile_includes_github_metadata(tmp_path):
    from b1.core.config import B1Config

    cfg = B1Config(github_owner="acme", github_repo="app", default_branch="main")
    ctx = ContextCompiler(tmp_path, config=cfg).compile()

    github_items = ctx.filter(visibility=SHARED, eager=True)
    matches = [i for i in github_items if i.title == "GitHub Repository"]
    assert matches
    assert any("github.com/acme/app" in i.body for i in matches)


def test_compile_includes_module_capabilities(tmp_path):
    import yaml

    mod_dir = tmp_path / ".agents" / "modules" / "flutter"
    (mod_dir / "context").mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text(
        yaml.dump({
            "name": "flutter",
            "version": "1.0.0",
            "type": "development",
            "commands": [{"name": "/setup", "description": "d"}],
            "skills": [{"name": "lint", "description": "s"}],
        }),
        encoding="utf-8",
    )

    ctx = ContextCompiler(tmp_path).compile()

    eager_shared = ctx.filter(visibility=SHARED, eager=True)
    matches = [i for i in eager_shared if "/setup" in i.body and "lint" in i.body]
    assert matches


def test_module_without_manifest_compiles_context_as_shared(tmp_path):
    mod_dir = tmp_path / ".agents" / "modules" / "no-manifest"
    (mod_dir / "context").mkdir(parents=True)
    (mod_dir / "context" / "x.md").write_text("plain docs", encoding="utf-8")

    ctx = ContextCompiler(tmp_path).compile()

    matches = [i for i in ctx.items if i.source_path == ".agents/modules/no-manifest/context/x.md"]
    assert matches
    for item in matches:
        assert item.eager is False
        assert item.visibility == SHARED


def test_module_with_unloadable_config_is_treated_proprietary(tmp_path):
    mod_dir = tmp_path / ".agents" / "modules" / "broken-manifest"
    (mod_dir / "context").mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text(":\n  - broken", encoding="utf-8")
    (mod_dir / "context" / "x.md").write_text("mystery docs", encoding="utf-8")

    ctx = ContextCompiler(tmp_path).compile()

    matches = [i for i in ctx.items if i.source_path == ".agents/modules/broken-manifest/context/x.md"
               or i.title.startswith("broken-manifest")]
    assert matches
    for item in matches:
        assert item.visibility == PROPRIETARY
