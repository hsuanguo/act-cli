"""Clone GitHub repos and install skills into .claude/skills/<key>/."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from act.coordinates import CoordKind, clone_url, parse_coordinate
from act.frontmatter import validate_skill_name


def _run_git_clone(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", url, str(dest)],
        check=True,
    )


def _replace_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def _copy_repo_root_non_dot(repo_root: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for entry in repo_root.iterdir():
        if entry.name.startswith("."):
            continue
        target = dst / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target)
        else:
            shutil.copy2(entry, target)


def install_skill_from_coordinate(
    skill_key: str,
    coordinate: str,
    project_root: Path,
) -> None:
    """Clone repo to a temp dir, copy skill files, delete temp dir."""
    parsed = parse_coordinate(coordinate)
    url = clone_url(parsed)
    tmp = Path(tempfile.mkdtemp(prefix="act-clone-"))
    repo_dir = tmp / "repo"
    target = project_root / ".claude" / "skills" / skill_key
    try:
        _run_git_clone(url, repo_dir)

        if parsed.kind is CoordKind.SINGLE_FILE:
            src_file = repo_dir / parsed.path_in_repo
            if not src_file.is_file():
                raise FileNotFoundError(
                    f"SKILL.md not found at {parsed.path_in_repo!r} in repository"
                )
            content = src_file.read_text(encoding="utf-8")
            validate_skill_name(content, skill_key)
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text(content, encoding="utf-8")
            return

        if parsed.kind is CoordKind.SUBDIR:
            src_dir = repo_dir / parsed.path_in_repo
            skill_md = src_dir / "SKILL.md"
            if not skill_md.is_file():
                raise FileNotFoundError(
                    f"SKILL.md not found under {parsed.path_in_repo!r} in repository"
                )
            content = skill_md.read_text(encoding="utf-8")
            validate_skill_name(content, skill_key)
            _replace_tree(src_dir, target)
            return

        # REPO_ROOT
        root_skill = repo_dir / "SKILL.md"
        if not root_skill.is_file():
            raise FileNotFoundError("No SKILL.md at repository root for owner/repo coordinate")
        content = root_skill.read_text(encoding="utf-8")
        validate_skill_name(content, skill_key)
        _copy_repo_root_non_dot(repo_dir, target)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
