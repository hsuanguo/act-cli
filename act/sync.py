"""Orchestrate sync from a loaded ActConfig."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from act.config import ActConfig
from act.install import install_skill_from_coordinate


def run_sync(cfg: ActConfig, project_root: Path) -> None:
    if not cfg.skills:
        typer.echo(
            "Error: [skills] is missing or empty. Add at least one skill entry in your manifest.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        for key, coord in cfg.skills.items():
            typer.echo(f"Skill {key!r} ← {coord!r}")
            install_skill_from_coordinate(key, coord, project_root)

        for spec in cfg.uv_tools:
            typer.echo(f"uv tool install {spec!r} …")
            subprocess.run(["uv", "tool", "install", spec], check=True, cwd=project_root)

        for spec in cfg.npm_tools:
            typer.echo(f"npm -g install {spec!r} …")
            subprocess.run(["npm", "-g", "install", spec], check=True, cwd=project_root)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error: external command failed with exit code {e.returncode}", err=True)
        raise typer.Exit(e.returncode) from e

    typer.echo("act: sync complete.")
