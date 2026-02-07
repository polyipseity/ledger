"""Tests for :mod:`scripts.format` helpers.

These tests exercise the property-based and example-based behaviour of the
formatting utilities (property tests use Hypothesis).
"""

from os import PathLike
from types import TracebackType
from typing import Self

import pytest
from anyio import Path
from hypothesis import given
from hypothesis import strategies as st

from scripts import format as fmt
from scripts.util.cache import JournalRunContext
from tests.conftest import RunModuleHelper

__all__ = ()


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


def test_sort_props_handles_empty_segments() -> None:
    """Comments containing empty segments or extra commas should not crash and should preserve key:value pairs."""
    line = "    account  ; a:1,, b:2, , c:3"
    out = fmt._sort_props(line)
    assert "a: 1" in out
    assert "b: 2" in out
    assert "c: 3" in out


def test_group_props_edge_cases() -> None:
    """Edge cases should still yield grouped and plain items as expected."""
    parts = list(fmt._group_props(["a:1", "b:2", "no-prop", "c:3"]))
    # Should yield grouped properties and plain items
    assert any(isinstance(p, list) for p in parts)
    assert any(isinstance(p, str) for p in parts)


# Property-based tests
@st.composite
def comment_parts(draw: st.DrawFn) -> list[str]:
    """Hypothesis strategy producing a mixture of key:value pairs and plain tokens."""
    # produce a sequence mixing key:value pairs and plain tokens
    parts: list[str] = []
    n: int = draw(st.integers(min_value=1, max_value=8))
    for _ in range(n):
        if draw(st.booleans()):
            k: str = draw(
                st.text(min_size=1, max_size=5).filter(lambda t: ":" not in t)
            )
            v: str = draw(
                st.text(min_size=0, max_size=5).filter(lambda t: "," not in t)
            )
            parts.append(f"{k}:{v}")
        else:
            token: str = draw(
                st.text(min_size=1, max_size=8).filter(lambda t: "," not in t)
            )
            parts.append(token)
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
def grouped_comment(draw: st.DrawFn) -> list[list[str] | str]:
    """Hypothesis strategy producing groups of key:value pairs or plain tokens."""
    # generate a sequence of 1-5 groups; each group is either a list of key:value pairs or a plain token
    parts: list[list[str] | str] = []
    count: int = draw(st.integers(min_value=1, max_value=5))
    for _ in range(count):
        if draw(st.booleans()):
            # group of 1-4 key:value pairs
            n: int = draw(st.integers(min_value=1, max_value=4))
            kvs: list[str] = []
            for _ in range(n):
                k: str = draw(
                    st.text(min_size=1, max_size=6).filter(
                        lambda t: ":" not in t and "," not in t
                    )
                )
                v: str = draw(
                    st.text(min_size=0, max_size=6).filter(
                        lambda t: "," not in t and ":" not in t
                    )
                )
                kvs.append(f"{k}:{v}")
            parts.append(kvs)
        else:
            # plain token
            tok: str = draw(
                st.text(min_size=1, max_size=8).filter(
                    lambda t: "," not in t and ":" not in t
                )
            )
            parts.append(tok)
    return parts


@given(grouped_comment())
def test_sort_props_sorts_keys_within_groups(
    parts: list[list[str] | str],
) -> None:
    """Groups of key:value properties are kept together and keys sorted."""
    # construct the comment string
    sections: list[str] = []

    for part in parts:
        if isinstance(part, list):
            joined = ", ".join(part)
        else:
            joined = part
        sections.append(joined)
    cmt = ", ".join(sections)
    line = f"    account  ; {cmt}"

    out = fmt._sort_props(line)
    assert out.startswith("    account  ;")

    # extract the comment text after '  ; '
    out_c = out.split("  ; ", 1)[1]
    out_parts: list[str] = [p.strip() for p in out_c.split(", ")]

    # Now check that for each original group of key:value pairs, the corresponding
    # group in out_parts has keys sorted alphabetically.
    # extract groups from out_parts: they are those parts that contain ':'
    found_groups: list[list[str]] = []
    current: list[str] = []
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
async def test_format_parser_invoke_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """The `format` parser's invoke wrapper should call :func:`format.main` with parsed args."""
    called: dict[str, fmt.Arguments] = {}

    async def fake_main(args: fmt.Arguments) -> None:
        called["args"] = args

    monkeypatch.setattr(fmt, "main", fake_main)
    p = fmt.parser()
    ns = p.parse_args(["--check", "file.journal"])

    await ns.invoke(ns)
    assert isinstance(called.get("args"), fmt.Arguments)
    assert called["args"].check is True


