import typer
from pathlib import Path
from rich.console import Console
from typing import List, Dict

from b1.core.fetcher import ModuleFetcher
from b1.core.installer import ModuleInstaller
from b1.core.exceptions import ProjectError, B1Error
from b1.core.config import B1Config

console = Console()

DEFAULT_BUNDLES = {
    "flutter": ["dart", "flutter"],
    "llc-base": [
        "llc-api-health",
        "llc-gcp-identity-platform",
        "llc-devops-infra",
        "llc-ip-protection",
        "llc-logging",
        "llc-security",
        "llc-standards",
        "llc-todo"
    ],
    "llc-flutter": [
        "dart",
        "flutter",
        "llc-flutter",
        "llc-api-health",
        "llc-gcp-identity-platform",
        "llc-logging",
        "llc-standards",
        "llc-security"
    ],
    "llc-react": [
        "typescript",
        "react-web",
        "llc-react",
        "llc-api-health",
        "llc-gcp-identity-platform",
        "llc-logging",
        "llc-standards",
        "llc-security"
    ],
    "llc-swift": [
        "swift",
        "swiftui",
        "llc-swift",
        "llc-api-health",
        "llc-gcp-identity-platform",
        "llc-logging",
        "llc-standards",
        "llc-security"
    ],
    "llc": [
        "llc-api-health",
        "llc-gcp-identity-platform",
        "llc-devops-infra",
        "llc-flutter",
        "llc-ip-protection",
        "llc-logging",
        "llc-react",
        "llc-security",
        "llc-standards",
        "llc-swift",
        "llc-todo"
    ]
}

def resolve_bundles(sources: List[str], custom_bundles: Dict[str, List[str]]) -> List[str]:
    expanded = []
    visited_bundles = set()
    
    def expand(source: str):
        if (source in custom_bundles or source in DEFAULT_BUNDLES) and source not in visited_bundles:
            visited_bundles.add(source)
            items = custom_bundles[source] if source in custom_bundles else DEFAULT_BUNDLES[source]
            for item in items:
                expand(item)
            visited_bundles.remove(source)
        else:
            if source not in expanded:
                expanded.append(source)
                
    for src in sources:
        expand(src)
        
    return expanded

def install_cmd(
    sources: List[str] = typer.Argument(..., help="Git URL(s), local path(s), or bundle name(s) of module target(s)"),
    link: bool = typer.Option(False, "--link", "-l", help="Symlink the module instead of copying (useful for development)")
):
    """
    Equips the current project workspace with specific development or deployment module(s).
    """
    project_dir = Path.cwd()
    if not (project_dir / ".agents").exists():
        raise ProjectError(
            "Not a b1CodingTool project.",
            suggestions=["Run `b1 init` to bootstrap the project structure.", "Ensure you are in the project root directory."]
        )
        
    config = B1Config.load(project_dir)
    custom_bundles = getattr(config, "bundles", {}) or {}
    
    resolved_sources = resolve_bundles(sources, custom_bundles)
    
    fetcher = ModuleFetcher()
    installer = ModuleInstaller(target_project_dir=project_dir)
    
    for idx, source in enumerate(resolved_sources, 1):
        console.print(f"\n[bold blue]Installing module {idx}/{len(resolved_sources)}: {source}[/bold blue]")
        module_path = fetcher.fetch(source)
        installer.install(module_path, link=link)
