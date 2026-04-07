"""Minimal YAML frontmatter helpers for SKILL.md."""

from __future__ import annotations


def extract_name_field(content: str) -> str | None:
    """Return `name` from YAML frontmatter, or None."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    block = "\n".join(lines[1:end])
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("name:"):
            val = stripped.split(":", 1)[1].strip()
            if val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            if val.startswith("'") and val.endswith("'"):
                return val[1:-1]
            return val
    return None


def validate_skill_name(content: str, skill_key: str) -> None:
    name = extract_name_field(content)
    if name is None:
        raise ValueError("SKILL.md must contain YAML frontmatter with a 'name' field")
    if name != skill_key:
        raise ValueError(
            f"SKILL.md name mismatch: frontmatter has name={name!r} but act.toml key is {skill_key!r}"
        )