@pytest.mark.asyncio
async def test__format_journal_check_true_unformatted(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
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
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        """Fake hledger runner returning a synthetic formatted body for the test."""
        return ("FORMATTED BODY\nline2", "", 0)

    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    unformatted: list[PathLike[str]] = []

    class Session(JournalRunContext):
        """Minimal session stub used in tests to capture and expose reported journals.

        This stub avoids the normal JournalRunContext caching behaviour by
        initializing with an empty journal list and records successes by adding
        journals to the base class _reported set so tests can assert on `reported`.
        """

        def __init__(self) -> None:
            """Initialize without any journals to avoid cache behaviour."""
            # Avoid JournalRunContext cache behaviour; initialize with no journals
            super().__init__(Path(__file__), [])

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful formatting by adding `journal` to the reported set."""
            # Record to the base class _reported set so `reported` property reflects it
            self._reported.add(journal)

    await fmt._format_journal(jpath, unformatted, True, Session())

    # file should have been formatted on disk
    assert "FORMATTED BODY" in await jpath.read_text()
    # in check-mode the file is reported as unformatted
    assert jpath in unformatted


@pytest.mark.asyncio
async def test__format_journal_check_false_reports_success(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When run in non-check mode the session is reported as successful even if the file changes."""

    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        """Fake hledger runner returning a synthetic new body for the test."""
        return ("NEW BODY\n", "", 0)

    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    class Session(JournalRunContext):
        """Minimal session stub used in tests to capture and expose reported journals.

        This stub avoids the normal JournalRunContext caching behaviour by
        initializing with an empty journal list and records successes by adding
        journals to the base class _reported set so tests can assert on `reported`.
        """

        def __init__(self) -> None:
            """Initialize without any journals to avoid cache behaviour."""
            # Avoid JournalRunContext cache behaviour; initialize with no journals
            super().__init__(Path(__file__), [])

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful formatting by adding `journal` to the reported set."""
            # Record to the base class _reported set so `reported` property reflects it
            self._reported.add(journal)

    s = Session()
    await fmt._format_journal(jpath, [], False, s)
    # session.report_success should have been called for non-check invocation
    assert jpath in s.reported


@pytest.mark.asyncio
async def test_main_check_exits_with_1(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.LogCaptureFixture,
) -> None:
    """When running the `format` script with --check and unformatted files present, exit with code 1."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    # Make discovery return our test journal and ensure the run reports processing
    monkeypatch.setattr(fmt, "get_ledger_folder", lambda: repo)

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        return [jpath]

    monkeypatch.setattr(fmt, "find_monthly_journals", fake_find)

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        # Return a body that differs from disk causing a 'changed' and thus an unformatted entry
        return ("DIFFERENT BODY\n", "", 0)

    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    class DummyRun:
        """Stub JournalRunContext that marks our journal as to_process."""

        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            self.to_process = [jpath]
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            return self._reported

    monkeypatch.setattr(fmt, "JournalRunContext", DummyRun)

    with pytest.raises(SystemExit) as exc:
        await fmt.main(fmt.Arguments(check=True, files=None))
    assert exc.value.code == 1


@pytest.mark.asyncio
async def test_main_reports_processed_when_reported(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the session reports processed files, the top-level main should exercise the 'processed' logging branch."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        return [jpath]

    monkeypatch.setattr(fmt, "find_monthly_journals", fake_find)

    class DummyRun:
        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            self.to_process = []
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = [jpath]

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            return self._reported

    monkeypatch.setattr(fmt, "JournalRunContext", DummyRun)


@pytest.mark.asyncio
async def test_format_main_logs_skipped_when_skipped(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When JournalRunContext has skipped journals the top-level main should exercise the 'skipped' logging branch."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        return [jpath]

    monkeypatch.setattr(fmt, "find_monthly_journals", fake_find)

    class DummyRun2:
        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            self.to_process = []
            self.skipped: list[PathLike[str]] = [jpath]
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            return self._reported

    monkeypatch.setattr(fmt, "JournalRunContext", DummyRun2)

    # Should exit 0
    with pytest.raises(SystemExit) as exc:
        await fmt.main(fmt.Arguments(check=False, files=None))
    assert exc.value.code == 0


@pytest.mark.asyncio
async def test_main_check_with_no_unformatted(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When --check is used and files are already formatted, the main should exit 0 without listing files."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nFORMATTED BODY\n')

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        return [jpath]

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        return ("FORMATTED BODY\n", "", 0)

    monkeypatch.setattr(fmt, "find_monthly_journals", fake_find)
    monkeypatch.setattr(fmt, "run_hledger", fake_run_hledger)

    class Session:
        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            # create a minimal session where to_process contains our journal
            self.to_process = list(j)
            self.skipped = []
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            return self._reported

    monkeypatch.setattr(fmt, "JournalRunContext", Session)

    # Should exit with 0 since no unformatted files
    with pytest.raises(SystemExit) as exc:
        await fmt.main(fmt.Arguments(check=True, files=None))
    assert exc.value.code == 0


@pytest.mark.asyncio
async def test__format_journal_propagates_hledger_error(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If `hledger` returns a non-zero exit, `_format_journal` should propagate the CalledProcessError."""
    from subprocess import CalledProcessError

    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    jpath = repo / "2024-01" / "self.journal"
    await jpath.write_text('include "preludes/self.journal"\n\nold\n')

    async def error_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        raise CalledProcessError(3, ["hledger", "print"], output="", stderr="err")

    monkeypatch.setattr(fmt, "run_hledger", error_run_hledger)

    class Session(JournalRunContext):
        def __init__(self) -> None:
            super().__init__(Path(__file__), [])

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.add(journal)

    with pytest.raises(CalledProcessError):
        await fmt._format_journal(jpath, [], False, Session())


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should call :func:`asyncio.run` with the parser-invoked coroutine."""
    called = run_module_helper(
        "scripts.format", ["scripts.format"]
    )  # avoid pytest args
    assert called["ran"] is True
