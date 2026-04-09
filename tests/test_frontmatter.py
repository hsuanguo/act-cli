import pytest

from act.frontmatter import extract_name_field, rewrite_skill_name, validate_skill_name


def test_extract_name() -> None:
    md = """---
name: llm-wiki
description: test
---

# Hi
"""
    assert extract_name_field(md) == "llm-wiki"


def test_validate_match() -> None:
    md = """---
name: my-skill
---

x
"""
    validate_skill_name(md, "my-skill")


def test_validate_mismatch() -> None:
    md = """---
name: wrong
---

x
"""
    with pytest.raises(ValueError, match="name mismatch"):
        validate_skill_name(md, "my-skill")


def test_rewrite_name() -> None:
    md = "---\nname: old-name\ndescription: d\n---\n\n# Content\n"
    result = rewrite_skill_name(md, "new-name")
    assert "name: new-name" in result
    assert "old-name" not in result
    assert "description: d" in result
    assert "# Content" in result


def test_rewrite_name_no_frontmatter() -> None:
    md = "# Just a markdown file\nno frontmatter here"
    result = rewrite_skill_name(md, "new-name")
    assert result == md
