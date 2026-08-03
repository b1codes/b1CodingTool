# tests/unit/test_fetcher.py
import subprocess
import os
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from b1.core.fetcher import ModuleFetcher


def _make_local_module(base: Path, name="test-module") -> Path:
    mod_dir = base / name
    mod_dir.mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text(
        yaml.dump({"name": name, "version": "1.0.0", "type": "development", "skills": [], "hooks": {}}),
        encoding="utf-8",
    )
    return mod_dir


def _fetcher(tmp_path) -> ModuleFetcher:
    """Create a ModuleFetcher with cache_dir redirected to tmp_path."""
    fetcher = ModuleFetcher()
    fetcher.cache_dir = tmp_path / "cache"
    fetcher.cache_dir.mkdir(parents=True, exist_ok=True)
    return fetcher


def test_fetch_local_path_returns_module_dir(tmp_path):
    mod_dir = _make_local_module(tmp_path)
    fetcher = _fetcher(tmp_path)
    result = fetcher.fetch(str(mod_dir))
    assert result == mod_dir


def test_fetch_local_path_missing_raises_value_error(tmp_path):
    fetcher = _fetcher(tmp_path)
    with pytest.raises(ValueError, match="Invalid module source or not found locally"):
        fetcher.fetch(str(tmp_path / "nonexistent"))


def test_fetch_local_path_without_yaml_raises_value_error(tmp_path):
    bare_dir = tmp_path / "bare"
    bare_dir.mkdir()
    fetcher = _fetcher(tmp_path)
    with pytest.raises(ValueError, match="but it contains no 'b1-module.yaml' or 'module.yaml'"):
        fetcher.fetch(str(bare_dir))


def test_fetch_git_url_clones_on_first_fetch(tmp_path):
    fetcher = _fetcher(tmp_path)
    # Do NOT pre-create the cache entry — fetcher should clone fresh
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        fetcher.fetch("https://github.com/org/my-module.git")

    # git clone should have been the first subprocess call
    first_call_args = mock_run.call_args_list[0][0][0]
    assert first_call_args[0] == "git"
    assert first_call_args[1] == "clone"


def test_fetch_git_url_pulls_when_cache_exists(tmp_path):
    fetcher = _fetcher(tmp_path)
    # Pre-create the cache entry to simulate an existing clone
    cached = fetcher.cache_dir / "my-module"
    _make_local_module(cached, "my-module")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        fetcher.fetch("https://github.com/org/my-module.git")

    first_call_args = mock_run.call_args_list[0][0][0]
    assert first_call_args[0] == "git"
    assert first_call_args[1] == "-C"
    assert first_call_args[3] == "pull"


from b1.core.exceptions import NetworkError

def test_fetch_git_url_raises_on_clone_failure(tmp_path):
    fetcher = _fetcher(tmp_path)
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr=b"auth failed")
        with pytest.raises(NetworkError):
            fetcher.fetch("https://github.com/org/my-module.git")
def test_fetch_by_name_with_library_path(tmp_path):
    # Setup library structure: lib/modules/framework/my-module
    lib_root = tmp_path / "lib"
    mod_dir = lib_root / "modules" / "framework" / "my-module"
    mod_dir.mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text("name: my-module", encoding="utf-8")
    
    fetcher = _fetcher(tmp_path)
    with patch.dict(os.environ, {"B1_LIBRARY_PATH": str(lib_root)}):
        result = fetcher.fetch("my-module")
        assert result == mod_dir


def test_fetch_by_name_discovers_sibling_llc_lib_repo(tmp_path, monkeypatch):
    # Simulate the umbrella workspace layout: a tool checkout and a sibling
    # "<name>-LLC-lib" repo, with no B1_LIBRARY_PATH configured.
    workspace = tmp_path / "workspace"
    tool_root = workspace / "b1CodingTool"
    fake_fetcher_file = tool_root / "src" / "b1" / "core" / "fetcher.py"

    overlay_root = workspace / "b1CodingTool-LLC-lib"
    mod_dir = overlay_root / "modules" / "llc-api-health"
    mod_dir.mkdir(parents=True)
    (mod_dir / "b1-module.yaml").write_text("name: llc-api-health", encoding="utf-8")

    monkeypatch.delenv("B1_LIBRARY_PATH", raising=False)
    monkeypatch.setattr("b1.core.fetcher.__file__", str(fake_fetcher_file))

    fetcher = _fetcher(tmp_path)
    result = fetcher.fetch("llc-api-health")
    assert result == mod_dir


def test_fetch_by_name_fallback_to_git(tmp_path):
    # lib_root exists but doesn't have the module
    lib_root = tmp_path / "lib"
    (lib_root / "modules").mkdir(parents=True)
    
    fetcher = _fetcher(tmp_path)
    with patch.dict(os.environ, {"B1_LIBRARY_PATH": str(lib_root)}):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            fetcher.fetch("https://github.com/org/my-module.git")
            
            # Should still try to clone because it wasn't in the library
            assert mock_run.called
            assert mock_run.call_args[0][0][1] == "clone"
