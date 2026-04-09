"""Load and validate act manifests (act.toml, agent.toml, or pyproject.toml [tool.act])."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolSpec:
    spec: str
    init: str | None = None


@dataclass
class ActConfig:
    project_name: str
    project_description: str
    skills: dict[str, str]
    uv_tools: list[ToolSpec]
    npm_tools: list[ToolSpec]


def _parse_tool_entries(d: dict[str, Any] | None) -> list[ToolSpec]:
    if not d:
        return []
    result: list[ToolSpec] = []
    for key, val in d.items():
        if isinstance(val, str):
            result.append(ToolSpec(spec=val))
        elif isinstance(val, dict):
            spec = val.get("spec")
            if not spec or not isinstance(spec, str):
                raise ValueError(
                    f"Tool entry {key!r}: inline table must include a 'spec' string"
                )
            init = val.get("init")
            if init is not None and not isinstance(init, str):
                raise ValueError(f"Tool entry {key!r}: 'init' must be a string")
            result.append(ToolSpec(spec=spec.strip(), init=init.strip() if init else None))
        else:
            raise ValueError(f"Tool entry {key!r}: expected a string or inline table")
    return result


def _parse_act_root(data: dict[str, Any]) -> ActConfig:
    proj = data.get("project") or {}
    if not isinstance(proj, dict):
        raise ValueError("Invalid [project] table")

    name = str(proj.get("name", "")).strip()
    desc = str(proj.get("description", "")).strip()
    if not name:
        raise ValueError("[project].name is required")
    if not desc:
        raise ValueError("[project].description is required")

    skills_raw = data.get("skills")
    if not isinstance(skills_raw, dict):
        skills_raw = {}
    skills: dict[str, str] = {
        str(k): str(v).strip() for k, v in skills_raw.items() if str(v).strip()
    }

    deps = data.get("dependencies") or {}
    if not isinstance(deps, dict):
        deps = {}
    tools = deps.get("tools") or {}
    if not isinstance(tools, dict):
        tools = {}

    uv_tbl = tools.get("uv")
    npm_tbl = tools.get("npm")

    uv_tools = _parse_tool_entries(uv_tbl if isinstance(uv_tbl, dict) else None)
    npm_tools = _parse_tool_entries(npm_tbl if isinstance(npm_tbl, dict) else None)

    return ActConfig(
        project_name=name,
        project_description=desc,
        skills=skills,
        uv_tools=uv_tools,
        npm_tools=npm_tools,
    )


def load_act_toml(path: Path) -> ActConfig:
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))

    if path.name == "pyproject.toml":
        tool = data.get("tool") or {}
        if not isinstance(tool, dict):
            raise ValueError("pyproject.toml: missing or invalid [tool] table")
        act = tool.get("act")
        if not isinstance(act, dict):
            raise ValueError(
                "pyproject.toml: missing [tool.act] — add act config under [tool.act] "
                "(same keys as act.toml: project, skills, dependencies.tools, …)"
            )
        data = act

    return _parse_act_root(data)


def _pyproject_has_usable_tool_act(data: dict[str, Any]) -> bool:
    tool = data.get("tool") or {}
    if not isinstance(tool, dict):
        return False
    act = tool.get("act")
    if not isinstance(act, dict):
        return False
    proj = act.get("project") or {}
    if not isinstance(proj, dict):
        return False
    name = str(proj.get("name", "")).strip()
    desc = str(proj.get("description", "")).strip()
    return bool(name and desc)


def find_default_manifest(cwd: Path) -> Path | None:
    """First match: ``act.toml``, then ``agent.toml``, then ``pyproject.toml`` with ``[tool.act]``."""
    for name in ("act.toml", "agent.toml"):
        p = cwd / name
        if p.is_file():
            return p
    pp = cwd / "pyproject.toml"
    if not pp.is_file():
        return None
    try:
        data = tomllib.loads(pp.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if _pyproject_has_usable_tool_act(data):
        return pp
    return None


def default_manifest_path(cwd: Path) -> Path:
    """Preferred default filename for messages (``act.toml``). Discovery uses :func:`find_default_manifest`."""
    return cwd / "act.toml"
