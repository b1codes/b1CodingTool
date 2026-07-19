import typer
from typing import Annotated
from pathlib import Path
from rich.console import Console

from b1.commands._notes import record_note

console = Console()


def rule_cmd(
    text: Annotated[str, typer.Argument(help="The recurring-bug rule to record.")],
    scope: Annotated[str, typer.Option("--scope", help="project (team) or local (personal).")] = "project",
    no_pair: Annotated[bool, typer.Option("--no-pair", help="Append only; don't regenerate agent files.")] = False,
):
    """Record a recurring-bug/behavior guardrail and fan it out to every agent."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    record_note(project_dir, "rule", text, scope, no_pair, "guardrail")
