"""CLI entrypoint for `act`."""

from __future__ import annotations

from pathlib import Path

import typer

from act import __version__
from act.config import find_default_manifest, load_act_toml
from act.sync import run_sync

_MANIFEST_HELP = "Manifest path (default: act.toml, else agent.toml, else pyproject.toml [tool.act])"


def _resolve_manifest(root: Path, file: Path | None) -> Path:
    """Return manifest path or raise typer.Exit with an error message."""
    mf = file if file is not None else find_default_manifest(root)
    if file is not None:
        if not mf.is_file():
            typer.echo(f"Error: manifest not found: {mf}", err=True)
            raise typer.Exit(1)
        return mf
    if mf is None or not mf.is_file():
        typer.echo(
            f"Error: no manifest in {root} (expected act.toml, agent.toml, "
            "or pyproject.toml with [tool.act] including [tool.act.project] name and description).",
            err=True,
        )
        raise typer.Exit(1)
    return mf

app = typer.Typer(
    help="Agent Configuration Toolkit — sync skills and CLI tools from a manifest",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _show_version(manifest: Path | None) -> None:
    root = Path.cwd()
    mf = manifest if manifest is not None else find_default_manifest(root)
    if mf is not None and mf.is_file():
        cfg = load_act_toml(mf)
        typer.echo(f"act-cli {__version__} — project: {cfg.project_name}")
    else:
        typer.echo(f"act-cli {__version__}")


@app.callback(invoke_without_command=True)
def cli_entry(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help=_MANIFEST_HELP,
    ),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-C",
        help="Project directory (default: current working directory)",
    ),
) -> None:
    """Without a subcommand, runs `sync` (same as `act sync`)."""
    if version:
        _show_version(file)
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        root = project_root or Path.cwd()
        mf = _resolve_manifest(root, file)
        cfg = load_act_toml(mf)
        run_sync(cfg, root)


@app.command("sync")
def sync_command(
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help=_MANIFEST_HELP,
    ),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-C",
        help="Project directory (default: current working directory)",
    ),
) -> None:
    """Apply manifest: install skills under .claude/skills/, then uv/npm tools."""
    root = project_root or Path.cwd()
    mf = _resolve_manifest(root, file)
    cfg = load_act_toml(mf)
    run_sync(cfg, root)


@app.command("version")
def version_command(
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help=_MANIFEST_HELP,
    ),
) -> None:
    """Print act-cli version and project name when a manifest is present."""
    _show_version(file)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
