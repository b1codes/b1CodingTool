import typer
from typing import Annotated
from pathlib import Path
from rich.console import Console

from b1.core.config import B1Config
from b1.core.compiler import ContextCompiler
from b1.core.translator import AgentTranslator
from b1.core.hook_engine import HookEngine

console = Console()

FULL_MATRIX = ["CLAUDE", "CODEX", "ANTIGRAVITY"]


def pair_cmd(
    sync: Annotated[bool, typer.Option("--sync", help="Regenerate the full agent matrix (Claude, Codex, Antigravity) regardless of active_agents.")] = False,
):
    """Compile the .agents/ sources into each agent's native files."""
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)

    config = B1Config.load(project_dir)
    hook_engine = HookEngine(project_dir)

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

    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)

    console.print("[bold blue]Compiling contexts...[/bold blue]")
    hook_engine.run_hooks("pre-pair")
    compiled = compiler.compile()
    if compiled.is_empty():
        console.print("[yellow]No context found to compile.[/yellow]")
        return
    console.print(f"[blue]Writing configurations for:[/blue] {', '.join(agents)}")
    translator.generate_files(agents, compiled)
    hook_engine.run_hooks("post-pair")
    console.print("\n[bold green]Cross-agent parity synchronization complete![/bold green] \U0001f504")
