import subprocess
import typer
from pathlib import Path
from typing import Annotated
from rich.console import Console

console = Console()


def update_project_cmd(
    claude: Annotated[bool, typer.Option("--claude", help="Only update Claude Code plugins/marketplaces.")] = False,
    agy: Annotated[bool, typer.Option("--agy", help="Only update Antigravity CLI plugins.")] = False,
    codex: Annotated[bool, typer.Option("--codex", help="Only update Codex CLI plugins/marketplaces.")] = False,
    all_agents: Annotated[bool, typer.Option("--all", help="Update Claude Code, Antigravity, and Codex CLI explicitly.")] = False,
    skip_skills: Annotated[bool, typer.Option("--skip-skills", help="Skip the 'npx skills update' step.")] = False,
):
    """Refreshes plugin marketplaces/plugins for whichever coding-agent CLIs are on PATH, then runs `npx skills update`."""
    # This file is at src/b1/commands/update_project.py; the bundled script
    # lives at <repo root>/scripts/update-project.sh.
    tool_root = Path(__file__).resolve().parent.parent.parent.parent
    script_path = tool_root / "scripts" / "update-project.sh"

    if not script_path.exists():
        console.print(f"[bold red]Error:[/bold red] update-project.sh not found at {script_path}")
        raise typer.Exit(1)

    args = [str(script_path)]
    if claude:
        args.append("--claude")
    if agy:
        args.append("--agy")
    if codex:
        args.append("--codex")
    if all_agents:
        args.append("--all")
    if skip_skills:
        args.append("--skip-skills")

    result = subprocess.run(args, cwd=Path.cwd())
    raise typer.Exit(result.returncode)
