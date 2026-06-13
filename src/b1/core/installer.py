import shutil
import subprocess
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from b1.core.schema import ModuleConfig
from b1.core.hook_engine import HookEngine

console = Console()

class ModuleInstaller:
    def __init__(self, target_project_dir: Path):
        self.project_dir = target_project_dir
        self.modules_dir = self.project_dir / ".agents" / "modules"
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        self.hook_engine = HookEngine(self.project_dir)
        
    def install(self, source_path: Path, link: bool = False):
        # Locate the yaml file
        yaml_path = source_path / "b1-module.yaml"
        if not yaml_path.exists():
            yaml_path = source_path / "module.yaml"
            if not yaml_path.exists():
                raise FileNotFoundError(f"No b1-module.yaml or module.yaml found in {source_path}")
                
        config = ModuleConfig.from_yaml(yaml_path)
        
        mode_str = " (symlinked)" if link else ""
        console.print(f"\n[bold green]Installing Module:[/bold green] {config.name} (v{config.version}){mode_str}")
        
        target_mod_dir = self.modules_dir / config.name
        
        # 1. Prepare target
        # Check if it exists or is a broken symlink (is_symlink() returns True even if broken)
        if target_mod_dir.exists() or target_mod_dir.is_symlink():
            console.print(f"[yellow]Module {config.name} already installed. Overwriting...[/yellow]")
            if target_mod_dir.is_symlink():
                target_mod_dir.unlink()
            else:
                shutil.rmtree(target_mod_dir)
            
        if link:
            # Create a relative symlink if possible, or absolute if not
            try:
                os.symlink(source_path.resolve(), target_mod_dir)
                console.print(f"[green]\u2714[/green] Created symlink to [blue]{source_path}[/blue]")
            except Exception as e:
                console.print(f"[bold red]Failed to create symlink:[/bold red] {e}")
                raise
        else:
            # Copy files (Ignore .git folder when copying)
            shutil.copytree(source_path, target_mod_dir, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            console.print(f"[green]\u2714[/green] Copied files to [blue]{target_mod_dir.relative_to(self.project_dir)}[/blue]")
        
        # 1.5. Gitignore if proprietary
        if config.proprietary:
            self._add_to_gitignore(config.name)
        
        # 2. Run skill setup scripts
        if config.skills:
            console.print("\n[bold]Preparing Skills[/bold]")
            for skill in config.skills:
                if skill.install_command:
                    self._run_skill_command(skill.name, skill.install_command, target_mod_dir)
                else:
                    console.print(f"[dim]  - {skill.name} (no setup required)[/dim]")

        # 3. Run lifecycle hooks
        if config.hooks:
            console.print("\n[bold]Running Lifecycle Hooks[/bold]")
            self.hook_engine.run_hooks("post-install", target_module=config.name)

        console.print(f"\n[bold green]Successfully installed {config.name}![/bold green] 🚀")

    def _run_skill_command(self, name: str, command: str, execution_dir: Path):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Executing setup for [cyan]{name}[/cyan]...", total=None)

            try:
                # Run the command with access to shell
                subprocess.run(
                    command, 
                    cwd=execution_dir, 
                    shell=True, 
                    text=True, 
                    capture_output=True,
                    check=True,
                    timeout=300 # 5 minute timeout
                )
                progress.update(task, description=f"[green]✔[/green] Setup complete for [cyan]{name}[/cyan]")
            except subprocess.TimeoutExpired:
                progress.update(task, description=f"[red]✖[/red] Timed out during setup for [cyan]{name}[/cyan]")
                console.print(f"[red]Error:[/red] Command timed out after 300s: {command}")
            except subprocess.CalledProcessError as e:
                progress.update(task, description=f"[red]✖[/red] Failed setup for [cyan]{name}[/cyan]")
                console.print(f"[red]Error Output:[/red]\n{e.stderr}")
                # Don't halt the whole installation if one skill script fails, just note it.

    def _add_to_gitignore(self, module_name: str):
        """Adds the proprietary module to .gitignore so it is not committed to the consumer project repo."""
        gitignore_path = self.project_dir / ".gitignore"
        entry = f".agents/modules/{module_name}"
        
        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            if entry not in content.splitlines():
                if content and not content.endswith("\n"):
                    content += "\n"
                content += f"{entry}\n"
                gitignore_path.write_text(content, encoding="utf-8")
                console.print(f"[dim]Added {entry} to .gitignore (proprietary lock)[/dim]")
        else:
            gitignore_path.write_text(f"{entry}\n", encoding="utf-8")
            console.print(f"[dim]Created .gitignore and added {entry} (proprietary lock)[/dim]")


