"""Shared fan-out helper for note-recording commands (`b1 rule`, `b1 edge-case`).

Both commands validate an already-resolved scope, append a note, print a
status line, and (unless --no-pair) regenerate agent files. This module
extracts that common tail so each command only needs its own guard/scope
logic plus a single call here.
"""
import typer
from pathlib import Path
from rich.console import Console

from b1.core.notes import append_note
from b1.commands.pair import _run_pair_or_halt, FULL_MATRIX

console = Console()


def record_note(project_dir: Path, kind: str, text: str, scope: str, no_pair: bool, label: str) -> None:
    """Validate scope, append the note, and fan out to every agent unless --no-pair.

    `scope` must already be resolved/defaulted by the caller (this function
    does no prompting). `label` is the noun used in the "Recorded ..." line
    (e.g. "guardrail", "edge case") so each command keeps its own wording.
    """
    if scope not in ("project", "local"):
        console.print("[bold red]--scope must be 'project' or 'local'.[/bold red]")
        raise typer.Exit(1)

    dest, appended = append_note(project_dir, kind, text, scope)
    rel = dest.relative_to(project_dir)
    if not appended:
        console.print(f"[yellow]Already recorded in {rel}; nothing to do.[/yellow]")
        return
    console.print(f"[green]✔ Recorded {label} in[/green] {rel}")
    if not no_pair:
        _run_pair_or_halt(project_dir, FULL_MATRIX)
        console.print("[green]Now loaded for every agent (Claude, Codex, Antigravity).[/green]")
