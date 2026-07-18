from pathlib import Path

_HEADINGS = {"rule": "## Guardrails", "edge-case": "## Edge cases"}
_FILES = {"project": ("project", "AGENTS.md"), "local": ("local", "AGENTS.md")}


def append_note(project_dir: Path, kind: str, text: str, scope: str) -> tuple[Path, bool]:
    """Append a bullet under the section for `kind` in the seed for `scope`.

    Returns (destination_path, appended). `appended` is False if the exact
    bullet already existed (dedup). Creates the heading if missing.
    """
    if kind not in _HEADINGS:
        raise ValueError(f"Unknown kind: {kind!r}")
    if scope not in _FILES:
        raise ValueError(f"Unknown scope: {scope!r}")

    heading = _HEADINGS[kind]
    sub, name = _FILES[scope]
    dest = project_dir / ".agents" / sub / name
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = dest.read_text(encoding="utf-8") if dest.exists() else ""
    bullet = f"- {text.strip()}"

    lines = content.splitlines()
    if bullet in lines:
        return dest, False

    if heading in lines:
        idx = lines.index(heading)
        # insert the bullet on the line directly after the heading (newest-first)
        lines.insert(idx + 1, bullet)
        new_content = "\n".join(lines) + "\n"
    else:
        prefix = content.rstrip("\n")
        joiner = "\n\n" if prefix else ""
        new_content = f"{prefix}{joiner}{heading}\n{bullet}\n"

    dest.write_text(new_content, encoding="utf-8")
    return dest, True
