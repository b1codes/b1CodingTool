from b1.core.snapshots import record_snapshots, check_drift, snapshot_for, tracked_files


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


def test_nested_tracked_path_round_trip(tmp_path):
    """Test that nested paths like .agents/rules/local.md are correctly
    recorded, retrieved, and drift-detected with / → __ flattening."""
    nested_file = tmp_path / ".agents/rules/local.md"
    content = "nested rules config\n"
    _write(nested_file, content)

    # Record snapshots
    record_snapshots(tmp_path)

    # snapshot_for should return the exact recorded content
    assert snapshot_for(tmp_path, nested_file) == content

    # Modify the file and verify drift detection
    modified_content = "nested rules config\n- modified\n"
    nested_file.write_text(modified_content, encoding="utf-8")
    drifted = check_drift(tmp_path)
    assert [p.name for p in drifted] == ["local.md"]


def test_tracked_files_direct_coverage(tmp_path):
    """Test that tracked_files() returns only existing tracked files,
    excluding non-tracked files."""
    # Create some tracked files
    _write(tmp_path / "AGENTS.md", "agents\n")
    _write(tmp_path / ".agents/rules/local.md", "rules\n")

    # Create a non-tracked file
    _write(tmp_path / "README.md", "readme\n")

    # tracked_files should return only the tracked ones
    result = tracked_files(tmp_path)
    result_names = sorted([p.name for p in result])
    assert result_names == ["AGENTS.md", "local.md"]

    # Verify the paths are correct (relative to project_dir)
    result_paths = sorted([p.relative_to(tmp_path).as_posix() for p in result])
    assert result_paths == [".agents/rules/local.md", "AGENTS.md"]
