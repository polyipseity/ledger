"""Tests for the :mod:`scripts.clopen_verify` monthly boundary verifier.

Every fixture writes a real journal and drives the verifier through the real
managed ``hledger`` binary, so the assertions also pin the hledger JSON field
names the module parses.
"""

from calendar import monthrange
from collections.abc import Sequence
from os import PathLike
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from scripts import clopen_verify

"""Public symbols exported by this module (none)."""
__all__ = ()


"""Account declarations shared by every fixture journal.

The verifier decides which accounts a closing must zero from
``hledger accounts --types``, so the types are declared explicitly rather than
left to hledger's name inference.
"""
_DECLARATIONS = """\
account assets:bank                ; type: A
account assets:cash                ; type: C
account equity:opening/closing balances
account expenses:food              ; type: X
"""


"""A clean April whose opening, activity, and closing all agree."""
_CLEAN_APRIL = """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD = 0.00 HKD
    equity:opening/closing balances   90.00 HKD
"""


def _write_named(folder: Path, month: str, name: str, text: str) -> Path:
    """Write ``text`` as ``folder/<month>/<name>``, declarations included."""
    directory = folder / month
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(f"{_DECLARATIONS}\n{text}")
    return path


def _write_journal(folder: Path, month: str, text: str) -> Path:
    """Write ``text`` as the monthly journal ``folder/<month>/self.journal``.

    Returns the journal path so a test can pass it straight to the verifier.
    """
    return _write_named(folder, month, "self.journal", text)


def _clean_month(month: str, balance: str) -> str:
    """Return a boundary-only journal for ``month`` whose cash opens at ``balance``.

    The balancing side is left unstated, so hledger infers it and the month
    stays clean whatever the opening balance is.
    """
    year, number = month.split("-")
    last = f"{month}-{monthrange(int(year), int(number))[1]:02d}"
    return (
        f"{month}-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00\n"
        f"    assets:cash                      {balance} HKD = {balance} HKD\n"
        "    equity:opening/closing balances\n"
        "\n"
        f"{last} closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00\n"
        f"    assets:cash                     -{balance} HKD = 0.00 HKD\n"
        "    equity:opening/closing balances\n"
    )


def _kinds(defects: Sequence[clopen_verify.Defect]) -> list[tuple[str, str]]:
    """Return the (month, kind) pair of every defect, for compact assertions."""
    return [(defect.month, defect.kind) for defect in defects]


@pytest.mark.anyio
async def test_clean_chain_reports_nothing(tmp_path: PathLike[str]) -> None:
    """A month whose opening and closing match its activity yields no defect."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                       90.00 HKD = 90.00 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -60.00 HKD = 0.00 HKD
    equity:opening/closing balances   60.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april, may], "2026-06")

    assert list(defects) == []


@pytest.mark.anyio
async def test_missing_closing_reported(tmp_path: PathLike[str]) -> None:
    """A month before the current one without a closing reports the omission."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "missing_closing")]


@pytest.mark.anyio
async def test_missing_opening_reported(tmp_path: PathLike[str]) -> None:
    """A month before the current one without an opening reports the omission."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                       10.00 HKD = 0.00 HKD
    equity:opening/closing balances  -10.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "missing_opening")]


@pytest.mark.anyio
async def test_opening_mismatch_reported(tmp_path: PathLike[str]) -> None:
    """An opening one cent away from negating the previous closing is reported."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                       90.01 HKD = 90.01 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -60.01 HKD = 0.00 HKD
    equity:opening/closing balances   60.01 HKD
""",
    )

    defects = await clopen_verify.verify_family([april, may], "2026-06")

    assert _kinds(defects) == [("2026-05", "opening_mismatch")]
    assert defects[0].detail == (
        "assets:cash: opening 2026-05 has 90.01 HKD, closing 2026-04 has -90.00 HKD"
    )


@pytest.mark.anyio
async def test_closing_incomplete_reported(tmp_path: PathLike[str]) -> None:
    """A closing that omits a funded account reports the balance it left open."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 transfer
    assets:bank                       50.00 HKD
    assets:cash                      -50.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -50.00 HKD = 0.00 HKD
    equity:opening/closing balances   50.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_incomplete")]
    assert defects[0].detail == "assets:bank: 50.00 HKD left unclosed"


@pytest.mark.anyio
async def test_closing_amount_wrong_reported(tmp_path: PathLike[str]) -> None:
    """A closing whose amount is not the negated balance is reported.

    hledger rejects a same-commodity assertion that the amount fails, so the
    only journal that reaches this check is one whose zero assertion names a
    different commodity than the balance the closing was meant to zero.
    """

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -89.99 HKD = 0.00 USD
    equity:opening/closing balances   89.99 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_not_zero")]
    assert defects[0].detail == ("assets:cash: expected -90.00 HKD, found -89.99 HKD")


