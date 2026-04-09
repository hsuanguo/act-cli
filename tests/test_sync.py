"""Tests for run_sync tool installation and init command support."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import call, patch

import pytest
from click.exceptions import Exit

from act.config import ActConfig, ToolSpec
from act.sync import run_sync


def _cfg(
    uv_tools: list[ToolSpec] | None = None,
    npm_tools: list[ToolSpec] | None = None,
) -> ActConfig:
    return ActConfig(
        project_name="test",
        project_description="test project",
        skills={"a": "x/y"},
        uv_tools=uv_tools or [],
        npm_tools=npm_tools or [],
    )


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_uv_tool_without_init(mock_run, mock_install, tmp_path: Path) -> None:
    cfg = _cfg(uv_tools=[ToolSpec(spec="ruff@0.8.0")])
    run_sync(cfg, tmp_path)

    mock_run.assert_called_once_with(
        ["uv", "tool", "install", "ruff@0.8.0"], check=True, cwd=tmp_path
    )


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_uv_tool_with_init(mock_run, mock_install, tmp_path: Path, capsys) -> None:
    cfg = _cfg(uv_tools=[ToolSpec(spec="docling", init="docling --help")])
    run_sync(cfg, tmp_path)

    assert mock_run.call_count == 2
    mock_run.assert_any_call(
        ["uv", "tool", "install", "docling"], check=True, cwd=tmp_path
    )
    mock_run.assert_any_call(
        "docling --help", shell=True, check=True, cwd=tmp_path
    )

    captured = capsys.readouterr()
    assert "Initializing 'docling' (this may take a while)" in captured.out
    assert "Initialized 'docling'" in captured.out


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_npm_tool_with_init(mock_run, mock_install, tmp_path: Path, capsys) -> None:
    cfg = _cfg(npm_tools=[ToolSpec(spec="mytool@1", init="mytool setup")])
    run_sync(cfg, tmp_path)

    assert mock_run.call_count == 2
    mock_run.assert_any_call(
        ["npm", "-g", "install", "mytool@1"], check=True, cwd=tmp_path
    )
    mock_run.assert_any_call(
        "mytool setup", shell=True, check=True, cwd=tmp_path
    )

    captured = capsys.readouterr()
    assert "Initializing 'mytool@1' (this may take a while)" in captured.out
    assert "Initialized 'mytool@1'" in captured.out


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_init_order_after_install(mock_run, mock_install, tmp_path: Path) -> None:
    """Init command runs after install, not before."""
    cfg = _cfg(uv_tools=[ToolSpec(spec="docling", init="docling --help")])
    run_sync(cfg, tmp_path)

    calls = mock_run.call_args_list
    assert calls[0] == call(["uv", "tool", "install", "docling"], check=True, cwd=tmp_path)
    assert calls[1] == call("docling --help", shell=True, check=True, cwd=tmp_path)


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_init_failure_raises_exit(mock_run, mock_install, tmp_path: Path) -> None:
    """If init command fails, sync exits with the error code."""

    def side_effect(*args, **kwargs):
        if kwargs.get("shell"):
            raise subprocess.CalledProcessError(42, "docling --help")

    mock_run.side_effect = side_effect
    cfg = _cfg(uv_tools=[ToolSpec(spec="docling", init="docling --help")])

    with pytest.raises(Exit):
        run_sync(cfg, tmp_path)


@patch("act.sync.install_skill_from_coordinate")
@patch("act.sync.subprocess.run")
def test_mixed_tools_with_and_without_init(mock_run, mock_install, tmp_path: Path) -> None:
    cfg = _cfg(uv_tools=[
        ToolSpec(spec="ruff@0.8.0"),
        ToolSpec(spec="docling", init="docling --help"),
    ])
    run_sync(cfg, tmp_path)

    # ruff: 1 call (install only), docling: 2 calls (install + init)
    assert mock_run.call_count == 3
