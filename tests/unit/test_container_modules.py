"""Tests for the `containers` module group: docker, apple-container, orbstack."""
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from b1.core.fetcher import ModuleFetcher
from b1.core.schema import ModuleConfig, ModuleType

MODULES_ROOT = Path(__file__).resolve().parents[2] / "modules"
CONTAINERS_ROOT = MODULES_ROOT / "containers"


def _load(module_name: str) -> ModuleConfig:
    return ModuleConfig.from_yaml(CONTAINERS_ROOT / module_name / "b1-module.yaml")


@pytest.mark.parametrize(
    "module_name,expected_type,expected_command_prefix",
    [
        ("docker", ModuleType.deployment, "/docker"),
        ("apple-container", ModuleType.development, "/apple-container"),
        ("orbstack", ModuleType.development, "/orbstack"),
    ],
)
def test_container_module_manifest_parses(module_name, expected_type, expected_command_prefix):
    config = _load(module_name)
    assert config.name == module_name
    assert config.type == expected_type
    assert len(config.skills) >= 2, f"{module_name} should declare at least 2 skills"
    assert len(config.commands) >= 2, f"{module_name} should declare at least 2 commands"
    assert all(
        c.name.startswith(expected_command_prefix) for c in config.commands
    ), f"all commands in {module_name} should start with {expected_command_prefix}"
    assert config.hooks.get("post-install") == "scripts/post-install.sh"


@pytest.mark.parametrize(
    "module_name,expected_files",
    [
        (
            "docker",
            [
                "context/best-practices.md",
                "context/python-conventions.md",
                "context/runtime.md",
                "context/agent-capabilities.md",
                "scripts/post-install.sh",
                "skills/docker-init.md",
                "templates/dockerfile-python.tmpl",
                "templates/compose-postgres.tmpl",
                "templates/compose-redis.tmpl",
                "templates/compose-db-backup.tmpl",
            ],
        ),
        (
            "apple-container",
            [
                "context/best-practices.md",
                "context/conventions.md",
                "context/agent-capabilities.md",
                "scripts/post-install.sh",
                "templates/dev-containers.sh.tmpl",
                "templates/config.toml.tmpl",
            ],
        ),
        (
            "orbstack",
            [
                "context/best-practices.md",
                "context/conventions.md",
                "context/agent-capabilities.md",
                "scripts/post-install.sh",
                "templates/compose.orbstack.yaml.tmpl",
            ],
        ),
    ],
)
def test_container_module_files_exist(module_name, expected_files):
    module_dir = CONTAINERS_ROOT / module_name
    missing = [f for f in expected_files if not (module_dir / f).is_file()]
    assert not missing, f"{module_name} is missing: {missing}"


@pytest.mark.parametrize("module_name", ["docker", "apple-container", "orbstack"])
def test_post_install_succeeds_without_runtime(module_name, tmp_path):
    """A missing runtime is informational — the hook must never fail `b1 install`.

    HookEngine runs post-install with check=True, so a non-zero exit would be
    reported as an install error. An empty PATH simulates a machine with no
    container tooling installed.
    """
    script = CONTAINERS_ROOT / module_name / "scripts" / "post-install.sh"
    result = subprocess.run(
        [str(script)],
        cwd=tmp_path,
        env={"PATH": str(tmp_path), "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    if module_name == "orbstack" and Path("/Applications/OrbStack.app").is_dir():
        return  # the app-bundle fallback detects OrbStack even with an empty PATH
    assert "not found" in result.stdout


def test_dev_containers_template_is_valid_bash():
    template = CONTAINERS_ROOT / "apple-container" / "templates" / "dev-containers.sh.tmpl"
    result = subprocess.run(["bash", "-n", str(template)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_module_names_are_unique_across_groups():
    """Name-based install globs `modules/**/<name>` and takes the first hit,
    so two modules sharing a name in different groups would silently shadow each other."""
    names = [
        ModuleConfig.from_yaml(manifest).name
        for manifest in MODULES_ROOT.glob("*/*/b1-module.yaml")
    ]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    assert not duplicates, f"duplicate module names: {duplicates}"


def test_docker_resolves_by_name_after_move(monkeypatch):
    """`b1 install docker` must keep working now that the module lives under containers/."""
    monkeypatch.delenv("B1_LIBRARY_PATH", raising=False)
    assert ModuleFetcher().fetch("docker") == CONTAINERS_ROOT / "docker"
