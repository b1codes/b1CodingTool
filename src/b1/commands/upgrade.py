import click
import typer
from typing import Optional, Annotated
from pathlib import Path
from rich.console import Console

from b1.core.exceptions import ProjectError
from b1.core.context_manager import setup_context
from b1.commands.pair import pair_cmd

console = Console()


def upgrade_cmd(
    path: Annotated[Optional[Path], typer.Argument(help="The project directory to upgrade (default: current directory)")] = None,
):
    """
    Backfills an existing project's .agents/ scaffolding (e.g. a missing
    .agents/local/AGENTS.md) to match what the current b1CodingTool version
    expects, without overwriting or discarding existing content.
    """
    project_dir = (path or Path.cwd()).resolve()

    if not (project_dir / ".agents").exists():
        raise ProjectError(
            "Not a b1CodingTool project.",
            suggestions=[
                "Run `b1 init` to bootstrap the project structure.",
                "Ensure you are in the project root directory.",
            ],
        )

    setup_context(project_dir)

    console.print("[bold green]Upgrade complete![/bold green]")

    try:
        do_repair = typer.confirm("Re-pair now to apply updates?", default=False)
    except click.Abort:
        do_repair = False
    if do_repair:
        pair_cmd(sync=False)
