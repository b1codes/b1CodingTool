# Agent File Management — Phase 1 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `AGENTS.md` + `.agents/` into a fully b1-managed multi-agent fan-out where behavioral rules are eager and personal/proprietary content is compiled into each agent's native gitignored vehicle — for Claude Code, Codex, and Antigravity in a single `b1 pair`.

**Architecture:** Replace the fragile "one compiled string with HTML-comment section markers" pipeline with a structured `CompiledContext` (a list of typed `ContextItem`s). The compiler classifies every unit of context by **eager/lazy** and **shared/personal/proprietary**; the translator renders that structure into each agent's native files. Root `AGENTS.md` becomes a **generated output** (no longer an authored source); `GEMINI.md` is dropped.

**Tech Stack:** Python 3.12, Pydantic v2, Typer, Rich, pytest, `uv`.

## Global Constraints

- Run all Python commands from `b1CodingTool/` using `uv` only (never `pip`/`poetry`). Tests: `uv run pytest`.
- Root `AGENTS.md` is a **generated output**, wholesale-regenerated. Never read it as a compile source.
- **Committed `AGENTS.md` contains public + shared content ONLY.** Personal (`visibility="personal"`) and proprietary (`visibility="proprietary"`) content must NEVER be written into it.
- Eager content is always **inlined**, never `@import`-ed (Codex and Antigravity have no reliable import directive).
- Proprietary modules are identified by `ModuleConfig.proprietary == True`.
- Agent name tokens are uppercase: `CLAUDE`, `CODEX`, `ANTIGRAVITY`. `GEMINI` is no longer a supported target.
- Seed filenames are `AGENTS.md` (uppercase) inside `.agents/project/` and `.agents/local/`.

---

## File Structure

**New files:**
- `src/b1/core/compiled.py` — `ContextItem` + `CompiledContext` structured intermediate representation (the compile result). One responsibility: model compiled context and filter it.
- `tests/unit/test_compiled.py` — unit tests for the model.

**Modified files:**
- `src/b1/core/compiler.py` — `ContextCompiler.compile()` returns a `CompiledContext` instead of `str`; reads the new seed hierarchy; classifies items; routes proprietary vs public via `ModuleConfig.proprietary`.
- `src/b1/core/translator.py` — `AgentTranslator.generate_files(agents, compiled)` renders the per-agent matrix from a `CompiledContext`; drops `GEMINI`; emits root `AGENTS.md`, `CLAUDE.md` + `.claude/context/`, `CLAUDE.local.md`, `AGENTS.override.md`, `.agents/rules/local.md`.
- `src/b1/core/context_manager.py` — stop authoring root `AGENTS.md` as a source; create `.agents/local/AGENTS.md` seed; migrate any existing authored root `AGENTS.md` content into `.agents/project/AGENTS.md`.
- `src/b1/core/scaffolder.py` — add the new `.gitignore` entries.
- `src/b1/commands/pair.py` — accept new `CompiledContext`; add `--sync` flag (full matrix regardless of `active_agents`).
- `src/b1/commands/pull.py` — optional `[y/N]` "Re-pair now?" prompt as the last step.

**Out of scope for Phase 1** (own plans later): slash commands `b1 rule` / `b1 edge-case` (Phase 2); drift snapshots + `/b1-reconcile` reverse sync (Phase 3). Until Phase 3 lands, generated files remain disposable (as they are today) and a re-pair overwrites hand-edits — acceptable because every generated file is gitignored; the only committed generated file, root `AGENTS.md`, is documented as "do not edit."

---

### Task 1: `CompiledContext` structured model

**Files:**
- Create: `src/b1/core/compiled.py`
- Test: `tests/unit/test_compiled.py`

