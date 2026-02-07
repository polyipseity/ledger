"""Tests for :mod:`scripts.util.journals`.

Property-based tests cover amount parsing and date parsing utilities. The
module also verifies journal file discovery, inclusive filtering by period,
and user-friendly listing helpers.
"""

from datetime import datetime
from os import PathLike, fspath
from types import SimpleNamespace
from typing import Any

import pytest
from anyio import Path
from hypothesis import given
from hypothesis import strategies as st

from scripts.util import journals

__all__ = ()


@st.composite
def amount_strings(draw: st.DrawFn) -> tuple[str, float]:
    """Hypothesis strategy producing amount strings with their expected float value."""
    int_part = draw(st.integers(min_value=0, max_value=1_000_000))
    frac = draw(st.integers(min_value=0, max_value=99))
    pattern = draw(st.sampled_from(["comma_dot", "space_comma", "plain"]))
    if pattern == "comma_dot":
        # 1,234.56
        s = f"{int_part:,}.{frac:02d}"
        value = float(f"{int_part}.{frac:02d}")
    elif pattern == "space_comma":
        # 1 234,56
        # insert spaces as thousands separators
        s_int = f"{int_part:,}".replace(",", " ")
        s = f"{s_int},{frac:02d}"
        value = float(f"{int_part}.{frac:02d}")
    else:
        # plain integer or with dot decimal
        if draw(st.booleans()):
            s = f"{int_part}"
            value = float(int_part)
        else:
            s = f"{int_part}.{frac:02d}"
            value = float(f"{int_part}.{frac:02d}")
    return s, value


@given(amount_strings())
def test_parse_amount_roundtrip(pair: tuple[str, float]) -> None:
    """Parsing strings produced by :func:`amount_strings` should round-trip to expected values."""
    s, expected = pair
    parsed = journals.parse_amount(s)
    assert abs(parsed - expected) < 1e-9


@given(st.integers(min_value=1900, max_value=2100))
def test_parse_period_start_year_only(year: int) -> None:
    """Year-only strings parse to a period start at January 1st of that year."""
    s = str(year)
    dt = journals.parse_period_start(s)
    assert isinstance(dt, datetime)
    assert dt.year == year
    assert dt.month == 1 and dt.day == 1


@given(st.tuples(st.integers(2000, 2100), st.integers(1, 12)))
def test_parse_period_start_month(year_month: tuple[int, int]) -> None:
    """Year-month strings parse to the first day of the given month."""
    y, m = year_month
    s = f"{y}-{m:02d}"
    dt = journals.parse_period_start(s)
    assert dt.year == y and dt.month == m and dt.day == 1


@given(st.tuples(st.integers(2000, 2100), st.integers(1, 12)))
def test_parse_period_end_month(year_month: tuple[int, int]) -> None:
    """Year-month strings parse to a datetime representing that month's end."""
    y, m = year_month
    s = f"{y}-{m:02d}"
    dt = journals.parse_period_end(s)
    assert isinstance(dt, datetime)
    # Month-end logic: returned month should match
    assert dt.month == m and dt.year == y


def test_parse_period_start_and_end_basic() -> None:
    """Loose ISO strings should parse to the correct period start/end."""
    s = journals.parse_period_start("2024")
    assert s.year == 2024 and s.month == 1 and s.day == 1

    s = journals.parse_period_start("2024-02")
    assert s.year == 2024 and s.month == 2 and s.day == 1

    e = journals.parse_period_end("2024")
    assert e.year == 2024 and e.month == 12 and e.day == 31

    e = journals.parse_period_end("2024-02")
    assert e.month == 2


@given(
    whole=st.integers(min_value=0, max_value=10_000),
    frac=st.integers(min_value=0, max_value=99),
)
def test_parse_amount_various(whole: int, frac: int) -> None:
    """parse_amount accepts common thousands separators and decimals."""
    val = whole + frac / 100.0
    # Produce a representation with commas as thousands separator
    s1 = f"{val:,.2f}"
    assert abs(journals.parse_amount(s1) - val) < 1e-9

    # Spaces as thousands separator and comma as decimal
    s2 = str(whole)
    if whole >= 1000:
        s2 = f"{whole:,}".replace(",", " ")
    s2 = s2 + "," + f"{frac:02d}"
    assert abs(journals.parse_amount(s2) - val) < 1e-9


@pytest.mark.asyncio
async def test_make_datetime_range_filters_and_filter_journals_between(
    tmp_path: PathLike[str],
) -> None:
    """Filtering journals by month inclusively should work as documented."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-02").mkdir()
    p1 = repo / "2024-01" / "self.journal"
    p2 = repo / "2024-02" / "self.journal"
    await p1.write_text("x")
    await p2.write_text("y")

    # from January to January should include only 2024-01
    from_dt = datetime.fromisoformat("2024-01-01")
    # Use an inclusive end-of-day to match the month-end used by the helper
    to_dt = datetime(2024, 1, 31, 23, 59, 59, 999999)
    journals_list = [p1, p2]
    filtered = journals.filter_journals_between(journals_list, from_dt, to_dt)
    assert p1 in filtered and p2 not in filtered


@pytest.mark.asyncio
async def test_find_monthly_and_all(tmp_path: PathLike[str]) -> None:
    """`find_monthly_journals` and `find_all_journals` should discover files under a ledger folder."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "some_folder").mkdir()
    await (repo / "2024-01" / "a.journal").write_text("")
    await (repo / "some_folder" / "b.journal").write_text("")

    monthly = await journals.find_monthly_journals(repo)
    all_js = await journals.find_all_journals(repo)

    assert any(Path(p).name == "a.journal" for p in monthly)
    assert any(Path(p).name == "a.journal" for p in all_js)
    assert any(Path(p).name == "b.journal" for p in all_js)


