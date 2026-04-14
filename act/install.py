"""Clone GitHub repos and install skills into .claude/skills/<key>/."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from act.coordinates import CoordKind, clone_url, derive_skill_key, parse_coordinate, resolve_source
from act.frontmatter import rewrite_skill_name, validate_skill_name


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


def _rewrite_skill_md_name(skill_md: Path, new_name: str) -> None:
    """Rewrite the ``name`` field in a SKILL.md to *new_name*."""
    content = skill_md.read_text(encoding="utf-8")
    updated = rewrite_skill_name(content, new_name)
    skill_md.write_text(updated, encoding="utf-8")


def install_skill_from_source(
    source: str,
    target_dir: Path,
    skill_key: str | None = None,
) -> tuple[str, bool]:
    """Fetch a skill from a GitHub URL or short coordinate.

    When *skill_key* is provided the SKILL.md ``name`` frontmatter field is
    rewritten to match so the folder name and internal name stay in sync.

    Returns (resolved_key, was_overwrite).
    """
    parsed = resolve_source(source)
    key = skill_key or derive_skill_key(parsed)
    url = clone_url(parsed)
    target = target_dir / key
    overwritten = target.exists()
    needs_rename = skill_key is not None

    tmp = Path(tempfile.mkdtemp(prefix="act-clone-"))
    repo_dir = tmp / "repo"
    try:
        _run_git_clone(url, repo_dir)

        if parsed.kind is CoordKind.SINGLE_FILE:
            src_file = repo_dir / parsed.path_in_repo
            if not src_file.is_file():
                raise FileNotFoundError(
                    f"SKILL.md not found at {parsed.path_in_repo!r} in repository"
                )
            content = src_file.read_text(encoding="utf-8")
            if needs_rename:
                content = rewrite_skill_name(content, key)
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text(content, encoding="utf-8")
            return key, overwritten

        if parsed.kind is CoordKind.SUBDIR:
            src_dir = repo_dir / parsed.path_in_repo
            skill_md = src_dir / "SKILL.md"
            if not skill_md.is_file():
                raise FileNotFoundError(
                    f"SKILL.md not found under {parsed.path_in_repo!r} in repository"
                )
            if needs_rename:
                _rewrite_skill_md_name(skill_md, key)
            _replace_tree(src_dir, target)
            return key, overwritten

        # REPO_ROOT
        root_skill = repo_dir / "SKILL.md"
        if not root_skill.is_file():
            raise FileNotFoundError("No SKILL.md at repository root for owner/repo coordinate")
        if needs_rename:
            _rewrite_skill_md_name(root_skill, key)
        _copy_repo_root_non_dot(repo_dir, target)
        return key, overwritten
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
