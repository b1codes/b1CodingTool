from pathlib import Path
from typing import List, Optional
from rich.console import Console

from b1.core.config import B1Config
from b1.core.schema import ModuleConfig

console = Console()

class ContextCompiler:
    def __init__(self, project_dir: Path, config: Optional[B1Config] = None):
        self.project_dir = project_dir
        self.config = config
        
    def compile(self) -> str:
        """
        Gathers content from the root agents.md, project-specific agents.md, 
        and module context files to form a unified document.
        """
        combined = []
        
        # 0. GitHub Metadata
        if self.config and self.config.github_owner and self.config.github_repo:
            combined.append("<!-- b1CodingTool: GitHub Repository -->\n")
            combined.append("# GitHub Repository\n")
            combined.append(f"- URL: https://github.com/{self.config.github_owner}/{self.config.github_repo}\n")
            if self.config.default_branch:
                combined.append(f"- Default Branch: {self.config.default_branch}\n")
            combined.append("\n\n")

        # 1. Root AGENTS.md / agents.md
        root_agent = self.project_dir / "AGENTS.md"
        if not root_agent.exists():
            root_agent = self.project_dir / "agents.md"
            
        if root_agent.exists():
            combined.append("<!-- b1CodingTool: Root Context -->\n")
            content = root_agent.read_text(encoding="utf-8").strip()
            # Strip auto-generated section if present
            start_marker = "<!-- b1CodingTool: start -->"
            if start_marker in content:
                content = content.split(start_marker)[0].strip()
            combined.append(content)
            combined.append("\n\n")
            
        # 2. Project-specific AGENTS.md / agents.md
        project_agent = self.project_dir / ".agents" / "project" / "AGENTS.md"
        if not project_agent.exists():
            project_agent = self.project_dir / ".agents" / "project" / "agents.md"
            
        if project_agent.exists():
            combined.append("<!-- b1CodingTool: Project Context -->\n")
            content = project_agent.read_text(encoding="utf-8").strip()
            start_marker = "<!-- b1CodingTool: start -->"
            if start_marker in content:
                content = content.split(start_marker)[0].strip()
            combined.append(content)
            combined.append("\n\n")
            
        # 3. Installed modules' context folder
        modules_dir = self.project_dir / ".agents" / "modules"
        if modules_dir.exists():
            for mod in [d for d in modules_dir.iterdir() if d.is_dir()]:
                # 3a. Add module capabilities (skills and commands)
                config_path = mod / "b1-module.yaml"
                if not config_path.exists():
                    config_path = mod / "module.yaml"

                if config_path.exists():
                    try:
                        mod_config = ModuleConfig.from_yaml(config_path)
                        if mod_config.commands or mod_config.skills:
                            combined.append(f"<!-- b1CodingTool: Module Capabilities [{mod.name}] -->\n")
                            combined.append(f"### {mod.name} Capabilities\n\n")

                            if mod_config.commands:
                                combined.append("#### Commands\n")
                                for cmd in mod_config.commands:
                                    combined.append(f"- `{cmd.name}`: {cmd.description}\n")
                                combined.append("\n")

                            if mod_config.skills:
                                combined.append("#### Skills\n")
                                for skill in mod_config.skills:
                                    combined.append(f"- **{skill.name}**: {skill.description}\n")
                                combined.append("\n")
                            combined.append("\n")
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not load config for module {mod.name}: {e}[/yellow]")

                # 3b. Add module context files
                context_dir = mod / "context"
                if context_dir.exists():
                    for md_file in context_dir.glob("*.md"):
                        combined.append(f"<!-- b1CodingTool: Module Context [{mod.name}] - {md_file.name} -->\n")
                        combined.append(md_file.read_text(encoding="utf-8").strip())
                        combined.append("\n\n")
                        
        return "".join(combined).strip()
