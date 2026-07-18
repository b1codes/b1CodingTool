import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

from b1.core.scaffolder import scaffold_project
from b1.core.context_manager import setup_context
from b1.core.fetcher import ModuleFetcher
from b1.core.installer import ModuleInstaller
from b1.core.compiler import ContextCompiler
from b1.core.config import B1Config
from b1.core.translator import AgentTranslator
from b1.commands.link_github import run_link_github
from b1.commands.link_clickup import run_link_clickup

# Initialize FastMCP
mcp = FastMCP("b1")

@mcp.tool()
def b1_init(path: Optional[str] = None) -> str:
    """
    Initializes a new or existing project with the b1 structure.
    
    :param path: The directory to initialize (default: current directory).
    """
    target_path = Path(path) if path else Path.cwd()
    target_path = target_path.resolve()
    
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
        
    scaffold_project(target_path)
    setup_context(target_path)
    return f"b1CodingTool project initialized at: {target_path}"

@mcp.tool()
def b1_install(source: str, link: bool = False) -> str:
    """
    Fetches and mounts a 'superpower' module into the project.
    
    :param source: Git URL or local path to module target.
    :param link: Symlink the module instead of copying (useful for development).
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        return "Error: Not a b1CodingTool project. Run b1_init first."
        
    fetcher = ModuleFetcher()
    installer = ModuleInstaller(target_project_dir=project_dir)
    
    try:
        module_path = fetcher.fetch(source)
        installer.install(module_path, link=link)
        return f"Module from {source} installed successfully."
    except Exception as e:
        return f"Error installing module: {str(e)}"

@mcp.tool()
def b1_pair() -> str:
    """
    Synchronizes the centralized agents.md context across agent-specific files (CLAUDE.md, CODEX, ANTIGRAVITY).
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        return "Error: Project not initialized. Run b1_init first."

    config = B1Config.load(project_dir)

    if not config.active_agents:
        # Default agents if none configured
        config.active_agents = ["CLAUDE", "CODEX", "ANTIGRAVITY"]
        config.save(project_dir)
        
    compiler = ContextCompiler(project_dir, config=config)
    translator = AgentTranslator(project_dir)
    
    compiled = compiler.compile()
    if compiled.is_empty():
        return "No context found to compile."

    translator.generate_files(config.active_agents, compiled)
    return f"Parity synchronization complete for: {', '.join(config.active_agents)}"

@mcp.tool()
def b1_link_github(repo_input: str) -> str:
    """
    Links the current project to a GitHub repository.
    
    :param repo_input: GitHub URL or owner/repo slug.
    """
    try:
        info = run_link_github(repo_input)
        return f"Project linked to {info['owner']}/{info['repo']} (default branch: {info['default_branch']})"
    except Exception as e:
        return f"Error linking GitHub repo: {str(e)}"

@mcp.tool()
def b1_link_clickup(list_input: str) -> str:
    """
    Links the project to a ClickUp list for task management.
    
    :param list_input: ClickUp List URL or ID.
    """
    try:
        list_id = run_link_clickup(list_input)
        return f"Project linked to ClickUp list: {list_id}"
    except Exception as e:
        return f"Error linking ClickUp list: {str(e)}"

@mcp.tool()
def b1_pull() -> str:
    """
    Syncs local modules with the upstream version control.
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        return "Error: Not a b1CodingTool project."

    modules_dir = project_dir / ".agents" / "modules"
    if not modules_dir.exists():
        return "No modules currently installed in this project."
        
    fetcher = ModuleFetcher()
    installer = ModuleInstaller(target_project_dir=project_dir)
    
    installed_modules = [d for d in modules_dir.iterdir() if d.is_dir()]
    if not installed_modules:
        return "No modules currently installed."
        
    results = []
    for mod_path in installed_modules:
        cache_target = fetcher.cache_dir / mod_path.name
        if cache_target.exists():
            try:
                updated_path = fetcher.fetch(str(cache_target))
                installer.install(updated_path)
                results.append(f"Successfully updated {mod_path.name}")
            except Exception as e:
                results.append(f"Error updating {mod_path.name}: {str(e)}")
        else:
            results.append(f"Module {mod_path.name} not found in global cache. Skipping sync.")
            
    return "\n".join(results)

@mcp.tool()
def b1_status() -> str:
    """
    Returns a summary of installed modules and current context parity.
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        return json.dumps({"error": "Not a b1CodingTool project."})
        
    config = B1Config.load(project_dir)
    modules_dir = project_dir / ".agents" / "modules"
    installed_modules = []
    if modules_dir.exists():
        installed_modules = [d.name for d in modules_dir.iterdir() if d.is_dir()]
        
    status = {
        "project_root": str(project_dir),
        "active_agents": config.active_agents,
        "installed_modules": installed_modules,
        "github_repo": f"{config.github_owner}/{config.github_repo}" if config.github_owner else None,
        "clickup_list": config.clickup_list_id if config.clickup_list_id else None
    }
    return json.dumps(status, indent=2)

@mcp.resource("b1://context/compiled")
def get_compiled_context() -> str:
    """
    Returns the fully merged content of the project-level agents.md and all active module context files.
    """
    project_dir = Path.cwd()
    config = B1Config.load(project_dir)
    compiler = ContextCompiler(project_dir, config=config)
    return compiler.compile().render_preview()

@mcp.resource("b1://config/project")
def get_project_config() -> str:
    """
    Returns the project settings, linked integrations, and environment variables.
    """
    project_dir = Path.cwd()
    config_path = project_dir / ".agents" / "config.yaml"
    if config_path.exists():
        return config_path.read_text()
    return "{}"

@mcp.resource("b1://modules/library")
def get_modules_library() -> str:
    """
    Returns a list of installed modules and their basic info.
    """
    project_dir = Path.cwd()
    modules_dir = project_dir / ".agents" / "modules"
    library = []
    if modules_dir.exists():
        for mod_dir in [d for d in modules_dir.iterdir() if d.is_dir()]:
            library.append({
                "name": mod_dir.name,
                "path": str(mod_dir)
            })
    return json.dumps(library, indent=2)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
