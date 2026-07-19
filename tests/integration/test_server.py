# tests/integration/test_server.py
import pytest
from fastapi.testclient import TestClient
from b1.server.main import app


# TestClient from fastapi/starlette runs the ASGI app in-process — no real server.
# Path.cwd() is set by cd_project/monkeypatch.chdir before each test.

@pytest.fixture
def client(cd_project):
    with TestClient(app) as c:
        yield c


def test_get_project_returns_name_and_initialized_true(client, cd_project):
    resp = client.get("/api/project")
    assert resp.status_code == 200
    data = resp.json()
    assert data["initialized"] is True
    assert data["name"] == cd_project.name


def test_get_config_returns_config_shape(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "upstream_repo" in data
    assert "active_agents" in data


def test_get_modules_returns_empty_list_with_no_modules(client):
    resp = client.get("/api/modules")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_modules_returns_installed_modules(make_project, monkeypatch):
    project = make_project(modules=["django"])
    monkeypatch.chdir(project)
    with TestClient(app) as client:
        resp = client.get("/api/modules")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "django" in names


def test_get_context_returns_compiled_content(client):
    resp = client.get("/api/context")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert isinstance(data["content"], str)
    assert "Project-specific context" in data["content"]


def test_get_context_returns_400_when_not_initialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        resp = client.get("/api/context")
    assert resp.status_code == 400


def test_init_project_creates_agent_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        resp = client.post("/api/project/init")
    assert resp.status_code == 200
    assert (tmp_path / ".agents").exists()


def test_update_config_saves_to_file(client, cd_project):
    resp = client.put("/api/config", json={"upstream_repo": "my/repo", "active_agents": ["GEMINI"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["upstream_repo"] == "my/repo"
    assert data["active_agents"] == ["GEMINI"]
    
    # Verify file was written
    from b1.core.config import B1Config
    config = B1Config.load(cd_project)
    assert config.upstream_repo == "my/repo"


def test_install_module_fetches_and_installs(client, cd_project, tmp_path):
    # Mock a module source
    source = tmp_path / "my-mod"
    source.mkdir()
    import yaml
    (source / "b1-module.yaml").write_text(yaml.dump({"name": "my-mod", "version": "1.0.0", "type": "development"}), encoding="utf-8")
    (source / "context").mkdir()
    
    resp = client.post("/api/modules/install", json={"source": str(source)})
    assert resp.status_code == 200
    assert (cd_project / ".agents" / "modules" / "my-mod").exists()


def test_pair_context_generates_agent_files(client, cd_project):
    # Configure agents first
    client.put("/api/config", json={"active_agents": ["CLAUDE"]})

    resp = client.post("/api/context/pair")
    assert resp.status_code == 200
    assert not (cd_project / "GEMINI.md").exists()
    assert (cd_project / "CLAUDE.md").exists()


def test_pair_context_updates_active_agents_if_provided(client, cd_project):
    resp = client.post("/api/context/pair", json={"agents": ["CLAUDE"]})
    assert resp.status_code == 200
    assert (cd_project / "CLAUDE.md").exists()

    # Verify config was updated
    resp_config = client.get("/api/config")
    assert resp_config.json()["active_agents"] == ["CLAUDE"]


def test_pair_context_records_snapshots_no_false_drift(client, cd_project):
    """Regression: the server pair path used to bypass record_snapshots,
    leaving the baseline stale. Simulate a pre-existing baseline (e.g. from
    an earlier CLI pair), change the source so a regenerate legitimately
    produces different output, then pair via the server: it must refresh
    the snapshot to match, leaving check_drift() clean. Before the fix, the
    server never records a snapshot, so the *old* baseline stays stale
    against the newly regenerated file and check_drift() falsely reports
    drift here (which would then falsely halt the next CLI `b1 pair`)."""
    from b1.core.snapshots import check_drift
    from b1.commands.pair import run_pair

    run_pair(cd_project, ["CLAUDE"])  # seed an initial, matching baseline

    (cd_project / ".agents" / "project" / "AGENTS.md").write_text(
        "# Project\nchanged rule\n", encoding="utf-8"
    )

    resp = client.post("/api/context/pair", json={"agents": ["CLAUDE"]})
    assert resp.status_code == 200
    assert "changed rule" in (cd_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert check_drift(cd_project) == []


def test_pair_context_returns_success_on_empty_compile(tmp_path, monkeypatch):
    """Regression/contract test: when run_pair returns False (empty compile --
    no project seed, local seed, github metadata, or modules to compile), the
    server must fall through to its existing success response rather than
    erroring. This is the intentionally-preserved pre-Phase-3 contract; it had
    no test coverage before."""
    (tmp_path / ".agents").mkdir()
    monkeypatch.chdir(tmp_path)

    with TestClient(app) as client:
        resp = client.post("/api/context/pair", json={"agents": ["CLAUDE"]})

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "agents": ["CLAUDE"]}
    # Confirm the compile really was empty: no agent file was generated.
    assert not (tmp_path / "CLAUDE.md").exists()


def test_pair_context_halts_409_on_handedit(client, cd_project):
    """Regression: the server pair path used to bypass check_drift and would
    silently overwrite a hand-edit. It must now halt with 409 and point the
    user at `b1 reconcile`."""
    resp = client.post("/api/context/pair", json={"agents": ["CLAUDE"]})
    assert resp.status_code == 200

    (cd_project / "CLAUDE.md").write_text("hand edited\n", encoding="utf-8")

    resp2 = client.post("/api/context/pair", json={"agents": ["CLAUDE"]})
    assert resp2.status_code == 409
    detail = resp2.json()["detail"]
    assert "CLAUDE.md" in detail
    assert "reconcile" in detail