@pytest.mark.anyio
async def test_closing_without_zero_assertion_reported(
    tmp_path: PathLike[str],
) -> None:
    """A closing posting that does not assert a zero balance is reported."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD
    equity:opening/closing balances   90.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_not_zero")]
    assert defects[0].detail == (
        "assets:cash: closing posting has no balance assertion"
    )


@pytest.mark.anyio
async def test_future_month_boundary_reported(tmp_path: PathLike[str]) -> None:
    """Boundaries in a month after the current one are unexpected."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april, may], "2026-04")

    assert _kinds(defects) == [
        ("2026-05", "unexpected_boundary"),
        ("2026-05", "unexpected_boundary"),
    ]
    assert [defect.detail for defect in defects] == [
        "closing balances transaction in a month after 2026-04",
        "opening balances transaction in a month after 2026-04",
    ]


@pytest.mark.anyio
async def test_closing_not_last_reported(tmp_path: PathLike[str]) -> None:
    """A transaction after the closing leaves the closing out of place."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD = 0.00 HKD
    equity:opening/closing balances   90.00 HKD

2026-04-30 adjustment
    expenses:food                      1.00 HKD
    assets:cash                       -1.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "boundary_unordered")]
    assert defects[0].detail == "closing balances is not the last transaction"


@pytest.mark.anyio
async def test_boundary_date_and_time_reported(tmp_path: PathLike[str]) -> None:
    """An opening off its date and time is reported for both."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-02 opening balances  ; clopen: , time: 00:00:01, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "boundary_unordered"),
        ("2026-04", "boundary_unordered"),
    ]
    assert [defect.detail for defect in defects] == [
        "opening balances has time 00:00:01, expected 00:00:00",
        "opening balances is dated 2026-04-02, expected 2026-04-01",
    ]


@pytest.mark.anyio
async def test_now_override_classifies_current_month(tmp_path: PathLike[str]) -> None:
    """The current month keeps its closing optional; an earlier view requires it."""

    folder = Path(tmp_path) / "ledger" / "2026"
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD
""",
    )

    assert list(await clopen_verify.verify_family([may], "2026-05")) == []
    assert _kinds(await clopen_verify.verify_family([may], "2026-06")) == [
        ("2026-05", "missing_closing")
    ]
    assert _kinds(await clopen_verify.verify_family([may], "2026-04")) == [
        ("2026-05", "unexpected_boundary"),
    ]


@pytest.mark.anyio
async def test_closing_asserting_nonzero_reported(tmp_path: PathLike[str]) -> None:
    """A closing that asserts a non-zero balance is reported twice over.

    hledger accepts an assertion that holds, so a closing posting can assert the
    very balance it was meant to zero out: the assertion rule and the amount
    rule then both speak about the same account.
    """

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:bank                       5.00 HKD = 5.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:bank                      = 5.00 HKD
    equity:opening/closing balances
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "closing_not_zero"),
        ("2026-04", "closing_not_zero"),
    ]
    assert [defect.detail for defect in defects] == [
        "assets:bank: closing posting asserts 5.00 HKD instead of zero",
        "assets:bank: expected -5.00 HKD, found 0.00 HKD",
    ]


@pytest.mark.anyio
async def test_closing_date_and_time_reported(tmp_path: PathLike[str]) -> None:
    """A closing off its date and time is reported for both."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-29 closing balances  ; clopen: , time: 23:59:58, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "boundary_unordered"),
        ("2026-04", "boundary_unordered"),
    ]
    assert [defect.detail for defect in defects] == [
        "closing balances has time 23:59:58, expected 23:59:59",
        "closing balances is dated 2026-04-29, expected 2026-04-30",
    ]


