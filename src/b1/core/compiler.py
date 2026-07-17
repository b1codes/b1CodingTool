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
        """
        Build the structured project context from source files.

        Reads `.agents/project/AGENTS.md` (eager, SHARED), `.agents/local/AGENTS.md`
        (eager, PERSONAL), configured GitHub metadata (eager, SHARED), and each
        installed module under `.agents/modules/*` — module capabilities are eager
        pointers and each `context/*.md` file is a lazy pointer, with visibility
        (SHARED vs PROPRIETARY) determined by the module's `proprietary` flag.

        Root `AGENTS.md` is NEVER read here: it is a generated OUTPUT produced from
        this compiled context (by the translator), not a source of it.

        Returns a `CompiledContext` (a list of typed `ContextItem`s), not a string.
        """
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
                # Fail-safe: an unreadable/unknown manifest must never be treated as
                # SHARED — assume the worst (PROPRIETARY) so broken metadata can't
                # leak module content into committed/shared outputs.
                visibility = PROPRIETARY
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
