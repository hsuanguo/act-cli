"""Optional network integration — run with ACT_INTEGRATION_TEST=1."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from act.install import install_skill_from_coordinate


@pytest.mark.skipif(
    not os.environ.get("ACT_INTEGRATION_TEST"),
    reason="Set ACT_INTEGRATION_TEST=1 to run (clones public GitHub)",
)
def test_shallow_clone_public_repo(tmp_path: Path) -> None:
    """Uses real git + network: tiny public repo path only."""
    proj = tmp_path / "proj"
    proj.mkdir()
    # Public template repo is heavy; use a known small path — may still be slow.
    install_skill_from_coordinate(
        "skill-creator",
        "anthropics/skills/skills/skill-creator",
        proj,
    )
    assert (proj / ".claude" / "skills" / "skill-creator" / "SKILL.md").is_file()