def test_parse_period_invalid_raises() -> None:
    """Invalid period strings should raise ValueError for both start and end parsing."""
    with pytest.raises(ValueError):
        journals.parse_period_start("not-a-date")
    with pytest.raises(ValueError):
        journals.parse_period_end("also-bad")


@pytest.mark.asyncio
async def test_run_hledger_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the `hledger` executable is not found in PATH run_hledger should raise FileNotFoundError."""

    def fake_which_none(prog: str) -> str | None:
        return None

    monkeypatch.setattr(journals, "which", fake_which_none)

    async def run_it() -> None:
        await journals.run_hledger("somefile", "print")

    with pytest.raises(FileNotFoundError):
        await run_it()


def test_format_journal_list_various() -> None:
    """format_journal_list produces a compact user-friendly listing."""
    assert journals.format_journal_list([]) == "none"

    class P(PathLike[str]):
        """Small PathLike helper used in tests to emulate discovered journal entries."""

        def __init__(self, parent: str, name: str) -> None:
            """Initialize with a synthetic parent object and filename."""
            self.parent = SimpleNamespace(name=parent)
            self.name = name

        def __fspath__(self) -> str:
            """Return a string path representation like 'YYYY-MM/name' for testing."""
            return f"{self.parent.name}/{self.name}"

    lst = [P("2024-01", "self.journal")]
    s = journals.format_journal_list(lst)
    assert "1 journal" in s

    # many items trigger the ellipsis (case 1)
    lst = [P("2024-%02d" % i, "self.journal") for i in range(1, 12)]
    s = journals.format_journal_list(lst, max_items=4)
    assert "... (" in s
    lst = [P("2024-01", "self.journal")]
    s = journals.format_journal_list(lst)
    assert "1 journal" in s

    # many items trigger the ellipsis
    lst = [P("2024-%02d" % i, "self.journal") for i in range(1, 12)]
    s = journals.format_journal_list(lst, max_items=4)
    assert "... (" in s


def test_format_journal_list_handles_path_exceptions() -> None:
    """If converting an entry to :class:`Path` raises, the original object should be used as the label."""

    class Bad:
        def __fspath__(self) -> str:  # pragma: no cover - simulated exception
            raise RuntimeError("boom")

    s = journals.format_journal_list([Bad()], max_items=4)
    # the representation should contain the stringified original object
    assert "boom" not in s
    assert "-" in s


@pytest.mark.asyncio
async def test_find_monthly_with_files_param(tmp_path: PathLike[str]) -> None:
    """When explicit file paths are supplied, `find_monthly_journals` should resolve and return them."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    f = repo / "2024-01" / "a.journal"
    await f.write_text("")

    res = await journals.find_monthly_journals(repo, files=[fspath(f)])
    assert any(Path(p).name == "a.journal" for p in res)


def test_filter_journals_skips_invalid_parent_names() -> None:
    """Journals whose parent folder name isn't a valid YYYY-MM should be silently ignored."""

    class Fake(PathLike[str]):
        def __init__(self):
            self.parent = SimpleNamespace(name="not-a-date")
            self.name = "x.journal"

        def __fspath__(self) -> str:
            return "bad"

    out = journals.filter_journals_between([Fake()], None, None)
    assert out == []


@pytest.mark.asyncio
async def test_run_hledger_handles_process_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate subprocess success and failure for `run_hledger` using a fake process."""

    class FakeProc:
        def __init__(self, out: bytes, err: bytes, rc: int):
            self._out = out
            self._err = err
            self._rc = rc

        async def communicate(self) -> tuple[bytes, bytes]:
            return self._out, self._err

        async def wait(self) -> int:
            return self._rc

    async def fake_create(*args: Any, **kwargs: Any) -> FakeProc:
        # return a process with non-zero returncode to exercise error path
        return FakeProc(b"ok\n", b"", 0)

    monkeypatch.setattr(journals, "create_subprocess_exec", fake_create)

    def fake_which(prog: str) -> str:
        return "fake"

    monkeypatch.setattr(journals, "which", fake_which)

    out, _err, _rc = await journals.run_hledger(
        "somefile", "print", raise_on_error=True
    )
    assert "ok" in out

    # Now simulate non-zero return code which should raise when raise_on_error=True
    async def fake_create_bad(*args: Any, **kwargs: Any) -> FakeProc:
        return FakeProc(b"", b"err\n", 2)

    monkeypatch.setattr(journals, "create_subprocess_exec", fake_create_bad)
    with pytest.raises(Exception):
        await journals.run_hledger("somefile", "print", raise_on_error=True)