**Interfaces:**
- Produces:
  - Constants `SHARED = "shared"`, `PERSONAL = "personal"`, `PROPRIETARY = "proprietary"`.
  - `@dataclass ContextItem(title: str, body: str, source_path: str, eager: bool, visibility: str)`.
  - `@dataclass CompiledContext(items: list[ContextItem])` with `filter(*, visibility: str | None = None, eager: bool | None = None) -> list[ContextItem]` and `is_empty() -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_compiled.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_compiled.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'b1.core.compiled'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/b1/core/compiled.py
from dataclasses import dataclass, field
from typing import List, Optional

SHARED = "shared"
PERSONAL = "personal"
PROPRIETARY = "proprietary"


@dataclass
class ContextItem:
    title: str
    body: str
    source_path: str
    eager: bool
    visibility: str  # SHARED | PERSONAL | PROPRIETARY


@dataclass
class CompiledContext:
    items: List[ContextItem] = field(default_factory=list)

    def filter(
        self,
        *,
        visibility: Optional[str] = None,
        eager: Optional[bool] = None,
    ) -> List[ContextItem]:
        result = []
        for item in self.items:
            if visibility is not None and item.visibility != visibility:
                continue
            if eager is not None and item.eager != eager:
                continue
            result.append(item)
        return result

    def is_empty(self) -> bool:
        return not self.items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_compiled.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/b1/core/compiled.py tests/unit/test_compiled.py
git commit -m "feat(compiler): add CompiledContext structured model"
```

---

### Task 2: Rewrite `ContextCompiler.compile()` to return `CompiledContext`

**Files:**
- Modify: `src/b1/core/compiler.py`
- Test: `tests/unit/test_compiler.py` (add new tests; existing string-based tests will be replaced)

**Interfaces:**
- Consumes: `CompiledContext`, `ContextItem`, `SHARED`, `PERSONAL`, `PROPRIETARY` from `b1.core.compiled` (Task 1); `ModuleConfig` from `b1.core.schema`.
- Produces: `ContextCompiler.compile() -> CompiledContext`. Classification rules:
  - `.agents/project/AGENTS.md` → one `ContextItem(title="Project Context", eager=True, visibility=SHARED)`.
  - `.agents/local/AGENTS.md` → `ContextItem(title="Local Context", eager=True, visibility=PERSONAL)`.
  - GitHub metadata (if configured) → `ContextItem(title="GitHub Repository", eager=True, visibility=SHARED)`.
  - Per module: `visibility = PROPRIETARY if config.proprietary else SHARED`. Capabilities (commands/skills) → `ContextItem(eager=True, visibility=vis)`. Each `context/*.md` → `ContextItem(eager=False, visibility=vis, source_path="<repo-relative>")`.
  - Root `AGENTS.md` is NOT read.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_compiler.py  (append these; keep imports at top of file)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_compiler.py::test_compile_returns_structured_context -v`
Expected: FAIL (compile returns a `str`, so `.filter` raises `AttributeError`)

- [ ] **Step 3: Write the implementation**

Replace the entire body of `src/b1/core/compiler.py` with:

```python
from pathlib import Path
from typing import List, Optional
from rich.console import Console

from b1.core.config import B1Config
from b1.core.schema import ModuleConfig
from b1.core.compiled import ContextItem, CompiledContext, SHARED, PERSONAL, PROPRIETARY

console = Console()


