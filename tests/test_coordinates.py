import pytest

from act.coordinates import CoordKind, parse_coordinate


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
