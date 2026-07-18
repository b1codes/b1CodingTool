from pathlib import Path
from b1.core.notes import append_note


def _seed(project, scope):
    return project / ".agents" / scope / "AGENTS.md"


def _mk(tmp_path):
    for scope in ("project", "local"):
        (tmp_path / ".agents" / scope).mkdir(parents=True, exist_ok=True)
        _seed(tmp_path, scope).write_text("# Seed\n\n## Guardrails\n\n## Edge cases\n", encoding="utf-8")
    return tmp_path


def test_rule_appends_under_guardrails_in_project(tmp_path):
    _mk(tmp_path)
    dest, appended = append_note(tmp_path, "rule", "Never call prod API in tests", "project")
    assert appended is True
    assert dest == _seed(tmp_path, "project")
    body = dest.read_text(encoding="utf-8")
    assert "## Guardrails\n- Never call prod API in tests" in body


def test_edge_case_appends_under_edge_cases_in_local(tmp_path):
    _mk(tmp_path)
    dest, appended = append_note(tmp_path, "edge-case", "Redis must be running", "local")
    assert dest == _seed(tmp_path, "local")
    assert "## Edge cases\n- Redis must be running" in dest.read_text(encoding="utf-8")


def test_creates_heading_when_missing(tmp_path):
    (tmp_path / ".agents" / "project").mkdir(parents=True)
    _seed(tmp_path, "project").write_text("# Seed\n", encoding="utf-8")
    append_note(tmp_path, "rule", "Use 2-space indent", "project")
    assert "## Guardrails\n- Use 2-space indent" in _seed(tmp_path, "project").read_text(encoding="utf-8")


def test_dedup_exact_duplicate(tmp_path):
    _mk(tmp_path)
    append_note(tmp_path, "rule", "No force push", "project")
    dest, appended = append_note(tmp_path, "rule", "No force push", "project")
    assert appended is False
    assert dest.read_text(encoding="utf-8").count("- No force push") == 1
