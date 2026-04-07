from pathlib import Path

from act.config import find_default_manifest, load_act_toml


def test_load_nested_tool_tables(tmp_path: Path) -> None:
    p = tmp_path / "act.toml"
    p.write_text(
        """
[project]
name = "demo"
description = "test project"

[skills]
a = "x/y"

[dependencies.tools.uv]
ruff = "ruff@0.8.0"

[dependencies.tools.npm]
prettier = "prettier@3"
""",
        encoding="utf-8",
    )
    c = load_act_toml(p)
    assert c.project_name == "demo"
    assert c.skills == {"a": "x/y"}
    assert "ruff@0.8.0" in c.uv_tools
    assert "prettier@3" in c.npm_tools


def test_load_pyproject_tool_act(tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text(
        """
[project]
name = "root-package"
description = "Python package root"

[tool.act.project]
name = "demo"
description = "via tool.act"

[tool.act.skills]
a = "x/y"

[tool.act.dependencies.tools.uv]
ruff = "ruff@0.8.0"
""",
        encoding="utf-8",
    )
    c = load_act_toml(p)
    assert c.project_name == "demo"
    assert c.project_description == "via tool.act"
    assert c.skills == {"a": "x/y"}
    assert "ruff@0.8.0" in c.uv_tools


def test_find_default_manifest_priority(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.act.project]
name = "p"
description = "d"
""",
        encoding="utf-8",
    )
    assert find_default_manifest(tmp_path) == tmp_path / "pyproject.toml"

    (tmp_path / "agent.toml").write_text(
        """
[project]
name = "a"
description = "agent"

[skills]
x = "y/z"
""",
        encoding="utf-8",
    )
    assert find_default_manifest(tmp_path) == tmp_path / "agent.toml"

    (tmp_path / "act.toml").write_text(
        """
[project]
name = "act"
description = "act file"

[skills]
k = "u/v"
""",
        encoding="utf-8",
    )
    assert find_default_manifest(tmp_path) == tmp_path / "act.toml"


def test_pyproject_without_tool_act_not_selected(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "only"
description = "no tool.act"
""",
        encoding="utf-8",
    )
    assert find_default_manifest(tmp_path) is None
