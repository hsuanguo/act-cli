"""Parse GitHub coordinate strings for skills."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CoordKind(Enum):
    REPO_ROOT = "repo_root"  # owner/repo — skill at repository root
    SUBDIR = "subdir"  # owner/repo/path/to/skill-dir
    SINGLE_FILE = "single_file"  # owner/repo/.../SKILL.md


@dataclass(frozen=True)
class ParsedCoordinate:
    owner: str
    repo: str
    kind: CoordKind
    """Path within repo: empty for repo root; posix-style relative path."""
    path_in_repo: str


def parse_coordinate(coord: str) -> ParsedCoordinate:
    c = coord.strip()
    if not c:
        raise ValueError("Empty coordinate")

    if c.startswith("git@") or c.startswith("https://") or c.startswith("http://"):
        raise ValueError(
            "Full git URLs are not supported in v1; use owner/repo or owner/repo/path"
        )

    parts = c.split("/")
    parts = [p for p in parts if p]
    if len(parts) < 2:
        raise ValueError(
            "Expected owner/repo or owner/repo/path[/.../SKILL.md], "
            f"got {coord!r}"
        )

    owner, repo = parts[0], parts[1]
    if len(parts) == 2:
        return ParsedCoordinate(
            owner=owner, repo=repo, kind=CoordKind.REPO_ROOT, path_in_repo=""
        )

    rest = "/".join(parts[2:])
    if rest.endswith("SKILL.md"):
        return ParsedCoordinate(
            owner=owner, repo=repo, kind=CoordKind.SINGLE_FILE, path_in_repo=rest
        )
    return ParsedCoordinate(
        owner=owner, repo=repo, kind=CoordKind.SUBDIR, path_in_repo=rest
    )


def clone_url(parsed: ParsedCoordinate) -> str:
    return f"https://github.com/{parsed.owner}/{parsed.repo}.git"
