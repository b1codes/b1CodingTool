import click
import typer
from typing import Optional, Annotated
from pathlib import Path
from rich.console import Console

from b1.commands._notes import record_note

console = Console()


def edge_case_cmd(
    text: Annotated[str, typer.Argument(help="The project-specific edge case to record.")],
    scope: Annotated[Optional[str], typer.Option("--scope", help="project (team) or local (personal).")] = None,
    no_pair: Annotated[bool, typer.Option("--no-pair", help="Append only; don't regenerate agent files.")] = False,
):
    """Record a project-specific edge case and fan it out to every agent."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    if scope is None:
        try:
            scope = typer.prompt("Scope? (project = team, local = personal)", default="project")
        except click.Abort:
            scope = "project"

    record_note(project_dir, "edge-case", text, scope, no_pair, "edge case")
