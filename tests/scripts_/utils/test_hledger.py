"""Tests for :mod:`scripts.utils.hledger`.

The contracts here are the ones the other modules depend on: a non-zero exit is
reported rather than raised when the caller asks for that, and the managed
hledger binary is resolved before anything else is tried.
"""

import logging
from os import PathLike
from pathlib import Path

import pytest

import scripts.utils.hledger as hmod

"""Public symbols exported by this module (none)."""
__all__ = ()


@pytest.mark.anyio
async def test_run_hledger_returns_error_without_raising(
    tmp_path: PathLike[str],
) -> None:
    """A non-zero exit is reported, not raised, when `raise_on_error` is False."""
    journal = Path(tmp_path) / "bad.journal"
    journal.write_text("this is not a journal\n", encoding="utf-8")
    stdout, stderr, code = await hmod.run_hledger(
        journal, "check", raise_on_error=False, strict=False
    )
    assert code != 0
    assert stderr or stdout


@pytest.mark.anyio
async def test_run_hledger_raises_when_asked(tmp_path: PathLike[str]) -> None:
    """The default still raises, with the command inside the message."""
    journal = Path(tmp_path) / "bad.journal"
    journal.write_text("this is not a journal\n", encoding="utf-8")
    with pytest.raises(hmod.HledgerRunError) as excinfo:
        await hmod.run_hledger(journal, "check", strict=False)
    assert str(journal) in str(excinfo.value)
    assert excinfo.value.returncode != 0


@pytest.mark.anyio
async def test_run_hledger_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When hledger is found nowhere, run_hledger raises FileNotFoundError."""

    def fake_find_hledger() -> str:
        """Simulate the binary search failing because no binary exists."""
        raise FileNotFoundError(
            "hledger executable not found in node_modules/.bin/ or PATH"
        )

    monkeypatch.setattr(hmod, "_find_hledger", fake_find_hledger)

    with pytest.raises(FileNotFoundError):
        await hmod.run_hledger("somefile", "print")


@pytest.mark.anyio
async def test_run_hledger_handles_process_exit(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Simulate subprocess success and failure for `run_hledger` using a fake process."""

    class FakeRunProcessResult:
        """Minimal object emulating anyio's run_process result."""

        def __init__(self, out: bytes, err: bytes, rc: int) -> None:
            """Initialize fake process result properties for stdout/stderr/returncode."""
            self.stdout = out
            self.stderr = err
            self.returncode = rc

    async def fake_run_process(*args: object, **kwargs: object) -> FakeRunProcessResult:
        """Return a fake process result to simulate anyio subprocess execution."""
        # return a process with zero returncode to exercise success path
        return FakeRunProcessResult(b"ok\n", b"", 0)

    monkeypatch.setattr(hmod, "run_process", fake_run_process)

    def fake_find_hledger() -> str:
        """Return a sentinel path to simulate a discovered hledger executable."""
        return "fake"

    monkeypatch.setattr(hmod, "_find_hledger", fake_find_hledger)

    out, _err, _rc = await hmod.run_hledger("somefile", "print", raise_on_error=True)
    assert "ok" in out

    # Now simulate non-zero return code which should raise when raise_on_error=True
    async def fake_run_process_bad(
        *args: object, **kwargs: object
    ) -> FakeRunProcessResult:
        """Return a fake process result with non-zero returncode and stderr to exercise error logging."""
        return FakeRunProcessResult(
            b"586061c8-6f1a-4e6c-96fa-fc3521e833b0\n",
            b"fa27ffae-770c-48b3-a232-ad63b23a9415\n",
            2,
        )

    monkeypatch.setattr(hmod, "run_process", fake_run_process_bad)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception):
            await hmod.run_hledger("somefile", "print", raise_on_error=True)
        # stderr should be logged
        assert "fa27ffae-770c-48b3-a232-ad63b23a9415" in caplog.text
        # stdout should also be included in the log
        assert "586061c8-6f1a-4e6c-96fa-fc3521e833b0" in caplog.text

    caplog.clear()
    out, err, rc = await hmod.run_hledger("somefile", "print", raise_on_error=False)
    assert rc == 2
    assert "fa27ffae-770c-48b3-a232-ad63b23a9415" in err
    # when not raising, the error should still have been logged
    assert "fa27ffae-770c-48b3-a232-ad63b23a9415" in caplog.text

    caplog.clear()
    out, err, rc = await hmod.run_hledger(
        "somefile", "print", raise_on_error=False, log_on_error=False
    )
    assert rc == 2
    # logging disabled: no records
    assert caplog.text == ""
