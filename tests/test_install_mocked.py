"""Install paths using a fake repo tree (no network)."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from act.install import install_skill_from_coordinate, install_skill_from_source


def _fake_clone(fixture_src: Path, url: str, dest: Path) -> None:
    shutil.copytree(fixture_src, dest)


def test_subdir_skill_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SUBDIR: repo contains skills/foo/SKILL.md matching key."""
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: foo\ndescription: d\n---\n\n# Foo\n",
        encoding="utf-8",
    )

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        proj = tmp_path / "proj"
        proj.mkdir()
        install_skill_from_coordinate("foo", "o/r/skills/foo", proj)

    out = proj / ".claude" / "skills" / "foo" / "SKILL.md"
    assert out.is_file()
    assert "name: foo" in out.read_text(encoding="utf-8")


def test_name_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: other\ndescription: d\n---\n",
        encoding="utf-8",
    )

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        proj = tmp_path / "proj"
        proj.mkdir()
        with pytest.raises(ValueError, match="name mismatch"):
            install_skill_from_coordinate("foo", "o/r/skills/foo", proj)


# --- install_skill_from_source ---


def test_source_subdir_skill(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "docling"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: docling\ndescription: d\n---\n# Docling\n",
        encoding="utf-8",
    )

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, overwritten = install_skill_from_source(
            "o/r/skills/docling", target_dir=target
        )

    assert key == "docling"
    assert not overwritten
    assert (target / "docling" / "SKILL.md").is_file()


def test_source_repo_root(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    fixture.mkdir(parents=True)
    (fixture / "SKILL.md").write_text(
        "---\nname: my-repo\ndescription: d\n---\n# Root\n",
        encoding="utf-8",
    )
    (fixture / "README.md").write_text("hello", encoding="utf-8")

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, overwritten = install_skill_from_source(
            "org/my-repo", target_dir=target
        )

    assert key == "my-repo"
    assert not overwritten
    assert (target / "my-repo" / "SKILL.md").is_file()
    assert (target / "my-repo" / "README.md").is_file()


def test_source_single_file(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "tiny"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: tiny\ndescription: d\n---\n# Tiny\n",
        encoding="utf-8",
    )

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, overwritten = install_skill_from_source(
            "o/r/skills/tiny/SKILL.md", target_dir=target
        )

    assert key == "tiny"
    assert (target / "tiny" / "SKILL.md").is_file()


def test_source_missing_skill_md(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    (fixture / "some" / "path").mkdir(parents=True)
    (fixture / "some" / "path" / "README.md").write_text("no skill", encoding="utf-8")

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        with pytest.raises(FileNotFoundError, match="SKILL.md not found"):
            install_skill_from_source("o/r/some/path", target_dir=target)


def test_source_overwrite(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: foo\ndescription: d\n---\n# Foo v2\n",
        encoding="utf-8",
    )

    target = tmp_path / "skills"
    existing = target / "foo"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("old content", encoding="utf-8")

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, overwritten = install_skill_from_source(
            "o/r/skills/foo", target_dir=target
        )

    assert key == "foo"
    assert overwritten
    assert "Foo v2" in (target / "foo" / "SKILL.md").read_text(encoding="utf-8")


def test_source_custom_key_rewrites_name(tmp_path: Path) -> None:
    """--name rewrites the SKILL.md frontmatter name to keep folder and name in sync."""
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "docling"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: docling\ndescription: d\n---\n# Docling\n",
        encoding="utf-8",
    )

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, _ = install_skill_from_source(
            "o/r/skills/docling", target_dir=target, skill_key="my-alias"
        )

    assert key == "my-alias"
    installed_md = (target / "my-alias" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: my-alias" in installed_md


def test_source_github_url(tmp_path: Path) -> None:
    """Full GitHub URL is parsed and works end-to-end."""
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "plugins" / "core" / "skills" / "docling"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: docling\ndescription: d\n---\n# Docling\n",
        encoding="utf-8",
    )

    target = tmp_path / "skills"
    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        key, _ = install_skill_from_source(
            "https://github.com/org/repo/tree/main/plugins/core/skills/docling",
            target_dir=target,
        )

    assert key == "docling"
    assert (target / "docling" / "SKILL.md").is_file()
