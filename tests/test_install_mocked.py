"""Install paths using a fake repo tree (no network)."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from act.install import install_skill_from_coordinate


def _fake_clone(fixture_src: Path, url: str, dest: Path) -> None:
    shutil.copytree(fixture_src, dest)


def test_subdir_skill_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SUBDIR: repo contains skills/foo/SKILL.md matching key."""
    fixture = tmp_path / "upstream"
    skill_dir = fixture / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        '---\nname: foo\ndescription: d\n---\n\n# Foo\n',
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
        '---\nname: other\ndescription: d\n---\n',
        encoding="utf-8",
    )

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        proj = tmp_path / "proj"
        proj.mkdir()
        with pytest.raises(ValueError, match="name mismatch"):
            install_skill_from_coordinate("foo", "o/r/skills/foo", proj)
