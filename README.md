# Agent Configuration Toolkit

<p align="center">
  <img src="assets/logo.svg" alt="act-cli" width="520" /><br />
</p>

Declare agent skills (from GitHub) and tools (`uv`, `npm`) in a manifest, then run **`act sync`** to materialize **`skills/`** and install tools. Works with most of major agents such as `claude code`, `cursor`, `github copilot` and `opencode`.

## Requirements

- **Python** 3.11+
- **Git** on `PATH` (for `git clone --depth 1`)
- **`uv`** / **`npm`** on `PATH` if you use `[dependencies.tools.uv]` / `[dependencies.tools.npm]`

## Quick Start

From this directory (standard **PEP 517** package; **pip** works too):

```bash
uv tool install .
# or editable:
uv tool install -e .
```

Development:

```bash
uv sync --all-extras
uv run act --help
uv run pytest
```

then run `act` where your manifest file is, that's all!

## Manifest

Supported filenames are **`act.toml`**, **`agent.toml`**, or config nested under **`[tool.act]`** in **`pyproject.toml`**. The layout is the same in each case; only the nesting differs for **`pyproject.toml`** (see the example below).

**Discovery (no `-f`):** from the project root (**`-C`**, default current directory), **`act`** uses the first match in this order:

1. **`act.toml`**
2. **`agent.toml`** (only if **`act.toml`** is absent)
3. **`pyproject.toml`** — only when **`[tool.act]`** exists and **`[tool.act.project]`** includes both **`name`** and **`description`** (so an ordinary Python **`pyproject.toml`** without **`[tool.act]`** is ignored)

**Layout:** standalone **`act.toml`** / **`agent.toml`** files use the top-level tables below. For **`pyproject.toml`**, mirror those tables under **`[tool.act]`** (e.g. **`[tool.act.project]`**, **`[tool.act.skills]`**, **`[tool.act.dependencies.tools.uv]`**).

```toml
[project]
name = "my-project"
description = "Local agent bundle"

[skills]
# TOML key = folder name under .claude/skills/<key>/
doc-coauthoring = "anthropics/skills/skills/doc-coauthoring"
# owner/repo — SKILL.md at repo root
# other = "org/single-skill-repo"
# Single-file skill path:
# tiny = "org/repo/docs/experimental/SKILL.md"

[dependencies.tools.uv]
ruff = "ruff@0.8.0"
lwiki = "git+https://github.com/hsuanguo/llm-wiki.git"

[dependencies.tools.npm]
prettier = "prettier@3"
```

Example nested under **`pyproject.toml`**:

```toml
[tool.act.project]
name = "my-vault"
description = "Local agent bundle"

[tool.act.skills]
llm-wiki = "hsuanguo/llm-wiki/skills/llm-wiki"

[tool.act.dependencies.tools.uv]
ruff = "ruff@0.8.0"
```

## Commands

| Command | Purpose |
|--------|---------|
| `act` | Same as **`act sync`** (default). |
| `act sync` | Read the resolved manifest, clone skills, copy into **`.claude/skills/<key>/`**, run **`uv tool install`** / **`npm -g install`**. |
| `act version` | Print version and **`[project].name`** when a manifest exists. |
| `act -f path/to.toml` | Use that manifest file (any `*.toml`; **`pyproject.toml`** uses **`[tool.act]`**). |
| `act -C /project/root` | Project root (default: cwd). |

## Coordinate forms

1. **`owner/repo`** — **`SKILL.md`** at repository root; non-hidden root files are copied into the skill dir.
2. **`owner/repo/path/to/skill-dir`** — directory containing **`SKILL.md`**; full directory copied.
3. **`owner/repo/.../SKILL.md`** — only that file is copied to **`.claude/skills/<key>/SKILL.md`**.

In every case, **`SKILL.md` frontmatter `name:`** must equal the TOML key.

## Re-running `act sync`

Each run will refresh the installed skills and tools.

## Compared to manual copy

You keep a single declarative file and a repeatable install path instead of copying trees and remembering **`uv` / `npm`** steps by hand. 
