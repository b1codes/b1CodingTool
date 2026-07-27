import typer
import subprocess
import time
from pathlib import Path
from rich.console import Console
import shutil

from b1.core.config import B1Config
from b1.core.rule_extractor import RuleExtractor
from b1.core.hook_engine import HookEngine

console = Console()

def push_cmd():
    """
    Scans project-specific agent files and drafts a Pull Request to upstream.
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        console.print("[bold red]Project not initialized. Run b1 init.[/bold red]")
        raise typer.Exit(1)
        
    config = B1Config.load(project_dir)
    hook_engine = HookEngine(project_dir)
    
    if not config.upstream_repo:
        repo = typer.prompt("No upstream repository configured. Enter the upstream GitHub repo (e.g. org/repo)")
        config.upstream_repo = repo
        config.save(project_dir)
        console.print(f"[green]Saved upstream config to .agents/config.yaml[/green]")
        
    if not shutil.which("gh"):
        console.print("[bold red]GitHub CLI (gh) is not installed. Please install it to use b1 push.[/bold red]")
        raise typer.Exit(1)
        
    # 1. Run pre-push hooks
    console.print("[bold blue]Running pre-push hooks...[/bold blue]")
    hook_engine.run_hooks("pre-push")
        
    # 2. Intelligent Scanning and Rule Extraction
    extractor = RuleExtractor()
    project_agent_path = project_dir / ".agents" / "project" / "AGENTS.md"
    if not project_agent_path.exists():
        project_agent_path = project_dir / ".agents" / "project" / "agents.md"
    extracted_content = ""
    rules_count = 0
    
    if project_agent_path.exists():
        rules = extractor.extract(project_agent_path.read_text(encoding="utf-8"))
        if rules:
            extracted_content = "\n\n".join(rules)
            rules_count = len(rules)
            
    learnings_path = project_dir / ".agents" / "learnings.md"
    if extracted_content:
        learnings_path.write_text(f"# Generalized Learnings\n\nExtracted from project context.\n\n{extracted_content}\n", encoding="utf-8")
        console.print(f"[green]Extracted {rules_count} generalized rules to .agents/learnings.md[/green]")
    else:
        if learnings_path.exists():
            learnings_path.unlink()
        
    branch_name = f"b1-learnings-{int(time.time())}"
    console.print(f"[bold blue]Checking out new branch {branch_name}...[/bold blue]")
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        
        # 2. Selective Staging
        staged_any = False
        
        # Always check root AGENTS.md / agents.md fallback as it's project-agnostic
        root_agent = project_dir / "AGENTS.md"
        root_agent_name = "AGENTS.md"
        if not root_agent.exists():
            root_agent = project_dir / "agents.md"
            root_agent_name = "agents.md"
            
        if root_agent.exists():
            subprocess.run(["git", "add", root_agent_name], check=False, capture_output=True)
            staged_any = True
            
        # Stage only the extracted learnings
        if learnings_path.exists():
            subprocess.run(["git", "add", ".agents/learnings.md"], check=True, capture_output=True)
            staged_any = True
            
        if not staged_any:
            console.print("[yellow]No project-agnostic changes detected. Nothing to push.[/yellow]")
            subprocess.run(["git", "checkout", "-"], check=True, capture_output=True)
            subprocess.run(["git", "branch", "-d", branch_name], check=True, capture_output=True)
            return

        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            console.print("[yellow]No modifications detected in relevant files. Nothing to push.[/yellow]")
            subprocess.run(["git", "checkout", "-"], check=True, capture_output=True)
            subprocess.run(["git", "branch", "-d", branch_name], check=True, capture_output=True)
            return

        subprocess.run(["git", "commit", "-m", "chore: drafted generalized learnings from project context"], check=True, capture_output=True)
        
        console.print(f"[blue]Pushing branch to origin...[/blue]")
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True, capture_output=True)
        
        console.print(f"\n[bold magenta]Drafting Pull Request to {config.upstream_repo}...[/bold magenta]")
        
        pr_command = [
            "gh", "pr", "create", 
            "--repo", config.upstream_repo,
            "--title", "Draft Generalized Learnings", 
            "--body", "This PR forwards project-agnostic guidelines and logic detected in the agent context files for community/team review.",
            "--draft"
        ]
        
        pr_result = subprocess.run(pr_command, check=True, capture_output=True, text=True)
        
        console.print(f"\n[bold green]Success! Pull Request Drafted:[/bold green] {pr_result.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Git/GH Error:[/bold red]")
        err_msg = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else (e.stderr or str(e))
        console.print(err_msg)
        raise typer.Exit(1)
