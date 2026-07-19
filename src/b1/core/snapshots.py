import shutil
from pathlib import Path
from typing import List, Optional

SNAPSHOT_DIR = ".agents/.b1-snapshots"

# Generated files whose content maps to a seed — drift-tracked in v1.
TRACKED = [
    "AGENTS.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "AGENTS.override.md",
    ".agents/rules/local.md",
]


def _snap_name(rel: str) -> str:
    return rel.replace("/", "__")


def _snap_dir(project_dir: Path) -> Path:
    return project_dir / SNAPSHOT_DIR


def tracked_files(project_dir: Path) -> List[Path]:
    return [project_dir / rel for rel in TRACKED if (project_dir / rel).exists()]


def record_snapshots(project_dir: Path) -> None:
    """Copy each existing tracked file into the snapshot dir; prune snapshots
    for tracked files that no longer exist."""
    snap = _snap_dir(project_dir)
    snap.mkdir(parents=True, exist_ok=True)
    for rel in TRACKED:
        f = project_dir / rel
        target = snap / _snap_name(rel)
        if f.exists():
            shutil.copyfile(f, target)
        elif target.exists():
            target.unlink()


def snapshot_for(project_dir: Path, path: Path) -> Optional[str]:
    rel = path.relative_to(project_dir).as_posix()
    target = _snap_dir(project_dir) / _snap_name(rel)
    return target.read_text(encoding="utf-8") if target.exists() else None


def check_drift(project_dir: Path) -> List[Path]:
    """Tracked files that exist, have a snapshot, and differ from it."""
    drifted = []
    for rel in TRACKED:
        f = project_dir / rel
        if not f.exists():
            continue
        snap = snapshot_for(project_dir, f)
        if snap is None:
            continue  # no baseline yet -> not drift
        if f.read_text(encoding="utf-8") != snap:
            drifted.append(f)
    return drifted