class ContextCompiler:
    def __init__(self, project_dir: Path, config: Optional[B1Config] = None):
        self.project_dir = project_dir
        self.config = config

    def compile(self) -> CompiledContext:
        items: List[ContextItem] = []

        # 0. GitHub metadata (eager, shared)
        if self.config and self.config.github_owner and self.config.github_repo:
            lines = [
                "# GitHub Repository",
                f"- URL: https://github.com/{self.config.github_owner}/{self.config.github_repo}",
            ]
            if self.config.default_branch:
                lines.append(f"- Default Branch: {self.config.default_branch}")
            items.append(ContextItem(
                title="GitHub Repository", body="\n".join(lines),
                source_path="", eager=True, visibility=SHARED,
            ))

        # 1. Shared project seed (eager, shared)
        project_seed = self.project_dir / ".agents" / "project" / "AGENTS.md"
        if project_seed.exists():
            items.append(ContextItem(
                title="Project Context",
                body=project_seed.read_text(encoding="utf-8").strip(),
                source_path=".agents/project/AGENTS.md",
                eager=True, visibility=SHARED,
            ))

        # 2. Personal local seed (eager, personal)
        local_seed = self.project_dir / ".agents" / "local" / "AGENTS.md"
        if local_seed.exists():
            items.append(ContextItem(
                title="Local Context",
                body=local_seed.read_text(encoding="utf-8").strip(),
                source_path=".agents/local/AGENTS.md",
                eager=True, visibility=PERSONAL,
            ))

        # 3. Modules (capabilities eager; context files lazy). Visibility by proprietary flag.
        modules_dir = self.project_dir / ".agents" / "modules"
        if modules_dir.exists():
            for mod in sorted([d for d in modules_dir.iterdir() if d.is_dir()], key=lambda p: p.name):
                items.extend(self._compile_module(mod))

        return CompiledContext(items)

    def _compile_module(self, mod: Path) -> List[ContextItem]:
        out: List[ContextItem] = []
        config_path = mod / "b1-module.yaml"
        if not config_path.exists():
            config_path = mod / "module.yaml"

        visibility = SHARED
        mod_config: Optional[ModuleConfig] = None
        if config_path.exists():
            try:
                mod_config = ModuleConfig.from_yaml(config_path)
                visibility = PROPRIETARY if mod_config.proprietary else SHARED
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config for module {mod.name}: {e}[/yellow]")

        # Capabilities (commands/skills) -> eager
        if mod_config and (mod_config.commands or mod_config.skills):
            lines = [f"### {mod.name} Capabilities", ""]
            if mod_config.commands:
                lines.append("#### Commands")
                for cmd in mod_config.commands:
                    lines.append(f"- `{cmd.name}`: {cmd.description}")
                lines.append("")
            if mod_config.skills:
                lines.append("#### Skills")
                for skill in mod_config.skills:
                    lines.append(f"- **{skill.name}**: {skill.description}")
                lines.append("")
            out.append(ContextItem(
                title=f"{mod.name} Capabilities", body="\n".join(lines).strip(),
                source_path="", eager=True, visibility=visibility,
            ))

        # Context files -> lazy pointers
        context_dir = mod / "context"
        if context_dir.exists():
            for md_file in sorted(context_dir.glob("*.md")):
                rel = md_file.relative_to(self.project_dir).as_posix()
                out.append(ContextItem(
                    title=f"{mod.name}: {md_file.name}",
                    body=md_file.read_text(encoding="utf-8").strip(),
                    source_path=rel, eager=False, visibility=visibility,
                ))
        return out
```

- [ ] **Step 4: Delete obsolete string-based compiler tests**

Open `tests/unit/test_compiler.py` and remove any existing tests that assert on the old string return value or on `<!-- b1CodingTool: ... -->` markers (e.g. tests calling `compile()` and doing `assert "..." in result` on a string). The three new tests replace them.

Run: `uv run pytest tests/unit/test_compiler.py -v`
Expected: PASS (3 passed — the new tests; no failures from removed legacy tests)

- [ ] **Step 5: Commit**

```bash
git add src/b1/core/compiler.py tests/unit/test_compiler.py
git commit -m "feat(compiler): return CompiledContext; classify eager/lazy and shared/personal/proprietary"
```

---

### Task 3: `b1 init` — local seed, gitignore, agnostic migration

**Files:**
- Modify: `src/b1/core/context_manager.py`
- Modify: `src/b1/core/scaffolder.py:6-14` (GITIGNORE_CONTENT)
- Test: `tests/unit/test_context_manager.py` (add tests), `tests/unit/test_scaffolder.py` (add test)

**Interfaces:**
- Consumes: nothing new.
- Produces: after `setup_context(root_dir)`:
  - `.agents/local/AGENTS.md` exists (personal seed) if absent.
  - If a pre-existing root `AGENTS.md` held user content, it has been appended into `.agents/project/AGENTS.md` and the root file is left for the translator to regenerate.
  - `.gitignore` (from scaffold) contains the Phase-1 generated-file entries.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_context_manager.py  (append)
from b1.core.context_manager import setup_context


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
```

```python
# tests/unit/test_scaffolder.py  (append)
from b1.core.scaffolder import scaffold_project


def test_gitignore_has_generated_entries(tmp_path):
    scaffold_project(tmp_path)
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    for entry in ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.override.md",
                  ".claude/", ".agents/local/", ".agents/rules/local.md"]:
        assert entry in gitignore
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_context_manager.py::test_creates_local_seed tests/unit/test_scaffolder.py::test_gitignore_has_generated_entries -v`
Expected: FAIL (`.agents/local/AGENTS.md` not created; gitignore missing entries)

- [ ] **Step 3: Implement the gitignore entries**

In `src/b1/core/scaffolder.py`, replace `GITIGNORE_CONTENT` (lines 6-14) with:

```python
GITIGNORE_CONTENT = """# Python
__pycache__/
*.pyc
.venv/
.env

# b1CodingTool generated agent files
CLAUDE.md
CLAUDE.local.md
AGENTS.override.md
.claude/
.agents/local/
.agents/rules/local.md
"""
```

