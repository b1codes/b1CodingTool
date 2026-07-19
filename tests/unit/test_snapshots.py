from b1.core.snapshots import record_snapshots, check_drift, snapshot_for


def _write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_no_drift_right_after_record(tmp_path):
    _write(tmp_path / "AGENTS.md", "generated\n")
    _write(tmp_path / "CLAUDE.md", "generated\n")
    record_snapshots(tmp_path)
    assert check_drift(tmp_path) == []


def test_detects_handedit(tmp_path):
    _write(tmp_path / "AGENTS.md", "generated\n")
    record_snapshots(tmp_path)
    (tmp_path / "AGENTS.md").write_text("generated\n- my hand edit\n", encoding="utf-8")
    drifted = check_drift(tmp_path)
    assert [p.name for p in drifted] == ["AGENTS.md"]


def test_file_without_snapshot_is_not_drift(tmp_path):
    # no record_snapshots call -> a freshly generated file is not "drift"
    _write(tmp_path / "AGENTS.md", "generated\n")
    assert check_drift(tmp_path) == []


def test_snapshot_for_returns_recorded_content(tmp_path):
    _write(tmp_path / "CLAUDE.md", "v1\n")
    record_snapshots(tmp_path)
    assert snapshot_for(tmp_path, tmp_path / "CLAUDE.md") == "v1\n"


def test_record_prunes_snapshot_when_file_removed(tmp_path):
    f = tmp_path / "AGENTS.override.md"
    _write(f, "personal\n")
    record_snapshots(tmp_path)
    f.unlink()
    record_snapshots(tmp_path)
    assert snapshot_for(tmp_path, f) is None
