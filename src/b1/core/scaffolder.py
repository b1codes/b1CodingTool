from pathlib import Path
from rich.console import Console

console = Console()

GITIGNORE_CONTENT = """# Python
__pycache__/
*.pyc
.venv/
.env

# b1CodingTool generated agent files
CLAUDE.md
CLAUDE.local.md
AGENTS.override.md
.claude/
.agents/local/
.agents/rules/local.md
.agents/skills/b1-rule.md
.agents/skills/b1-edge-case.md
.agents/skills/b1-reconcile.md
.agents/.b1-snapshots/
"""

README_CONTENT = """# b1CodingTool Project

This project is managed by b1CodingTool.
"""

def scaffold_project(root_dir: Path):
    agent_dir = root_dir / ".agents"
    docs_dir = root_dir / "docs"
    
    if not agent_dir.exists():
        agent_dir.mkdir(parents=True, exist_ok=True)
        console.print("[green]Created .agents/ directory.[/green]")
    else:
        console.print("[dim].agents/ directory already exists.[/dim]")
    
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        console.print("[green]Created docs/ directory.[/green]")
    else:
        console.print("[dim]docs/ directory already exists.[/dim]")
    
    gitignore_path = root_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE_CONTENT, encoding="utf-8")
        console.print("[green]Created .gitignore.[/green]")
    else:
        console.print("[dim].gitignore already exists.[/dim]")
        
    readme_path = root_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(README_CONTENT, encoding="utf-8")
        console.print("[green]Created README.md.[/green]")
    else:
        console.print("[dim]README.md already exists.[/dim]")