- [ ] **Step 4: Implement the local seed + migration**

In `src/b1/core/context_manager.py`, add a `LOCAL_AGENT_MD` constant after `PROJECT_AGENT_MD` (line 24):

```python
LOCAL_AGENT_MD = """# b1CodingTool: Local Context (personal, gitignored)
Personal, machine-specific notes and overrides. Not committed; compiled only into
your local agent files (CLAUDE.local.md, AGENTS.override.md, .agents/rules/local.md).

## Guardrails

## Edge cases
"""
```

Then, inside `setup_context`, replace the "Root AGENTS.md handling" block (lines 45-56) with a **migration** block, and add local-seed creation at the end. The new root-handling block:

```python
    # Root AGENTS.md is now a GENERATED OUTPUT. If a user authored one, migrate
    # its content into the shared project seed so nothing is lost, then leave the
    # root file for the translator to regenerate.
    project_agent_dir.mkdir(parents=True, exist_ok=True)
    if case_sensitive_exists(root_agent_path):
        root_content = root_agent_path.read_text(encoding="utf-8")
        is_generated = "AUTO-GENERATED BY b1CodingTool" in root_content
        if not is_generated and "b1CodingTool" not in root_content:
            existing_project = ""
            if case_sensitive_exists(project_agent_path):
                existing_project = project_agent_path.read_text(encoding="utf-8")
            merged = (existing_project.rstrip() + "\n\n" + root_content.strip() + "\n").lstrip()
            project_agent_path.write_text(merged, encoding="utf-8")
            console.print("[yellow]Migrated existing root AGENTS.md content into .agents/project/AGENTS.md.[/yellow]")
```

Delete the old `else:` branch that wrote `BASE_AGENT_MD` to the root path (root is no longer authored here). Keep the lowercase→uppercase migration for `agents.md` at the top of the function unchanged.

At the **end** of `setup_context`, add:

```python
    # Personal local seed (gitignored)
    local_agent_dir = root_dir / ".agents" / "local"
    local_agent_dir.mkdir(parents=True, exist_ok=True)
    local_agent_path = local_agent_dir / "AGENTS.md"
    if not case_sensitive_exists(local_agent_path):
        local_agent_path.write_text(LOCAL_AGENT_MD, encoding="utf-8")
        console.print("[green]Created personal local seed in .agents/local/AGENTS.md.[/green]")
    else:
        console.print("[dim]Personal local seed already exists, skipping.[/dim]")
```

The `BASE_AGENT_MD` constant is now unused; delete it (lines 6-13).

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_context_manager.py tests/unit/test_scaffolder.py -v`
Expected: PASS (existing tests may need the removed `BASE_AGENT_MD`/root-authoring assertions deleted — remove any test asserting root `AGENTS.md` is authored with `BASE_AGENT_MD`).

- [ ] **Step 6: Commit**

```bash
git add src/b1/core/context_manager.py src/b1/core/scaffolder.py tests/unit/test_context_manager.py tests/unit/test_scaffolder.py
git commit -m "feat(init): create local seed, migrate agnostic root content, gitignore generated files"
```

---

### Task 4: Rewrite `AgentTranslator` — shared outputs (root `AGENTS.md` + Claude)

**Files:**
- Modify: `src/b1/core/translator.py`
- Test: `tests/unit/test_translator.py` (replace legacy tests)

**Interfaces:**
- Consumes: `CompiledContext`, `SHARED`, `PERSONAL`, `PROPRIETARY` (Task 1); `compile()` returns `CompiledContext` (Task 2).
- Produces:
  - `AgentTranslator.generate_files(agents: list[str], compiled: CompiledContext) -> None`.
  - `AgentTranslator.render_root_agents(compiled) -> None` — writes `AGENTS.md` (shared eager inline + public lazy pointers; excludes personal + proprietary).
  - `AgentTranslator.render_claude(compiled) -> None` — writes `CLAUDE.md` (shared eager inline + filemap of ALL lazy pointers copied into `.claude/context/`) and `CLAUDE.local.md` (personal eager inline).
  - Helper `_pointer_line(item) -> str` → `- [{title}]({source_path})`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_translator.py  (replace file contents)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_translator.py -v`
Expected: FAIL (`render_root_agents` / `render_claude` do not exist)

- [ ] **Step 3: Write the implementation**

