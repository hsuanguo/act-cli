# AGENTS.md

This file provides guidance when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --all-extras

# Run the CLI
uv run act --help
uv run act                        # Sync skills from manifest in cwd
uv run act sync -f path/act.toml  # Sync with a specific manifest file
uv run act version

# Tests
uv run pytest                     # All tests
uv run pytest tests/test_config.py::test_load_nested_tool_tables  # Single test
ACT_INTEGRATION_TEST=1 uv run pytest  # Include real-network integration test

# Lint & format
uv run ruff check .
uv run ruff format .
```

## Architecture

**act-cli** is a manifest-driven CLI tool that installs AI agent skills (Markdown-based prompt files) from GitHub repositories into `.claude/skills/<key>/`, and optionally installs associated CLI tools via `uv` or `npm`.

**Data flow:** Manifest file → parse config → for each skill: parse GitHub coordinate → `git clone` → validate frontmatter → copy files → cleanup → run `uv`/`npm` installs.

**Module responsibilities:**

| Module | Role |
|--------|------|
| `act/cli.py` | Typer app with `sync` and `version` commands |
| `act/config.py` | Load & validate manifest (`act.toml`, `agent.toml`, or `pyproject.toml [tool.act]`) |
| `act/coordinates.py` | Parse GitHub coordinate strings into `ParsedCoordinate` (three formats: repo root, subdir, single file) |
| `act/frontmatter.py` | Extract YAML frontmatter from `SKILL.md`; validate that `name` matches the manifest key |
| `act/install.py` | Clone repo → copy files → validate → clean up temp dir |
| `act/sync.py` | Orchestrate all installs; invoke `uv tool install` / `npm -g install` for tool dependencies |

**Manifest discovery order:** `act.toml` → `agent.toml` → `pyproject.toml` (under `[tool.act]`).

**Coordinate formats** (value in `[skills]`):
- `owner/repo` — entire repo root
- `owner/repo/path/to/dir` — subdirectory
- `owner/repo/path/to/SKILL.md` — single file
