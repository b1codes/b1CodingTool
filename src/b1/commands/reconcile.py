import difflib
import typer
from typing import Annotated, List
from pathlib import Path
from rich.console import Console

from b1.core.snapshots import check_drift, snapshot_for
from b1.commands.pair import run_pair, FULL_MATRIX

console = Console()


def _added_lines(old: str, new: str) -> List[str]:
    added = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("+ "):
            added.append(line[2:])
    return added


def _append_block(project_dir: Path, scope: str, lines: List[str]) -> None:
    seed = project_dir / ".agents" / scope / "AGENTS.md"
    seed.parent.mkdir(parents=True, exist_ok=True)
    existing = seed.read_text(encoding="utf-8") if seed.exists() else ""
    block = "\n".join(lines).strip()
    prefix = existing.rstrip("\n")
    joiner = "\n\n" if prefix else ""
    seed.write_text(f"{prefix}{joiner}{block}\n", encoding="utf-8")


def reconcile_cmd(
    discard_all: Annotated[bool, typer.Option("--discard-all", help="Discard every hand-edit (revert to generated).")] = False,
):
    """Promote or discard hand-edits made directly to generated agent files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    drifted = check_drift(project_dir)
    if not drifted:
        console.print("[green]Nothing to reconcile — no hand-edits detected.[/green]")
        return

    for f in drifted:
        rel = f.relative_to(project_dir)
        old = snapshot_for(project_dir, f) or ""
        added = _added_lines(old, f.read_text(encoding="utf-8"))
        if discard_all:
            console.print(f"[yellow]Discarding hand-edits in {rel}.[/yellow]")
            continue
        console.print(f"\n[bold]{rel}[/bold] — your added lines:")
        for line in added:
            console.print(f"  [green]+ {line}[/green]")
        choice = typer.prompt("Promote to (p)roject seed, (l)ocal seed, or (d)iscard?", default="d")
        c = choice.strip().lower()[:1]
        if c == "p":
            _append_block(project_dir, "project", added)
            console.print("[green]Promoted to .agents/project/AGENTS.md[/green]")
        elif c == "l":
            _append_block(project_dir, "local", added)
            console.print("[green]Promoted to .agents/local/AGENTS.md[/green]")
        else:
            console.print("[yellow]Discarding.[/yellow]")

    run_pair(project_dir, FULL_MATRIX, force=True)   # regenerate past the drift, refresh snapshots
    console.print("\n[bold green]Reconcile complete — agent files regenerated.[/bold green]")