Replace the entire body of `src/b1/core/translator.py` with (this task adds root + Claude renderers and the dispatcher; Task 5 adds Codex + Antigravity renderers to the same class):

```python
import shutil
from pathlib import Path
from rich.console import Console

from b1.core.compiled import CompiledContext, ContextItem, SHARED, PERSONAL, PROPRIETARY

console = Console()

HEADER = "<!-- AUTO-GENERATED BY b1CodingTool (b1 pair). DO NOT EDIT DIRECTLY. -->\n\n"


class AgentTranslator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def generate_files(self, agents: list[str], compiled: CompiledContext):
        # Root AGENTS.md is the universal native file — always rendered.
        self.render_root_agents(compiled)

        upper = {a.upper() for a in agents}
        if "CLAUDE" in upper:
            self.render_claude(compiled)
        # Codex + Antigravity renderers are added in Task 5.
        if "CODEX" in upper:
            self.render_codex(compiled)
        if "ANTIGRAVITY" in upper:
            self.render_antigravity(compiled)

        self._ensure_gitignore()

    # ---- helpers ----

    def _pointer_line(self, item: ContextItem) -> str:
        return f"- [{item.title}]({item.source_path})"

    def _inline_block(self, item: ContextItem) -> str:
        return f"## {item.title}\n\n{item.body}\n"

    # ---- shared / root ----

    def render_root_agents(self, compiled: CompiledContext):
        parts = [HEADER, "# AGENTS.md\n"]
        eager = compiled.filter(visibility=SHARED, eager=True)
        for item in eager:
            parts.append("\n" + self._inline_block(item))
        lazy = compiled.filter(visibility=SHARED, eager=False)
        if lazy:
            parts.append("\n## Reference (read on demand)\n\n")
            parts.extend(self._pointer_line(i) + "\n" for i in lazy)
        (self.project_dir / "AGENTS.md").write_text("".join(parts), encoding="utf-8")
        console.print("[green]✔ Generated:[/green] AGENTS.md")

    # ---- Claude ----

    def render_claude(self, compiled: CompiledContext):
        context_dir = self.project_dir / ".claude" / "context"
        if context_dir.exists():
            shutil.rmtree(context_dir)
        context_dir.mkdir(parents=True, exist_ok=True)

        parts = [HEADER, "# CLAUDE.md\n"]
        for item in compiled.filter(visibility=SHARED, eager=True):
            parts.append("\n" + self._inline_block(item))

        # All lazy items (public + proprietary) -> copies in gitignored .claude/context,
        # linked as a filemap. .claude/ is gitignored so proprietary content is safe here.
        lazy = [i for i in compiled.items if not i.eager and i.visibility in (SHARED, PROPRIETARY)]
        if lazy:
            parts.append("\n## Reference (read on demand)\n\n")
            for idx, item in enumerate(lazy):
                fname = f"{idx:03d}_{Path(item.source_path).name}"
                (context_dir / fname).write_text(item.body, encoding="utf-8")
                parts.append(f"- [{item.title}](.claude/context/{fname})\n")

        (self.project_dir / "CLAUDE.md").write_text("".join(parts), encoding="utf-8")

        personal = compiled.filter(visibility=PERSONAL, eager=True)
        local_parts = [HEADER, "# CLAUDE.local.md (personal)\n"]
        for item in personal:
            local_parts.append("\n" + self._inline_block(item))
        (self.project_dir / "CLAUDE.local.md").write_text("".join(local_parts), encoding="utf-8")
        console.print("[green]✔ Generated:[/green] CLAUDE.md, CLAUDE.local.md, .claude/context/")

    def render_codex(self, compiled: CompiledContext):
        raise NotImplementedError  # implemented in Task 5

    def render_antigravity(self, compiled: CompiledContext):
        raise NotImplementedError  # implemented in Task 5

    def _ensure_gitignore(self):
        gitignore = self.project_dir / ".gitignore"
        entries = ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.override.md",
                   ".claude/", ".agents/local/", ".agents/rules/local.md"]
        existing = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
        missing = [e for e in entries if e not in existing]
        if missing:
            with open(gitignore, "a", encoding="utf-8") as f:
                if existing and existing[-1].strip():
                    f.write("\n")
                if "# b1CodingTool generated agent files" not in existing:
                    f.write("# b1CodingTool generated agent files\n")
                for e in missing:
                    f.write(e + "\n")
```

- [ ] **Step 4: Delete obsolete translator tests**

