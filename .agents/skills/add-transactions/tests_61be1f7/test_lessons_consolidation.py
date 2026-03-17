"""Tests that keep add-transactions lessons concise and integration-oriented."""

import re

import pytest
from anyio import Path

"""Public symbols exported by this module (none)."""
__all__ = ()


async def _load_lessons_text() -> str:
    """Return the full text of the skill's lessons document."""
    path = Path(__file__).parents[1] / "lessons.md"
    return await path.read_text(encoding="utf-8")


def _dated_headings(text: str) -> list[str]:
    """Extract dated level-3 headings from the integrated archive."""
    pattern = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\b", re.MULTILINE)
    return pattern.findall(text)


@pytest.mark.anyio
async def test_lessons_has_limited_dated_entries() -> None:
    """The lessons file should stay short; older details belong in canonical docs."""
    text = await _load_lessons_text()
    headings = _dated_headings(text)
    assert len(headings) <= 8


@pytest.mark.anyio
async def test_each_dated_entry_is_integration_pointer() -> None:
    """Each dated archive entry must point to canonical files via Integrated arrows."""
    text = await _load_lessons_text()

    headings = list(re.finditer(r"^###\s+\d{4}-\d{2}-\d{2}\b.*$", text, re.MULTILINE))
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[start:end]
        assert "Integrated →" in section
