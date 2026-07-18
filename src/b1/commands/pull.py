import click
import typer
from pathlib import Path
from rich.console import Console
from b1.core.exceptions import B1Error, ProjectError

from b1.core.fetcher import ModuleFetcher
from b1.core.installer import ModuleInstaller
from b1.commands.pair import pair_cmd

console = Console()

def pull_cmd():
    """
    Syncs local modules with the upstream version control.
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        raise ProjectError(
            "Not a b1CodingTool project.",
            suggestions=["Run `b1 init` to bootstrap the project structure.", "Ensure you are in the project root directory."]
        )

    modules_dir = project_dir / ".agents" / "modules"

    if not modules_dir.exists():
        console.print("[yellow]No modules currently installed in this project.[/yellow]")
    else:
        fetcher = ModuleFetcher()
        installer = ModuleInstaller(target_project_dir=project_dir)

        installed_modules = [d for d in modules_dir.iterdir() if d.is_dir()]
        if not installed_modules:
            console.print("[yellow]No modules currently installed.[/yellow]")
        else:
            for mod_path in installed_modules:
                console.print(f"\\n[bold blue]Pulling updates for {mod_path.name}...[/bold blue]")
                cache_target = fetcher.cache_dir / mod_path.name

                if cache_target.exists():
                    try:
                        # We use the cached path as the source to fetch (which pulls latest)
                        updated_path = fetcher.fetch(str(cache_target))
                        installer.install(updated_path)
                    except B1Error as e:
                        console.print(f"[bold red]Error updating {mod_path.name}:[/bold red] {e.message}")
                        if e.suggestions:
                            console.print("[yellow]Suggestions:[/yellow]")
                            for suggestion in e.suggestions:
                                console.print(f"  - {suggestion}")
                    except Exception as e:
                        console.print(f"[bold red]Unexpected error updating {mod_path.name}:[/bold red] {e}")
                else:
                    console.print(f"[yellow]Module {mod_path.name} not found in global cache. Skipping sync.[/yellow]")

            console.print("\\n[bold green]Pull sync complete![/bold green]")

    try:
        do_repair = typer.confirm("Re-pair now to apply updates?", default=False)
    except click.Abort:
        do_repair = False
    if do_repair:
        pair_cmd(sync=False)
