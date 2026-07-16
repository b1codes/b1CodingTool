from pathlib import Path
from rich.console import Console

console = Console()

BASE_AGENT_MD = """# b1CodingTool: Global Context
This is the root `agents.md` file managed by b1CodingTool. 
It contains project-agnostic software development practices and general notes.

## General Guidelines
- Write clean, modular code.
- Include thoughtful documentation.
"""

PROJECT_AGENT_MD = """# b1CodingTool: Project Context
This is the project-specific `agents.md` context file.
It contains app logic, directory structures, and active tasks.

## Active Tasks
- Initial b1 setup

## Architecture Notes
- Follow the guidelines specified in the root `agents.md`.
"""

def setup_context(root_dir: Path):
    def case_sensitive_exists(path: Path) -> bool:
        if not path.exists():
            return False
        return path.name in {p.name for p in path.parent.iterdir()}

    # Migrate lowercase root to uppercase if exists
    old_root_path = root_dir / "agents.md"
    root_agent_path = root_dir / "AGENTS.md"
    if case_sensitive_exists(old_root_path) and not case_sensitive_exists(root_agent_path):
        console.print("[yellow]Renaming existing agents.md to AGENTS.md...[/yellow]")
        temp_path = old_root_path.with_name(old_root_path.name + ".tmp_rename")
        old_root_path.rename(temp_path)
        temp_path.rename(root_agent_path)

    project_agent_dir = root_dir / ".agents" / "project"
    old_project_path = project_agent_dir / "agents.md"
    project_agent_path = project_agent_dir / "AGENTS.md"
    
    # Root AGENTS.md handling
    if case_sensitive_exists(root_agent_path):
        content = root_agent_path.read_text(encoding="utf-8")
        if "b1CodingTool" not in content:
            console.print("[yellow]Appending b1CodingTool context to existing AGENTS.md...[/yellow]")
            with open(root_agent_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + BASE_AGENT_MD)
        else:
            console.print("[dim]Root AGENTS.md already configured for b1CodingTool, skipping.[/dim]")
    else:
        root_agent_path.write_text(BASE_AGENT_MD, encoding="utf-8")
        console.print("[green]Created root AGENTS.md.[/green]")

    # Project-specific AGENTS.md handling
    project_agent_dir.mkdir(parents=True, exist_ok=True)
    if case_sensitive_exists(old_project_path) and not case_sensitive_exists(project_agent_path):
        console.print("[yellow]Renaming existing project agents.md to AGENTS.md...[/yellow]")
        temp_path = old_project_path.with_name(old_project_path.name + ".tmp_rename")
        old_project_path.rename(temp_path)
        temp_path.rename(project_agent_path)

    if not case_sensitive_exists(project_agent_path):
        project_agent_path.write_text(PROJECT_AGENT_MD, encoding="utf-8")
        console.print("[green]Created project-specific AGENTS.md in .agents/project/.[/green]")
    else:
        console.print("[dim]Project-specific AGENTS.md already exists, skipping.[/dim]")