@pytest.mark.anyio
async def test_unreadable_journal_reported(tmp_path: PathLike[str]) -> None:
    """A journal hledger cannot read becomes an unreadable defect."""

    folder = Path(tmp_path) / "ledger" / "2026"
    broken = _write_journal(folder, "2026-04", "2026-13-01 not a month\n")

    defects = await clopen_verify.verify_family([broken], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail.startswith("hledger print exited 1: ")


def _write_chain(folder: Path) -> list[Path]:
    """Write one clean and one closing-less month, in two journal families."""
    june = _write_journal(
        folder,
        "2026-06",
        """\
2026-06-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances
""",
    )
    alternatives = june.with_name("self.alternatives.journal")
    alternatives.write_text(june.read_text())
    return [june, alternatives]


@pytest.mark.anyio
async def test_main_prints_defects_and_exits_one(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI prints one line per defect and exits non-zero."""

    ledger = Path(tmp_path) / "ledger"
    journals = _write_chain(ledger / "2026")
    monkeypatch.setattr(clopen_verify, "get_ledger_folder", lambda: ledger)

    with pytest.raises(SystemExit) as exit_info:
        await clopen_verify.main(clopen_verify.Arguments(now="2026-07"))

    assert exit_info.value.code == 1
    printed = sorted(capsys.readouterr().out.splitlines())
    assert printed == sorted(
        f"{journal.resolve()}:2026-06: missing_closing: no closing balances transaction"
        for journal in journals
    )


@pytest.mark.anyio
async def test_main_filters_by_period_and_file(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--period`` and ``--files`` narrow the journals that are reported."""

    ledger = Path(tmp_path) / "ledger"
    journals = _write_chain(ledger / "2026")
    monkeypatch.setattr(clopen_verify, "get_ledger_folder", lambda: ledger)

    with pytest.raises(SystemExit) as exit_info:
        await clopen_verify.main(
            clopen_verify.Arguments(
                now="2026-07", period="2026-06", files=("self.journal",)
            )
        )

    assert exit_info.value.code == 1
    assert capsys.readouterr().out.splitlines() == [
        f"{journals[0].resolve()}:2026-06: missing_closing: "
        "no closing balances transaction"
    ]


@pytest.mark.anyio
async def test_main_exits_zero_when_clean(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean chain prints nothing and exits zero."""

    ledger = Path(tmp_path) / "ledger"
    _write_journal(
        ledger / "2026",
        "2026-06",
        """\
2026-06-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-06-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )
    monkeypatch.setattr(clopen_verify, "get_ledger_folder", lambda: ledger)

    with pytest.raises(SystemExit) as exit_info:
        await clopen_verify.main(
            clopen_verify.Arguments(
                now="2026-06", period="2026-06", files=("self.journal",)
            )
        )

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == ""


@pytest.mark.anyio
async def test_account_types_failure_reported(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing ``accounts --types`` call is reported instead of guessed around."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    real_run_hledger = clopen_verify.run_hledger

    async def fake_run_hledger(
        journal: PathLike[str],
        *args: str,
        strict: bool = True,
        raise_on_error: bool = True,
        log_on_error: bool = True,
    ) -> tuple[str, str, int]:
        """Fail the ``accounts`` call and leave the ``print`` call alone."""
        if args[:1] == ("accounts",):
            raise CalledProcessError(2, "hledger", b"", b"boom\n")
        return await real_run_hledger(
            journal,
            *args,
            strict=strict,
            raise_on_error=raise_on_error,
            log_on_error=log_on_error,
        )

    monkeypatch.setattr(clopen_verify, "run_hledger", fake_run_hledger)

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail == "hledger accounts --types exited 2: boom"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("stdout", "detail"),
    [
        ("", "hledger print produced no output"),
        ("not json", "hledger print produced an unexpected document"),
    ],
)
async def test_invalid_hledger_output_reported(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    detail: str,
) -> None:
    """Output hledger cannot have produced becomes an unreadable defect."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)

    async def fake_run_hledger(
        journal: PathLike[str],
        *args: str,
        strict: bool = True,
        raise_on_error: bool = True,
        log_on_error: bool = True,
    ) -> tuple[str, str, int]:
        """Return the given output as if hledger had printed it."""
        return stdout, "", 0

    monkeypatch.setattr(clopen_verify, "run_hledger", fake_run_hledger)

    defects = await clopen_verify.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail.startswith(detail)


@pytest.mark.anyio
async def test_parser_builds_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser collects the three options into one :class:`Arguments`."""

    captured: list[clopen_verify.Arguments] = []

    async def fake_main(args: clopen_verify.Arguments) -> None:
        """Record the arguments instead of verifying the ledger."""
        captured.append(args)

    monkeypatch.setattr(clopen_verify, "main", fake_main)

    entry = clopen_verify.parser().parse_args(
        [
            "--period",
            "2026-06",
            "--files",
            "self.journal",
            "--files",
            "self.alternatives.journal",
            "--now",
            "2026-06-30",
        ]
    )
    await entry.invoke(entry)

    assert captured == [
        clopen_verify.Arguments(
            period="2026-06",
            files=("self.journal", "self.alternatives.journal"),
            now="2026-06-30",
        )
    ]


@pytest.mark.anyio
async def test_current_month_missing_opening_reported(tmp_path: PathLike[str]) -> None:
    """The current month needs its opening but not its closing."""

    folder = Path(tmp_path) / "ledger" / "2026"
    june = _write_journal(
        folder,
        "2026-06",
        """\
2026-06-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD
""",
    )

    defects = await clopen_verify.verify_family([june], "2026-06")

    assert _kinds(defects) == [("2026-06", "missing_opening")]


@pytest.mark.anyio
async def test_journal_families_are_not_compared(tmp_path: PathLike[str]) -> None:
    """Two journal families in one month are never compared with each other."""

    folder = Path(tmp_path) / "ledger" / "2026"
    main_journal = _write_journal(folder, "2026-04", _clean_month("2026-04", "90.00"))
    alternatives = _write_named(
        folder,
        "2026-04",
        "self.alternatives.journal",
        _clean_month("2026-04", "500.00"),
    )

    defects = await clopen_verify.verify_family([main_journal, alternatives], "2026-05")

    assert list(defects) == []


@pytest.mark.anyio
async def test_duplicate_boundary_reported(tmp_path: PathLike[str]) -> None:
    """Two closing transactions in one month are reported, not silently picked."""

    folder = Path(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-15 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                        0.00 HKD = 0.00 HKD
    equity:opening/closing balances
""",
    )

    defects = await clopen_verify.verify_family([april], "2026-05")

    assert _kinds(defects) == [("2026-04", "boundary_unordered")]
    assert defects[0].detail == "2 closing balances transactions"


@pytest.mark.anyio
async def test_unreadable_month_breaks_the_chain(tmp_path: PathLike[str]) -> None:
    """A month that cannot be read leaves its neighbours unpaired."""

    folder = Path(tmp_path) / "ledger" / "2026"
    march = _write_journal(folder, "2026-03", _clean_month("2026-03", "90.00"))
    april = _write_journal(folder, "2026-04", "2026-13-01 not a month\n")
    may = _write_journal(folder, "2026-05", _clean_month("2026-05", "500.00"))

    defects = await clopen_verify.verify_family([march, april, may], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("month", "detail"),
    [
        ("june", "month directory 'june' is not named YYYY-MM"),
        ("2026-13", "month directory '2026-13' is not a calendar month"),
    ],
)
async def test_malformed_month_directory_reported(
    tmp_path: PathLike[str], month: str, detail: str
) -> None:
    """A directory that is not a month is a defect, not a crash."""

    folder = Path(tmp_path) / "ledger" / "2026"
    journal = _write_journal(folder, month, _clean_month("2026-04", "90.00"))

    defects = await clopen_verify.verify_family([journal], "2026-06")

    assert _kinds(defects) == [(month, "unreadable")]
    assert defects[0].detail == detail


@pytest.mark.anyio
async def test_main_rejects_malformed_period(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A period that is not a month is rejected instead of selecting nothing."""

    monkeypatch.setattr(clopen_verify, "get_ledger_folder", lambda: Path(tmp_path))

    with pytest.raises(ValueError, match="--period '2026-1' is not a YYYY-MM month"):
        await clopen_verify.main(
            clopen_verify.Arguments(period="2026-1", now="2026-11")
        )


@pytest.mark.anyio
async def test_main_rejects_unknown_file(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A filename that matches no journal is rejected instead of selecting nothing."""

    folder = Path(tmp_path) / "ledger" / "2026"
    _write_journal(folder, "2026-06", _clean_month("2026-06", "90.00"))
    monkeypatch.setattr(
        clopen_verify, "get_ledger_folder", lambda: Path(tmp_path) / "ledger"
    )

    with pytest.raises(ValueError, match="--files 'ledger/2026/2026-06/self.journal'"):
        await clopen_verify.main(
            clopen_verify.Arguments(
                files=("ledger/2026/2026-06/self.journal",), now="2026-11"
            )
        )


@pytest.mark.anyio
async def test_main0_reports_argument_errors(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rejected argument exits non-zero with one line naming it."""

    monkeypatch.setattr(clopen_verify, "get_ledger_folder", lambda: Path(tmp_path))
    monkeypatch.setattr(
        clopen_verify.sys, "argv", ["clopen_verify", "--period", "2026-1"]
    )

    with pytest.raises(SystemExit) as exit_info:
        await clopen_verify.main0()

    assert exit_info.value.code == 1
    assert capsys.readouterr().err == (
        "error: --period '2026-1' is not a YYYY-MM month\n"
    )
