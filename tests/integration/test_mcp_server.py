import pytest
import yaml
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from b1.server.mcp_server import mcp

@pytest.mark.asyncio
async def test_mcp_init(tmp_path):
    """Test the b1_init tool via MCP."""
    # FastMCP uses list_tools()
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "b1_init" in tool_names

@pytest.mark.asyncio
async def test_mcp_resources():
    """Test that MCP resources are registered."""
    resources = await mcp.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    assert "b1://context/compiled" in resource_uris
    assert "b1://config/project" in resource_uris
    assert "b1://modules/library" in resource_uris

@pytest.mark.asyncio
async def test_b1_status_uninitialized(tmp_path, monkeypatch):
    """Test b1_status tool output when project is not initialized."""
    monkeypatch.chdir(tmp_path)
    # Call the underlying function directly for testing
    from b1.server.mcp_server import b1_status
    result = b1_status()
    assert "error" in result
    assert "Not a b1CodingTool project" in result


def test_b1_pair_default_agents_are_gemini_free(make_project, monkeypatch):
    """Regression: b1_pair used to default empty active_agents to
    ["CLAUDE", "GEMINI"] and persist it. GEMINI has been retired: the
    default must no longer be written to config.yaml, and GEMINI.md must
    never be produced."""
    project = make_project()
    monkeypatch.chdir(project)

    # make_project always sets active_agents, so force the empty-config
    # scenario (the branch b1_pair defaults) explicitly.
    config_path = project / ".agents" / "config.yaml"
    config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config_data["active_agents"] = []
    config_path.write_text(yaml.dump(config_data), encoding="utf-8")

    from b1.server.mcp_server import b1_pair
    result = b1_pair()

    assert not (project / "GEMINI.md").exists()
    assert (project / "CLAUDE.md").exists()

    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert "GEMINI" not in persisted["active_agents"]
    assert "GEMINI" not in result


def test_b1_pair_records_snapshots_no_false_drift(make_project, monkeypatch):
    """Regression: b1_pair used to bypass record_snapshots, leaving the
    baseline stale so a later CLI `b1 pair` falsely raised DriftError.
    Seed a matching baseline, change the source so a regenerate legitimately
    differs, then run b1_pair: it must refresh the snapshot to match."""
    from b1.core.snapshots import check_drift
    from b1.commands.pair import run_pair

    project = make_project(agents=["CLAUDE"])
    monkeypatch.chdir(project)

    run_pair(project, ["CLAUDE"])  # seed an initial, matching baseline
    (project / ".agents" / "project" / "AGENTS.md").write_text(
        "# Project\nchanged rule\n", encoding="utf-8"
    )

    from b1.server.mcp_server import b1_pair
    result = b1_pair()

    assert "changed rule" in (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert check_drift(project) == []
    assert "reconcile" not in result.lower()


def test_b1_pair_returns_reconcile_message_on_drift(make_project, monkeypatch):
    """Regression: b1_pair used to bypass check_drift and would silently
    overwrite a hand-edit. It must now report the drift and point the user
    at `b1 reconcile` via the returned string (MCP tools communicate via
    strings, not HTTP status codes)."""
    project = make_project(agents=["CLAUDE"])
    monkeypatch.chdir(project)

    from b1.server.mcp_server import b1_pair
    b1_pair()  # first run records snapshots

    (project / "CLAUDE.md").write_text("hand edited\n", encoding="utf-8")

    result = b1_pair()
    assert "CLAUDE.md" in result
    assert "reconcile" in result.lower()


@pytest.mark.asyncio
async def test_get_compiled_context_returns_str(make_project, monkeypatch):
    """The MCP resource must return a plain string, not a CompiledContext
    object, so MCP clients can render it directly."""
    project = make_project()
    monkeypatch.chdir(project)

    from b1.server.mcp_server import get_compiled_context
    result = get_compiled_context()
    assert isinstance(result, str)
