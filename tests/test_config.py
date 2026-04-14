from pathlib import Path

import pytest

from act.config import ToolSpec, find_default_manifest, load_act_toml


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
    assert any(t.spec == "ruff@0.8.0" for t in c.uv_tools)
    assert any(t.spec == "prettier@3" for t in c.npm_tools)


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
    assert any(t.spec == "ruff@0.8.0" for t in c.uv_tools)


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


# --- ToolSpec parsing ---


def test_tool_string_values_produce_toolspec(tmp_path: Path) -> None:
    p = tmp_path / "act.toml"
    p.write_text(
        """
[project]
name = "t"
description = "d"

[skills]
a = "x/y"

[dependencies.tools.uv]
ruff = "ruff@0.8.0"
lwiki = "git+https://github.com/hsuanguo/llm-wiki.git"
""",
        encoding="utf-8",
    )
    c = load_act_toml(p)
    assert len(c.uv_tools) == 2
    assert all(isinstance(t, ToolSpec) for t in c.uv_tools)
    assert all(t.init is None for t in c.uv_tools)


def test_tool_inline_table_with_init(tmp_path: Path) -> None:
    p = tmp_path / "act.toml"
    p.write_text(
        """
[project]
name = "t"
description = "d"

[skills]
a = "x/y"

[dependencies.tools.uv]
ruff = "ruff@0.8.0"
docling = { spec = "docling", init = "docling --help" }
""",
        encoding="utf-8",
    )
    c = load_act_toml(p)
    assert len(c.uv_tools) == 2
    plain = [t for t in c.uv_tools if t.spec == "ruff@0.8.0"][0]
    assert plain.init is None
    with_init = [t for t in c.uv_tools if t.spec == "docling"][0]
    assert with_init.init == "docling --help"


def test_tool_inline_table_without_init(tmp_path: Path) -> None:
    p = tmp_path / "act.toml"
    p.write_text(
        """
[project]
name = "t"
description = "d"

[skills]
a = "x/y"

[dependencies.tools.uv]
mytools = { spec = "mytool@1.0" }
""",
        encoding="utf-8",
    )
    c = load_act_toml(p)
    assert len(c.uv_tools) == 1
    assert c.uv_tools[0].spec == "mytool@1.0"
    assert c.uv_tools[0].init is None


def test_tool_inline_table_missing_spec_raises(tmp_path: Path) -> None:
    p = tmp_path / "act.toml"
    p.write_text(
        """
[project]
name = "t"
description = "d"

[skills]
a = "x/y"

[dependencies.tools.uv]
bad = { init = "bad --help" }
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must include a 'spec' string"):
        load_act_toml(p)
