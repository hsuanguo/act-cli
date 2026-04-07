import pytest

from act.frontmatter import extract_name_field, validate_skill_name


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
