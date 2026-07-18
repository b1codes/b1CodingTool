import typer
from typing import Annotated
from pathlib import Path
from rich.console import Console

from b1.core.notes import append_note
from b1.commands.pair import run_pair, FULL_MATRIX

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
    if scope not in ("project", "local"):
        console.print("[bold red]--scope must be 'project' or 'local'.[/bold red]")
        raise typer.Exit(1)

    dest, appended = append_note(project_dir, "rule", text, scope)
    rel = dest.relative_to(project_dir)
    if not appended:
        console.print(f"[yellow]Already recorded in {rel}; nothing to do.[/yellow]")
        return
    console.print(f"[green]✔ Recorded guardrail in[/green] {rel}")
    if not no_pair:
        run_pair(project_dir, FULL_MATRIX)
        console.print("[green]Now loaded for every agent (Claude, Codex, Antigravity).[/green]")
