import typer
from typing import Annotated, Optional
from pathlib import Path
from rich.console import Console

from b1.core.config import B1Config
from b1.core.compiler import ContextCompiler
from b1.core.translator import AgentTranslator
from b1.core.hook_engine import HookEngine
from b1.core.snapshots import check_drift, record_snapshots
from b1.core.exceptions import DriftError

console = Console()

FULL_MATRIX = ["CLAUDE", "CODEX", "ANTIGRAVITY"]


def run_pair(project_dir: Path, agents: list[str], config: Optional[B1Config] = None, force: bool = False) -> bool:
    """Non-interactive compile -> translate core. Returns True if files were generated,
    False if there was no context to compile. Raises DriftError when a generated file
    was hand-edited (unless force=True). Records snapshots after generating."""
    if config is None:
        config = B1Config.load(project_dir)
    if not force:
        drifted = check_drift(project_dir)
        if drifted:
            raise DriftError(drifted)
    hook_engine = HookEngine(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)

    hook_engine.run_hooks("pre-pair")
    compiled = compiler.compile()
    if compiled.is_empty():
        return False
    translator.generate_files(agents, compiled)
    hook_engine.run_hooks("post-pair")
    record_snapshots(project_dir)
    return True


def _run_pair_or_halt(project_dir: Path, agents: list[str], config: Optional[B1Config] = None) -> bool:
    """run_pair, but on drift print a clear halt message and exit non-zero."""
    try:
        return run_pair(project_dir, agents, config=config)
    except DriftError as e:
        console.print("[bold red]Hand-edited generated files detected:[/bold red]")
        for f in e.files:
            console.print(f"  - {f.relative_to(project_dir)}")
        console.print("Run [bold]b1 reconcile[/bold] to resolve, then retry.")
        raise typer.Exit(1)


def pair_cmd(
    sync: Annotated[bool, typer.Option("--sync", help="Regenerate the full agent matrix (Claude, Codex, Antigravity) regardless of active_agents.")] = False,
):
    """Compile the .agents/ sources into each agent's native files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    config = B1Config.load(project_dir)

    if sync:
        agents = FULL_MATRIX
    else:
        if not config.active_agents:
            agent_input = typer.prompt(
                "Which agents do you want to target? (comma separated: CLAUDE,CODEX,ANTIGRAVITY)",
                default="CLAUDE,CODEX,ANTIGRAVITY",
            )
            agents = [a.strip().upper() for a in agent_input.split(",") if a.strip()]
            config.active_agents = agents
            config.save(project_dir)
        else:
            agents = config.active_agents

    console.print("[bold blue]Compiling contexts...[/bold blue]")
    if not _run_pair_or_halt(project_dir, agents, config=config):
        console.print("[yellow]No context found to compile.[/yellow]")
        return
    console.print(f"[blue]Writing configurations for:[/blue] {', '.join(agents)}")
    console.print("\n[bold green]Cross-agent parity synchronization complete![/bold green] \U0001f504")
