"""Tests for :mod:`scripts.check`.

Ensure the CLI parser exposes the expected invocation hooks.
"""

from builtins import BaseExceptionGroup
from collections.abc import Iterable
from os import PathLike
from subprocess import CalledProcessError
from types import TracebackType
from typing import Self, Sequence

import pytest
from anyio import Path

from scripts import check
from tests.conftest import RunModuleHelper

__all__ = ()


def test_check_parser_invoke_callable() -> None:
    """Parser should attach an 'invoke' callable for the subcommand."""
    p = check.parser()
    ns = p.parse_args([])
    assert hasattr(ns, "invoke")


@pytest.mark.asyncio
async def test_check_parser_invoke_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser's `invoke` should call :func:`check.main` with parsed args."""
    called: dict[str, object] = {}

    async def fake_main(args: check.Arguments) -> None:
        """Fake `check.main` used to capture arguments passed by the parser."""
        called["args"] = args

    monkeypatch.setattr(check, "main", fake_main)
    p = check.parser()
    ns = p.parse_args([])

    await ns.invoke(ns)
    assert isinstance(called.get("args"), check.Arguments)


@pytest.mark.asyncio
async def test_check_main_runs_hledger_for_each_journal(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
):
    """Main should invoke `run_hledger` for each journal that requires processing.

    This test stubs out the discovery and the JournalRunContext so the
    behaviour of `main` can be observed without touching global cache files.
    """
    # Create a simple ledger with two monthly journals
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")
    await (repo / "2024-02").mkdir(parents=True)
    await (repo / "2024-02" / "b.journal").write_text("y")

    journals: Sequence[PathLike[str]] = [
        repo / "2024-01" / "a.journal",
        repo / "2024-02" / "b.journal",
    ]

    # Point ledger discovery at our temporary repo
    monkeypatch.setattr(check, "get_ledger_folder", lambda: repo)

    async def fake_find(
        folder: PathLike[str], files: Iterable[str] | None = None
    ) -> Sequence[PathLike[str]]:
        """Fake discovery implementation that returns the local test journals list."""
        return journals

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    calls: list[PathLike[str]] = []

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        """Fake hledger runner used by tests to capture invocation without subprocesses."""
        calls.append(journal)
        return ("", "", 0)

    monkeypatch.setattr(check, "run_hledger", fake_run_hledger)

    # Stub JournalRunContext so everything is treated as 'to_process'
    class DummyRun:
        """A minimal JournalRunContext stub used by tests to emulate session behaviour."""

        def __init__(
            self, script_id: PathLike[str], j: Sequence[PathLike[str]]
        ) -> None:
            """Initialize with a list of journals to process and empty reported/skipped lists."""
            self.to_process = list(j)
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            """Async context manager entry: return self for use in tests."""
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            """Async context manager exit: no cleanup required in tests."""
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful journal processing for assertions in tests."""
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            """Return the list of reported journals for test assertions."""
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun)

    args = check.Arguments(files=None)

    with pytest.raises(SystemExit) as exc:
        await check.main(args)
    assert exc.value.code == 0
    # ensure run_hledger was called for both journals
    assert len(calls) == 2, "run_hledger should be invoked for both discovered journals"


@pytest.mark.asyncio
async def test_check_logs_skipped_when_skipped(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When JournalRunContext has skipped journals, the 'skipped' info branch should be exercised."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> Sequence[PathLike[str]]:
        """Fake discovery used by this test to return the single journal path."""
        return [repo / "2024-01" / "a.journal"]

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    class DummyRun3:
        """JournalRunContext stub used in tests to simulate skipped journals."""

        def __init__(
            self, script_id: PathLike[str], j: Sequence[PathLike[str]]
        ) -> None:
            """Initialize with no journals to process and one skipped journal."""
            self.to_process = []
            self.skipped = [repo / "2024-01" / "a.journal"]
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            """Async context entry: return self for use in tests."""
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            """Async context exit: no cleanup required in tests."""
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful journal processing for assertions in tests."""
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            """Return the list of reported journals for test assertions."""
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun3)

    with pytest.raises(SystemExit) as exc:
        await check.main(check.Arguments(files=None))
    assert exc.value.code == 0


@pytest.mark.asyncio
async def test_check_propagates_hledger_errors(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If `run_hledger` raises CalledProcessError the exception should propagate from `main`."""

    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")

    journals = [repo / "2024-01" / "a.journal"]

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> Sequence[PathLike[str]]:
        """Fake discovery returning the local journals list used in this test."""
        return journals

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    async def error_run_hledger(journal: PathLike[str], *args: object):
        """Fake run_hledger that raises CalledProcessError to exercise error path."""
        raise CalledProcessError(2, ["hledger", "check"], output="", stderr="fail")

    monkeypatch.setattr(check, "run_hledger", error_run_hledger)

    class DummyRun:
        """A minimal JournalRunContext stub used by tests to emulate session behaviour."""

        def __init__(
            self, script_id: PathLike[str], j: Sequence[PathLike[str]]
        ) -> None:
            """Initialize with a list of journals to process and empty reported/skipped lists."""
            self.to_process = list(j)
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            """Async context manager entry: return self for use in tests."""
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            """Async context manager exit: no cleanup required in tests."""
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful journal processing for assertions in tests."""
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            """Return the list of reported journals for test assertions."""
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun)

    with pytest.raises(BaseExceptionGroup) as eg:
        await check.main(check.Arguments(files=None))
    # ensure the wrapped exception is the CalledProcessError we raised
    assert any(isinstance(e, CalledProcessError) for e in eg.value.exceptions)


@pytest.mark.asyncio
async def test_check_logs_processed_when_reported(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the JournalRunContext reports processed items, the main function logs the 'processed' summary branch."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> Sequence[PathLike[str]]:
        """Fake discovery returning the single test journal path for this case."""
        return [repo / "2024-01" / "a.journal"]

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    class DummyRun2:
        """JournalRunContext stub used to simulate reported journals in tests."""

        def __init__(
            self, script_id: PathLike[str], j: Sequence[PathLike[str]]
        ) -> None:
            """Initialize with pre-populated reported list for assertions."""
            self.to_process = []
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = [repo / "2024-01" / "a.journal"]

        async def __aenter__(self) -> Self:
            """Async context entry: return the stub instance."""
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            """Async context exit: no special cleanup required for the stub."""
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            """Record successful processing in the stub's reported list."""
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            """Return the stub's reported list for assertions."""
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun2)

    # should run and complete without raising
    with pytest.raises(SystemExit) as exc:
        await check.main(check.Arguments(files=None))
    assert exc.value.code == 0


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should call :func:`asyncio.run` with the parser-invoked coroutine."""
    called = run_module_helper("scripts.check", ["scripts.check"])  # avoid pytest args
    assert called["ran"] is True
