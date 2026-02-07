"""Tests for :mod:`scripts.format` helpers.

These tests exercise the property-based and example-based behaviour of the
formatting utilities (property tests use Hypothesis).
"""

from os import PathLike
from typing import Literal

import pytest
from anyio import Path
from hypothesis import given
from hypothesis import strategies as st

from scripts import format as fmt
from scripts.util.cache import JournalRunContext


def test_group_props_and_sort_props() -> None:
    """Verify grouping and sorting of key:value properties in inline comments."""
    # A comment with ordered key:value pairs should be grouped and sorted
    line = "    account  ; b: 2, a: 1, free text, c: 3"
    out = fmt._sort_props(line)
    # properties should be sorted within their group (a then b then c)
    assert "a: 1" in out
    assert "b: 2" in out
    assert out.index("a: 1") < out.index("b: 2")
    assert "free text" in out

    # lines without `  ;` should return unchanged
    assert fmt._sort_props("no comment here") == "no comment here"


def test_group_props_edge_cases() -> None:
    """Edge cases should still yield grouped and plain items as expected."""
    parts = list(fmt._group_props(["a:1", "b:2", "no-prop", "c:3"]))
    # Should yield grouped properties and plain items
    assert any(isinstance(p, list) for p in parts)
    assert any(isinstance(p, str) for p in parts)


# Property-based tests
@st.composite
def comment_parts(draw: st.DrawFn) -> list[str]:
    # produce a sequence mixing key:value pairs and plain tokens
    parts: list[str] = []
    for _ in range(draw(st.integers(min_value=1, max_value=8))):
        if draw(st.booleans()):
            k = draw(st.text(min_size=1, max_size=5).filter(lambda t: ":" not in t))
            v = draw(st.text(min_size=0, max_size=5).filter(lambda t: "," not in t))
            parts.append(f"{k}:{v}")
        else:
            parts.append(
                draw(st.text(min_size=1, max_size=8).filter(lambda t: "," not in t))
            )
    return parts


@given(comment_parts())
def test_group_props_and_sort_props_roundtrip(parts: list[str]) -> None:
    """Round-trip property-based test: tokens are preserved and no errors occur."""
    cmt = ", ".join(parts)
    line = f"    account  ; {cmt}"
    out = fmt._sort_props(line)
    # should not raise and must contain all plain tokens
    for tok in [p for p in parts if ":" not in p]:
        assert tok.strip() in out


@st.composite
def grouped_comment(
    draw: st.DrawFn,
) -> list[tuple[Literal[True], list[str]] | tuple[Literal[False], str]]:
    # generate a sequence of 1-5 groups; each group is either a list of key:value pairs or a plain token
    parts: list[tuple[Literal[True], list[str]] | tuple[Literal[False], str]] = []
    for _ in range(draw(st.integers(min_value=1, max_value=5))):
        if draw(st.booleans()):
            # group of 1-4 key:value pairs
            n = draw(st.integers(min_value=1, max_value=4))
            kvs: list[str] = []
            for _ in range(n):
                k = draw(
                    st.text(min_size=1, max_size=6).filter(
                        lambda t: ":" not in t and "," not in t
                    )
                )
                v = draw(
                    st.text(min_size=0, max_size=6).filter(
                        lambda t: "," not in t and ":" not in t
                    )
                )
                kvs.append(f"{k}:{v}")
            partT: tuple[Literal[True], list[str]] = (True, kvs)
            parts.append(partT)
        else:
            # plain token
            tok = draw(
                st.text(min_size=1, max_size=8).filter(
                    lambda t: "," not in t and ":" not in t
                )
            )
            partF: tuple[Literal[False], str] = (False, tok)
            parts.append(partF)
    return parts


@given(grouped_comment())
def test_sort_props_sorts_keys_within_groups(
    parts: list[tuple[Literal[True], list[str]] | tuple[Literal[False], str]],
) -> None:
    """Groups of key:value properties are kept together and keys sorted."""
    # construct the comment string
    sections = []
    for is_group, val in parts:
        if is_group:
            sections.append(", ".join(val))
        else:
            sections.append(val)
    cmt = ", ".join(sections)
    line = f"    account  ; {cmt}"

    out = fmt._sort_props(line)
    assert out.startswith("    account  ;")

    # extract the comment text after '  ; '
    out_c = out.split("  ; ", 1)[1]
    out_parts = [p.strip() for p in out_c.split(", ")]

    # Now check that for each original group of key:value pairs, the corresponding
    # group in out_parts has keys sorted alphabetically.
    # extract groups from out_parts: they are those parts that contain ':'
    found_groups = []
    current = []
    for part in out_parts:
        if ":" in part:
            current.append(part)
        else:
            if current:
                found_groups.append(current)
                current = []
    if current:
        found_groups.append(current)

    # We only assert relative ordering: for each found group, keys must be sorted
    for grp in found_groups:
        keys = [g.split(":", 1)[0].strip() for g in grp]
        assert keys == sorted(keys)


def test_format_parser_check_flag() -> None:
    """Parser exposes the --check flag that maps to ns.check True."""
    p = fmt.parser()
    ns = p.parse_args(["--check"])
    assert ns.check is True


@pytest.mark.asyncio
async def test__format_journal_check_true_unformatted(
    tmp_path: PathLike, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When run in check mode, unformatted journals are returned in the list.

    The test uses the real file updater so the resulting formatted text is
    written and observed on disk; the session object is a minimal stub that
    captures reported successes.
    """

    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def fake_run_hledger(
        journal: PathLike, *args: object
    ) -> tuple[str, str, int]:
        return ("FORMATTED BODY\nline2", "", 0)

    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    unformatted = []

    class Session(JournalRunContext):
        def __init__(self) -> None:
            # Avoid JournalRunContext cache behaviour; initialize with no journals
            super().__init__(Path(__file__), [])

        def report_success(self, journal: PathLike) -> None:
            # Record to the base class _reported set so `reported` property reflects it
            self._reported.add(journal)

    await fmt._format_journal(jpath, unformatted, True, Session())

    # file should have been formatted on disk
    assert "FORMATTED BODY" in await jpath.read_text()
    # in check-mode the file is reported as unformatted
    assert jpath in unformatted


@pytest.mark.asyncio
async def test__format_journal_check_false_reports_success(
    tmp_path: PathLike, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When run in non-check mode the session is reported as successful even if the file changes."""

    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def fake_run_hledger(
        journal: PathLike, *args: object
    ) -> tuple[str, str, int]:
        return ("NEW BODY\n", "", 0)

    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    class Session(JournalRunContext):
        def __init__(self) -> None:
            # Avoid JournalRunContext cache behaviour; initialize with no journals
            super().__init__(Path(__file__), [])

        def report_success(self, journal: PathLike) -> None:
            # Record to the base class _reported set so `reported` property reflects it
            self._reported.add(journal)

    s = Session()
    await fmt._format_journal(jpath, [], False, s)
    # session.report_success should have been called for non-check invocation
    assert jpath in s.reported