In `tests/unit/test_translator.py` you already replaced the file in Step 1. Also check `tests/unit/test_translator_dart.py` — if it asserts the old GEMINI preamble or `<tag>`-wrapped output or the old `generate_files(agents, str)` signature, update it to call `generate_files(agents, CompiledContext([...]))` or delete the assertions that no longer hold. Run:

Run: `uv run pytest tests/unit/test_translator.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/b1/core/translator.py tests/unit/test_translator.py tests/unit/test_translator_dart.py
git commit -m "feat(translator): render root AGENTS.md + Claude from CompiledContext; drop GEMINI"
```

---

### Task 5: `AgentTranslator` — Codex + Antigravity personal/proprietary outputs

**Files:**
- Modify: `src/b1/core/translator.py` (replace the two `NotImplementedError` stubs)
- Test: `tests/unit/test_translator.py` (add tests)

**Interfaces:**
- Consumes: `render_codex` / `render_antigravity` stubs from Task 4; the `_inline_block` / `_pointer_line` helpers.
- Produces:
  - `render_codex(compiled)` → writes `AGENTS.override.md` = personal eager inline + proprietary lazy pointers (to real `.agents/modules/...` paths). Skips writing (and removes any stale file) when there is no personal or proprietary content.
  - `render_antigravity(compiled)` → writes `.agents/rules/local.md` = personal eager inline + proprietary lazy pointers. Same skip/remove behavior.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_translator.py  (append; reuse _compiled from Task 4)
def test_codex_override_has_personal_and_proprietary_only(tmp_path):
    AgentTranslator(tmp_path).render_codex(_compiled())
    override = (tmp_path / "AGENTS.override.md").read_text(encoding="utf-8")
    assert "Sandbox: http://localhost:9000" in override                # personal
    assert ".agents/modules/llc-react/context/a.md" in override        # proprietary pointer
    assert "Never call prod API" not in override                       # shared stays in root AGENTS.md
    assert "react-web" not in override                                 # public stays in root AGENTS.md


def test_antigravity_local_rules_file(tmp_path):
    AgentTranslator(tmp_path).render_antigravity(_compiled())
    rules = (tmp_path / ".agents" / "rules" / "local.md").read_text(encoding="utf-8")
    assert "Sandbox: http://localhost:9000" in rules
    assert ".agents/modules/llc-react/context/a.md" in rules


