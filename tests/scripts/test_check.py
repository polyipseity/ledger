"""Tests for :mod:`scripts.check`.

Ensure the CLI parser exposes the expected invocation hooks.
"""

from os import PathLike

import pytest
from anyio import Path

from scripts import check


def test_check_parser_invoke_callable() -> None:
    """Parser should attach an 'invoke' callable for the subcommand."""
    p = check.parser()
    ns = p.parse_args([])
    assert hasattr(ns, "invoke")


@pytest.mark.asyncio
async def test_check_main_runs_hledger_for_each_journal(
    tmp_path: PathLike, monkeypatch
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

    journals: list[PathLike] = [
        repo / "2024-01" / "a.journal",
        repo / "2024-02" / "b.journal",
    ]

    # Point ledger discovery at our temporary repo
    monkeypatch.setattr(check, "get_ledger_folder", lambda: repo)

    async def fake_find(folder: PathLike, files=None) -> list[PathLike]:
        return journals

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    calls = []

    async def fake_run_hledger(journal: PathLike, *args) -> tuple[str, str, int]:
        calls.append(journal)
        return ("", "", 0)

    monkeypatch.setattr(check, "run_hledger", fake_run_hledger)

    # Stub JournalRunContext so everything is treated as 'to_process'
    class DummyRun:
        def __init__(self, script_id: PathLike, j: list[PathLike]) -> None:
            self.to_process = list(j)
            self.skipped: list[PathLike] = []
            self._reported: list[PathLike] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def report_success(self, journal: PathLike) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike]:
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun)

    args = check.Arguments(files=None)

    with pytest.raises(SystemExit) as exc:
        await check.main(args)
    assert exc.value.code == 0
    # ensure run_hledger was called for both journals
    assert len(calls) == 2
