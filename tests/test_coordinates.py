import pytest

from act.coordinates import (
    CoordKind,
    derive_skill_key,
    parse_coordinate,
    parse_github_url,
    resolve_source,
)


# --- parse_coordinate (existing) ---


def test_parse_owner_repo() -> None:
    p = parse_coordinate("anthropics/skills")
    assert p.owner == "anthropics"
    assert p.repo == "skills"
    assert p.kind is CoordKind.REPO_ROOT
    assert p.path_in_repo == ""


def test_parse_subdir() -> None:
    p = parse_coordinate("anthropics/skills/skills/llm-wiki")
    assert p.kind is CoordKind.SUBDIR
    assert p.path_in_repo == "skills/llm-wiki"


def test_parse_single_file() -> None:
    p = parse_coordinate("foo/bar/path/to/SKILL.md")
    assert p.kind is CoordKind.SINGLE_FILE
    assert p.path_in_repo == "path/to/SKILL.md"


def test_rejects_bare_url() -> None:
    with pytest.raises(ValueError, match="Full git URLs"):
        parse_coordinate("https://github.com/a/b")


# --- parse_github_url ---


def test_github_url_tree_subdir() -> None:
    p = parse_github_url(
        "https://github.com/existential-birds/beagle/tree/main/plugins/beagle-core/skills/docling"
    )
    assert p.owner == "existential-birds"
    assert p.repo == "beagle"
    assert p.kind is CoordKind.SUBDIR
    assert p.path_in_repo == "plugins/beagle-core/skills/docling"


def test_github_url_blob_skill_md() -> None:
    p = parse_github_url(
        "https://github.com/org/repo/blob/main/skills/my-skill/SKILL.md"
    )
    assert p.owner == "org"
    assert p.repo == "repo"
    assert p.kind is CoordKind.SINGLE_FILE
    assert p.path_in_repo == "skills/my-skill/SKILL.md"


def test_github_url_bare_repo() -> None:
    p = parse_github_url("https://github.com/org/single-skill-repo")
    assert p.owner == "org"
    assert p.repo == "single-skill-repo"
    assert p.kind is CoordKind.REPO_ROOT
    assert p.path_in_repo == ""


def test_github_url_bare_repo_with_git_suffix() -> None:
    p = parse_github_url("https://github.com/org/repo.git")
    assert p.owner == "org"
    assert p.repo == "repo"
    assert p.kind is CoordKind.REPO_ROOT
    assert p.path_in_repo == ""


def test_github_url_tree_root_only() -> None:
    """tree/<ref> with no path after ref → REPO_ROOT."""
    p = parse_github_url("https://github.com/org/repo/tree/main")
    assert p.kind is CoordKind.REPO_ROOT
    assert p.path_in_repo == ""


def test_github_url_rejects_non_github() -> None:
    with pytest.raises(ValueError, match="Only GitHub URLs"):
        parse_github_url("https://gitlab.com/org/repo/tree/main/skill")


def test_github_url_rejects_unexpected_action() -> None:
    with pytest.raises(ValueError, match="Unexpected GitHub URL format"):
        parse_github_url("https://github.com/org/repo/issues/123")


# --- resolve_source ---


def test_resolve_source_url() -> None:
    p = resolve_source("https://github.com/org/repo/tree/main/skills/foo")
    assert p.owner == "org"
    assert p.repo == "repo"
    assert p.kind is CoordKind.SUBDIR


def test_resolve_source_short_coordinate() -> None:
    p = resolve_source("org/repo/skills/foo")
    assert p.owner == "org"
    assert p.repo == "repo"
    assert p.kind is CoordKind.SUBDIR
    assert p.path_in_repo == "skills/foo"


# --- derive_skill_key ---


def test_derive_key_subdir() -> None:
    from act.coordinates import ParsedCoordinate

    p = ParsedCoordinate(owner="o", repo="r", kind=CoordKind.SUBDIR, path_in_repo="path/to/my-skill")
    assert derive_skill_key(p) == "my-skill"


def test_derive_key_single_file() -> None:
    from act.coordinates import ParsedCoordinate

    p = ParsedCoordinate(
        owner="o", repo="r", kind=CoordKind.SINGLE_FILE, path_in_repo="skills/my-skill/SKILL.md"
    )
    assert derive_skill_key(p) == "my-skill"


def test_derive_key_repo_root() -> None:
    from act.coordinates import ParsedCoordinate

    p = ParsedCoordinate(owner="org", repo="awesome-skill", kind=CoordKind.REPO_ROOT, path_in_repo="")
    assert derive_skill_key(p) == "awesome-skill"
