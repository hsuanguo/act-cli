"""End-to-end tests for `act get-skill` (mocked git clone)."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from act.cli import app

runner = CliRunner()


def _fake_clone(fixture_src: Path, url: str, dest: Path) -> None:
    shutil.copytree(fixture_src, dest)


def _make_skill_fixture(tmp_path: Path, subpath: str, name: str) -> Path:
    """Create a fake repo with a SKILL.md at the given subpath."""
    fixture = tmp_path / "upstream"
    skill_dir = fixture / subpath
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n# {name}\n",
        encoding="utf-8",
    )
    return fixture


# --- happy paths ---


def test_get_skill_short_coordinate(tmp_path: Path) -> None:
    fixture = _make_skill_fixture(tmp_path, "skills/docling", "docling")
    proj = tmp_path / "proj"
    proj.mkdir()

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        result = runner.invoke(app, ["get-skill", "org/repo/skills/docling", "-C", str(proj)])

    assert result.exit_code == 0, result.output
    assert "Installed skill 'docling'" in result.output
    assert (proj / ".claude" / "skills" / "docling" / "SKILL.md").is_file()


def test_get_skill_github_url(tmp_path: Path) -> None:
    fixture = _make_skill_fixture(tmp_path, "plugins/core/skills/docling", "docling")
    proj = tmp_path / "proj"
    proj.mkdir()

    url = "https://github.com/org/repo/tree/main/plugins/core/skills/docling"
    with patch("act.install._run_git_clone", lambda url_, dest: _fake_clone(fixture, url_, dest)):
        result = runner.invoke(app, ["get-skill", url, "-C", str(proj)])

    assert result.exit_code == 0, result.output
    assert "Installed skill 'docling'" in result.output
    assert (proj / ".claude" / "skills" / "docling" / "SKILL.md").is_file()


def test_get_skill_global_flag(tmp_path: Path) -> None:
    fixture = _make_skill_fixture(tmp_path, "skills/foo", "foo")
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()

    with (
        patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)),
        patch("act.cli.Path.home", return_value=fake_home),
    ):
        result = runner.invoke(app, ["get-skill", "--global", "org/repo/skills/foo"])

    assert result.exit_code == 0, result.output
    assert "Installed skill 'foo'" in result.output
    assert (fake_home / ".claude" / "skills" / "foo" / "SKILL.md").is_file()


def test_get_skill_name_override_rewrites(tmp_path: Path) -> None:
    fixture = _make_skill_fixture(tmp_path, "skills/docling", "docling")
    proj = tmp_path / "proj"
    proj.mkdir()

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        result = runner.invoke(
            app, ["get-skill", "org/repo/skills/docling", "--name", "my-alias", "-C", str(proj)]
        )

    assert result.exit_code == 0, result.output
    assert "Installed skill 'my-alias'" in result.output
    skill_md = proj / ".claude" / "skills" / "my-alias" / "SKILL.md"
    assert skill_md.is_file()
    assert "name: my-alias" in skill_md.read_text(encoding="utf-8")


def test_get_skill_overwrite_warning(tmp_path: Path) -> None:
    fixture = _make_skill_fixture(tmp_path, "skills/foo", "foo")
    proj = tmp_path / "proj"
    proj.mkdir()
    existing = proj / ".claude" / "skills" / "foo"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("old", encoding="utf-8")

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        result = runner.invoke(app, ["get-skill", "org/repo/skills/foo", "-C", str(proj)])

    assert result.exit_code == 0, result.output
    assert "Warning: overwritten existing skill" in result.output
    assert "Installed skill 'foo'" in result.output


# --- error cases ---


def test_get_skill_missing_skill_md(tmp_path: Path) -> None:
    fixture = tmp_path / "upstream"
    (fixture / "some" / "path").mkdir(parents=True)
    (fixture / "some" / "path" / "README.md").write_text("nope", encoding="utf-8")

    proj = tmp_path / "proj"
    proj.mkdir()

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        result = runner.invoke(app, ["get-skill", "org/repo/some/path", "-C", str(proj)])

    assert result.exit_code == 1
    assert "SKILL.md not found" in result.output


def test_get_skill_name_override_different_name(tmp_path: Path) -> None:
    """--name with a different name rewrites SKILL.md instead of erroring."""
    fixture = _make_skill_fixture(tmp_path, "skills/docling", "docling")
    proj = tmp_path / "proj"
    proj.mkdir()

    with patch("act.install._run_git_clone", lambda url, dest: _fake_clone(fixture, url, dest)):
        result = runner.invoke(
            app, ["get-skill", "org/repo/skills/docling", "--name", "custom-name", "-C", str(proj)]
        )

    assert result.exit_code == 0, result.output
    assert "Installed skill 'custom-name'" in result.output
    skill_md = proj / ".claude" / "skills" / "custom-name" / "SKILL.md"
    assert skill_md.is_file()
    assert "name: custom-name" in skill_md.read_text(encoding="utf-8")
