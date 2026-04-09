"""Parse GitHub coordinate strings for skills."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


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
        raise ValueError("Full git URLs are not supported in v1; use owner/repo or owner/repo/path")

    parts = c.split("/")
    parts = [p for p in parts if p]
    if len(parts) < 2:
        raise ValueError(f"Expected owner/repo or owner/repo/path[/.../SKILL.md], got {coord!r}")

    owner, repo = parts[0], parts[1]
    if len(parts) == 2:
        return ParsedCoordinate(owner=owner, repo=repo, kind=CoordKind.REPO_ROOT, path_in_repo="")

    rest = "/".join(parts[2:])
    if rest.endswith("SKILL.md"):
        return ParsedCoordinate(
            owner=owner, repo=repo, kind=CoordKind.SINGLE_FILE, path_in_repo=rest
        )
    return ParsedCoordinate(owner=owner, repo=repo, kind=CoordKind.SUBDIR, path_in_repo=rest)


def parse_github_url(url: str) -> ParsedCoordinate:
    """Parse a full GitHub URL into a ParsedCoordinate.

    Supported formats:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - https://github.com/owner/repo/tree/<ref>/path/to/dir
      - https://github.com/owner/repo/blob/<ref>/path/to/SKILL.md
    """
    parsed = urlparse(url.strip())
    if parsed.hostname != "github.com":
        raise ValueError(
            f"Only GitHub URLs are supported, got host {parsed.hostname!r}"
        )

    segments = [s for s in parsed.path.split("/") if s]
    if len(segments) < 2:
        raise ValueError(f"GitHub URL must include owner/repo, got {url!r}")

    owner = segments[0]
    repo = segments[1].removesuffix(".git")

    if len(segments) == 2:
        return ParsedCoordinate(owner=owner, repo=repo, kind=CoordKind.REPO_ROOT, path_in_repo="")

    # segments[2] is "tree" or "blob"; segments[3] starts the ref.
    # The ref can contain slashes (e.g. feature/branch-name), so we can't
    # simply split at a fixed index.  Strategy: try each candidate split
    # point for where the ref ends and the in-repo path begins.  The first
    # segment after "tree|blob" that does NOT look like it continues a ref
    # is where the path starts.  Heuristic: ref segments don't contain "."
    # or known directory names is unreliable.  Instead we use the GitHub
    # API convention: the path component after the ref is the first segment
    # that, when joined with subsequent segments, forms a valid-looking
    # filesystem path.  Since we can't verify against the repo, we assume
    # a single-segment ref (the common case) and fall back if the caller
    # provides an explicit ref in the future.
    #
    # Practical approach: treat segments[3] as the ref (covers main, master,
    # v1.0, etc.).  For multi-segment refs like feature/foo, the user can
    # use the short-form coordinate instead.
    action = segments[2]  # "tree" or "blob"
    if action not in ("tree", "blob"):
        raise ValueError(
            f"Unexpected GitHub URL format (expected /tree/ or /blob/): {url!r}"
        )

    if len(segments) < 4:
        raise ValueError(f"GitHub URL with /{action}/ must include a ref: {url!r}")

    # ref = segments[3], path = segments[4:]
    rest_parts = segments[4:]
    if not rest_parts:
        return ParsedCoordinate(owner=owner, repo=repo, kind=CoordKind.REPO_ROOT, path_in_repo="")

    path_in_repo = "/".join(rest_parts)

    if action == "blob" and path_in_repo.endswith("SKILL.md"):
        return ParsedCoordinate(
            owner=owner, repo=repo, kind=CoordKind.SINGLE_FILE, path_in_repo=path_in_repo
        )
    return ParsedCoordinate(owner=owner, repo=repo, kind=CoordKind.SUBDIR, path_in_repo=path_in_repo)


def resolve_source(source: str) -> ParsedCoordinate:
    """Dispatch to parse_github_url or parse_coordinate based on input format."""
    s = source.strip()
    if s.startswith("https://") or s.startswith("http://"):
        return parse_github_url(s)
    return parse_coordinate(s)


def derive_skill_key(parsed: ParsedCoordinate) -> str:
    """Derive a skill directory name from a parsed coordinate.

    - SUBDIR  → last path segment (e.g. "docling" from "plugins/.../docling")
    - SINGLE_FILE → parent directory name (e.g. "my-skill" from ".../my-skill/SKILL.md")
    - REPO_ROOT → repository name
    """
    if parsed.kind is CoordKind.SUBDIR:
        return parsed.path_in_repo.rstrip("/").rsplit("/", 1)[-1]
    if parsed.kind is CoordKind.SINGLE_FILE:
        parent = parsed.path_in_repo.rsplit("/", 1)[0] if "/" in parsed.path_in_repo else ""
        return parent.rsplit("/", 1)[-1] if parent else parsed.repo
    return parsed.repo


def clone_url(parsed: ParsedCoordinate) -> str:
    return f"https://github.com/{parsed.owner}/{parsed.repo}.git"
