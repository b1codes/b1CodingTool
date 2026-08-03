import subprocess
import os
import re
from pathlib import Path
from typing import Optional
from rich.console import Console
from b1.core.exceptions import NetworkError

console = Console()

class ModuleFetcher:
    def __init__(self, timeout: int = 60):
        self.cache_dir = Path.home() / ".b1" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        
    def fetch(self, source: str) -> Path:
        """
        Takes a source (either a git url or local path).
        Returns the pathlib.Path to the prepared module directory.
        """
        # 0. Check if it's a GitHub URL with a subpath
        github_info = self.parse_github_url(source)
        if github_info:
            return self.fetch_github_subpath(github_info)

        # 1. Try to resolve by name from B1_LIBRARY_PATH if set
        library_path_env = os.environ.get("B1_LIBRARY_PATH")
        potential_library_roots = []
        if library_path_env:
            potential_library_roots.append(Path(library_path_env).expanduser().resolve())
        
        # Add the tool's own directory as a fallback library root
        # fetcher.py is at src/b1/core/fetcher.py, so root is 3 levels up
        tool_root = Path(__file__).resolve().parent.parent.parent.parent
        if tool_root not in potential_library_roots:
            potential_library_roots.append(tool_root)

        # Also check for a sibling private overlay repo (e.g. "<name>-LLC-lib"
        # next to the tool checkout), matching the umbrella workspace convention
        # documented in this project's CLAUDE.md, so proprietary llc-* bundle
        # modules resolve without requiring B1_LIBRARY_PATH to be set manually.
        workspace_root = tool_root.parent
        if workspace_root.exists():
            for sibling in sorted(workspace_root.iterdir()):
                if (
                    sibling.is_dir()
                    and sibling != tool_root
                    and "llc-lib" in sibling.name.lower()
                    and sibling not in potential_library_roots
                ):
                    potential_library_roots.append(sibling)

        for lib_root in potential_library_roots:
            if lib_root.exists():
                modules_base = lib_root / "modules"
                if modules_base.exists():
                    # Strip trailing slashes and get the name part
                    clean_source = source.rstrip("/")
                    search_name = clean_source.split("/")[-1] if "/" in clean_source else clean_source
                    
                    # Try direct relative path first (e.g. modules/framework/react-native)
                    direct_rel = lib_root / source
                    if direct_rel.exists() and direct_rel.is_dir() and ((direct_rel / "b1-module.yaml").exists() or (direct_rel / "module.yaml").exists()):
                        return direct_rel

                    # Try searching for the name
                    matches = list(modules_base.glob(f"**/{search_name}"))
                    for match in matches:
                        if match.is_dir() and ((match / "b1-module.yaml").exists() or (match / "module.yaml").exists()):
                            return match

        # 2. Try as a local path (relative to CWD)
        potential_paths = [
            Path(source).expanduser(),
            Path.cwd() / source,
            Path.cwd() / "modules" / source
        ]
        
        for p in potential_paths:
            resolved = p.resolve()
            if resolved.exists() and resolved.is_dir():
                if (resolved / "b1-module.yaml").exists() or (resolved / "module.yaml").exists():
                    return resolved

        # 3. Specific error if directory found but missing module file
        direct_path = Path(source).expanduser().resolve()
        if direct_path.exists() and direct_path.is_dir():
             raise ValueError(f"Found directory at '{direct_path}', but it contains no 'b1-module.yaml' or 'module.yaml'.")
                
        # 4. If it looks like a Git URL
        if source.startswith("http") or source.startswith("git@") or source.startswith("file://") or source.endswith(".git"):
            module_name = source.split("/")[-1].replace(".git", "")
            target_path = self.cache_dir / module_name
            
            if target_path.exists():
                console.print(f"[dim]Module {module_name} already in cache. Pulling latest...[/dim]")
                try:
                    subprocess.run(
                        ["git", "-C", str(target_path), "pull"], 
                        check=True, 
                        capture_output=True,
                        timeout=self.timeout
                    )
                except subprocess.TimeoutExpired:
                    raise NetworkError(
                        f"Connection timed out while pulling {source}",
                        suggestions=[
                            "Check your internet connection.",
                            "The git server might be slow or unresponsive.",
                            f"Try increasing the timeout (current: {self.timeout}s)."
                        ]
                    )
                except subprocess.CalledProcessError as e:
                    stderr = e.stderr.decode('utf-8')
                    suggestions = [
                        "Verify you have access to the repository.",
                        "Check if the repository URL is correct."
                    ]
                    if "SSL" in stderr or "certificate" in stderr:
                        suggestions.append("Check your SSL certificate configuration.")
                        suggestions.append("Try setting GIT_SSL_NO_VERIFY=true if you are behind a corporate proxy (use with caution).")
                    
                    raise NetworkError(
                        f"Failed to pull latest from {source}\nError: {stderr.strip()}",
                        suggestions=suggestions
                    )
                return target_path
            
            console.print(f"[blue]Cloning module from {source}...[/blue]")
            try:
                subprocess.run(
                    ["git", "clone", source, str(target_path)], 
                    check=True, 
                    capture_output=True,
                    timeout=self.timeout
                )
            except subprocess.TimeoutExpired:
                raise NetworkError(
                    f"Connection timed out while cloning {source}",
                    suggestions=[
                        "Check your internet connection.",
                        "Verify the repository URL exists.",
                        f"Try increasing the timeout (current: {self.timeout}s)."
                    ]
                )
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode('utf-8')
                suggestions = [
                    "Verify you have access to the repository.",
                    "Check if the repository URL is correct."
                ]
                if "SSL" in stderr or "certificate" in stderr:
                    suggestions.append("Check your SSL certificate configuration.")
                    suggestions.append("Try setting GIT_SSL_NO_VERIFY=true if you are behind a corporate proxy (use with caution).")
                
                raise NetworkError(
                    f"Failed to clone {source}\nError: {stderr.strip()}",
                    suggestions=suggestions
                )
                
            return target_path
            
        raise ValueError(f"Invalid module source or not found locally: {source}")

    def parse_github_url(self, url: str) -> Optional[dict]:
        """
        Parses a GitHub web URL like https://github.com/owner/repo/tree/branch/path
        """
        # Match both /tree/ and /blob/
        pattern = r"https://github\.com/([^/]+)/([^/]+)/(tree|blob)/([^/]+)/(.*)"
        match = re.match(pattern, url)
        if match:
            return {
                "owner": match.group(1),
                "repo": match.group(2),
                "branch": match.group(4),
                "path": match.group(5),
                "repo_url": f"https://github.com/{match.group(1)}/{match.group(2)}.git"
            }
        return None

    def fetch_github_subpath(self, info: dict) -> Path:
        """
        Clones a repo and returns the path to the specific subdirectory.
        """
        repo_cache_name = f"{info['owner']}-{info['repo']}"
        target_repo_path = self.cache_dir / repo_cache_name
        
        if not target_repo_path.exists():
            console.print(f"[blue]Cloning {info['repo_url']}...[/blue]")
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", info["branch"], info["repo_url"], str(target_repo_path)],
                check=True,
                capture_output=True,
                timeout=self.timeout
            )
        else:
            console.print(f"[dim]Using cached repo {repo_cache_name}.[/dim]")
            # Optionally pull latest if needed
            
        subpath = target_repo_path / info["path"]
        if not subpath.exists():
            raise FileNotFoundError(f"Path {info['path']} not found in repo {info['repo']}")
            
        return subpath