def test_codex_skips_when_no_personal_or_proprietary(tmp_path):
    empty = CompiledContext([
        ContextItem("Project Context", "rule", ".agents/project/AGENTS.md", eager=True, visibility=SHARED),
    ])
    AgentTranslator(tmp_path).render_codex(empty)
    assert not (tmp_path / "AGENTS.override.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_translator.py::test_codex_override_has_personal_and_proprietary_only -v`
Expected: FAIL with `NotImplementedError`

- [ ] **Step 3: Implement the two renderers**

In `src/b1/core/translator.py`, replace the `render_codex` and `render_antigravity` stubs with:

```python
    def _render_personal_vehicle(self, compiled: CompiledContext, out_path: Path, title: str):
        personal = compiled.filter(visibility=PERSONAL, eager=True)
        proprietary_lazy = compiled.filter(visibility=PROPRIETARY, eager=False)
        proprietary_eager = compiled.filter(visibility=PROPRIETARY, eager=True)
        if not personal and not proprietary_lazy and not proprietary_eager:
            if out_path.exists():
                out_path.unlink()
            return
        parts = [HEADER, f"# {title}\n"]
        for item in personal:
            parts.append("\n" + self._inline_block(item))
        for item in proprietary_eager:
            parts.append("\n" + self._inline_block(item))
        if proprietary_lazy:
            parts.append("\n## Proprietary reference (read on demand)\n\n")
            parts.extend(self._pointer_line(i) + "\n" for i in proprietary_lazy)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(parts), encoding="utf-8")
        console.print(f"[green]✔ Generated:[/green] {out_path.relative_to(self.project_dir)}")

    def render_codex(self, compiled: CompiledContext):
        self._render_personal_vehicle(
            compiled, self.project_dir / "AGENTS.override.md", "AGENTS.override.md (personal)")

    def render_antigravity(self, compiled: CompiledContext):
        self._render_personal_vehicle(
            compiled, self.project_dir / ".agents" / "rules" / "local.md", "Local rules (personal)")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_translator.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/b1/core/translator.py tests/unit/test_translator.py
git commit -m "feat(translator): render Codex AGENTS.override.md and Antigravity .agents/rules/local.md"
```

---

### Task 6: Wire `b1 pair` to the new pipeline + `--sync` flag

**Files:**
- Modify: `src/b1/commands/pair.py`
- Test: `tests/integration/test_pair_cmd.py` (add tests)

**Interfaces:**
- Consumes: `ContextCompiler.compile() -> CompiledContext` (Task 2); `AgentTranslator.generate_files(agents, compiled)` (Tasks 4–5).
- Produces: `pair_cmd(sync: bool = False)`. When `sync=True`, generate the full matrix `["CLAUDE", "CODEX", "ANTIGRAVITY"]` regardless of `active_agents`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_pair_cmd.py  (append)
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def test_pair_sync_generates_full_matrix(make_project):
    project = make_project(agents=["CLAUDE"])
    (project / ".agents" / "project" / "AGENTS.md").write_text("# Project\nNever push to main.", encoding="utf-8")
    (project / ".agents" / "local" / "AGENTS.md").parent.mkdir(parents=True, exist_ok=True)
    (project / ".agents" / "local" / "AGENTS.md").write_text("# Local\nMy token is in .env.local", encoding="utf-8")

    import os
    cwd = os.getcwd()
    os.chdir(project)
    try:
        result = runner.invoke(app, ["pair", "--sync"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert (project / "AGENTS.md").exists()                 # root output
    assert (project / "CLAUDE.md").exists()
    assert (project / "CLAUDE.local.md").exists()
    assert (project / "AGENTS.override.md").exists()        # Codex personal (has local content)
    assert (project / ".agents" / "rules" / "local.md").exists()  # Antigravity personal
    assert "Never push to main." in (project / "AGENTS.md").read_text(encoding="utf-8")
```

> If the `make_project` fixture does not yet create `.agents/local/`, add that directory to the fixture in `tests/conftest.py` (one line: `(project_dir / ".agents" / "local").mkdir(parents=True, exist_ok=True)`).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_pair_cmd.py::test_pair_sync_generates_full_matrix -v`
Expected: FAIL (`--sync` is not a known option; or old translator signature errors)

- [ ] **Step 3: Update `pair_cmd`**

Replace `src/b1/commands/pair.py` `pair_cmd` signature and body core with:

```python
import typer
from typing import Annotated
from pathlib import Path
from rich.console import Console

from b1.core.config import B1Config
from b1.core.compiler import ContextCompiler
from b1.core.translator import AgentTranslator
from b1.core.hook_engine import HookEngine

console = Console()

FULL_MATRIX = ["CLAUDE", "CODEX", "ANTIGRAVITY"]


def pair_cmd(
    sync: Annotated[bool, typer.Option("--sync", help="Regenerate the full agent matrix (Claude, Codex, Antigravity) regardless of active_agents.")] = False,
):
    """Compile the .agents/ sources into each agent's native files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    config = B1Config.load(project_dir)
    hook_engine = HookEngine(project_dir)

    if sync:
        agents = FULL_MATRIX
    else:
        if not config.active_agents:
            agent_input = typer.prompt(
                "Which agents do you want to target? (comma separated: CLAUDE,CODEX,ANTIGRAVITY)",
                default="CLAUDE,CODEX,ANTIGRAVITY",
            )
            agents = [a.strip().upper() for a in agent_input.split(",") if a.strip()]
            config.active_agents = agents
            config.save(project_dir)
        else:
            agents = config.active_agents

    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)

    console.print("[bold blue]Compiling contexts...[/bold blue]")
    hook_engine.run_hooks("pre-pair")
    compiled = compiler.compile()
    if compiled.is_empty():
        console.print("[yellow]No context found to compile.[/yellow]")
        return
    console.print(f"[blue]Writing configurations for:[/blue] {', '.join(agents)}")
    translator.generate_files(agents, compiled)
    hook_engine.run_hooks("post-pair")
    console.print("\n[bold green]Cross-agent parity synchronization complete![/bold green] \U0001f504")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_pair_cmd.py -v`
Expected: PASS. Fix any legacy assertions in this file that expected `GEMINI.md` or the old filemap-only `CLAUDE.md`.

- [ ] **Step 5: Commit**

```bash
git add src/b1/commands/pair.py tests/integration/test_pair_cmd.py tests/conftest.py
git commit -m "feat(pair): wire CompiledContext pipeline and add --sync full-matrix flag"
```

---

### Task 7: `b1 pull` — optional re-pair prompt

**Files:**
- Modify: `src/b1/commands/pull.py`
- Test: `tests/integration/test_pull_cmd.py` (add test)

**Interfaces:**
- Consumes: `pair_cmd` from `b1.commands.pair` (Task 6).
- Produces: after a successful pull, prompt `Re-pair now to apply updates? [y/N]`; on `y`, call `pair_cmd(sync=False)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_pull_cmd.py  (append)
from unittest.mock import patch
from typer.testing import CliRunner
from b1.cli import app

runner = CliRunner()


def test_pull_offers_repair_and_runs_it_on_yes(make_project):
    project = make_project(agents=["CLAUDE"])
    import os
    cwd = os.getcwd()
    os.chdir(project)
    try:
        with patch("b1.commands.pull.pair_cmd") as mock_pair:
            result = runner.invoke(app, ["pull"], input="y\n")
    finally:
        os.chdir(cwd)
    assert result.exit_code == 0
    mock_pair.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_pull_cmd.py::test_pull_offers_repair_and_runs_it_on_yes -v`
Expected: FAIL (no prompt / `pair_cmd` never called)

- [ ] **Step 3: Implement the prompt**

In `src/b1/commands/pull.py`, add the import at the top:

```python
from b1.commands.pair import pair_cmd
```

At the very end of `pull_cmd`, after the existing `console.print("\\n[bold green]Pull sync complete![/bold green]")`, add:

```python
    if typer.confirm("Re-pair now to apply updates?", default=False):
        pair_cmd(sync=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_pull_cmd.py -v`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest`
Expected: PASS. Address any remaining legacy tests referencing `GEMINI.md`, the old `compile() -> str` return, or `<!-- b1CodingTool: -->` markers by updating them to the new structured pipeline.

- [ ] **Step 6: Commit**

```bash
git add src/b1/commands/pull.py tests/integration/test_pull_cmd.py
git commit -m "feat(pull): offer optional re-pair after fetching module updates"
```

---

## Subsequent Phases (own plans after Phase 1 lands)

- **Phase 2 — Slash commands:** `b1 rule` (centerpiece) and `b1 edge-case` CLI subcommands writing to `.agents/project/AGENTS.md` or `.agents/local/AGENTS.md` (scope param; edge-case prompts when omitted), plus per-agent shims (`.claude/commands/`, Antigravity `.agents/skills/`; Codex = CLI fallback / Skill shim TBD). Each ends by invoking the compile.
- **Phase 3 — Drift safety + reverse sync:** per-file snapshots written on every generate (under `.agents/.b1-snapshots/`, gitignored); a drift-halt guard in every write path (`pair`, `pull`, `--sync`) that refuses to overwrite a hand-edited generated file; and the `/b1-reconcile` guided skill that promotes hand-edits back into the seeds.

---

## Self-Review

**Spec coverage (Phase 1 scope):**
- §4 seeds (`.agents/local/AGENTS.md`, gitignore, agnostic fold+migrate) → Task 3. ✅
- §5 fan-out matrix (root `AGENTS.md` output; Claude; Codex `AGENTS.override.md`; Antigravity `.agents/rules/local.md`; GEMINI dropped; public/proprietary routing) → Tasks 2, 4, 5. ✅
- §5 `--sync` full matrix → Task 6. ✅
- §8 `pull` → optional re-pair → Task 7. ✅
- Eager-inline / lazy-pointer split; personal & proprietary excluded from committed root → Tasks 2, 4 (tests assert exclusion). ✅
- §6 slash commands, §7 drift/reverse-sync → deferred to Phases 2–3 (explicitly out of scope). ✅

**Placeholder scan:** No "TBD/TODO/handle edge cases" in Phase 1 tasks. Codex shim TBD is confined to the Phase 2 outline, not a Phase 1 task. ✅

**Type consistency:** `compile() -> CompiledContext` (Task 2) consumed by `generate_files(agents, compiled)` (Tasks 4–6). `ContextItem(title, body, source_path, eager, visibility)` field order identical across all tasks. `render_root_agents` / `render_claude` / `render_codex` / `render_antigravity` names consistent between Tasks 4 and 5. `pair_cmd(sync)` (Task 6) consumed by `pull` (Task 7). ✅
