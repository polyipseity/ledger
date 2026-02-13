"""Tests for :mod:`scripts.utils.files`.

These exercises test the stack-inspection-based helpers and the
`file_update_if_changed` async updater using both concrete and property-based
inputs.
"""

from collections.abc import Callable
from os import PathLike

import pytest
from anyio import Path, TemporaryDirectory
from hypothesis import given
from hypothesis import strategies as st

from scripts.utils import files

__all__ = ()


def test_get_script_folder_returns_pathlike() -> None:
    """get_script_folder returns a path-like object that contains a module name."""
    p = files.get_script_folder()
    assert isinstance(Path(p).name, str) and Path(p).name


def test_get_script_folder_depth() -> None:
    """get_script_folder(depth=1) returns the parent of the caller's folder."""
    p0 = files.get_script_folder()
    p1 = files.get_script_folder(depth=1)
    assert Path(p1) == Path(p0).parent


def test_get_script_folder_negative_raises() -> None:
    """Negative depth values raise a ValueError."""
    with pytest.raises(ValueError):
        files.get_script_folder(depth=-1)


@pytest.mark.asyncio
async def test_get_ledger_folder_points_to_ledger() -> None:
    """get_ledger_folder() returns an existing path named 'ledger'."""
    ledger = files.get_ledger_folder()
    assert await Path(ledger).exists()
    assert Path(ledger).name == "ledger"


def test_get_script_folder_frame_none_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """When inspect.currentframe() returns None, get_script_folder must raise ValueError."""
    monkeypatch.setattr(files, "currentframe", lambda: None)
    with pytest.raises(ValueError):
        files.get_script_folder()


def test_get_script_folder_no_caller_frame_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the caller frame is missing (f_back is None) get_script_folder raises ValueError."""

    class FakeFrame:
        """Fake frame object with no caller to simulate inspect.currentframe() returning a frame without f_back."""

        f_back = None

    monkeypatch.setattr(files, "currentframe", lambda: FakeFrame())
    with pytest.raises(ValueError):
        files.get_script_folder()


@pytest.mark.asyncio
async def test_file_update_if_changed_roundtrip(tmp_path: PathLike[str]) -> None:
    """file_update_if_changed should write new content and leave unchanged files alone."""
    fp = Path(tmp_path) / "test.journal"
    await fp.write_text("original\n")

    changed = await files.file_update_if_changed(
        fp, lambda s: s.replace("original", "modified")
    )
    assert changed
    assert await fp.read_text() == "modified\n"

    not_changed = await files.file_update_if_changed(fp, lambda s: s)
    assert not not_changed
    assert await fp.read_text() == "modified\n"


def test_get_script_folder_basic() -> None:
    """get_script_folder() returns a Path and rejects negative depth."""
    p = files.get_script_folder()
    assert isinstance(p, PathLike)

    with pytest.raises(ValueError):
        files.get_script_folder(depth=-1)


def test_get_ledger_folder_contains_ledger_name() -> None:
    """get_ledger_folder() returns a Path whose last part is ``ledger``."""
    p = files.get_ledger_folder()
    assert Path(p).name == "ledger"


@pytest.mark.asyncio
async def test_file_update_if_changed_true_and_false(tmp_path: PathLike[str]) -> None:
    """file_update_if_changed writes only when the updater changes the text."""
    p = Path(tmp_path) / "journal.journal"
    await p.write_text("original\n")

    res = await files.file_update_if_changed(p, lambda s: s)
    assert res is False
    assert await p.read_text() == "original\n"

    res = await files.file_update_if_changed(p, lambda s: s.replace("original", "new"))
    assert res is True
    assert await p.read_text() == "new\n"


# Property-based tests for files
@pytest.mark.asyncio
@given(st.text(max_size=200))
async def test_file_update_if_changed_with_random_text(s: str) -> None:
    """Property-based async test: file updater handles random text values using a real tempfile."""
    async with TemporaryDirectory() as td:
        p = Path(td) / "f.journal"
        await p.write_text(s)

        changed = await files.file_update_if_changed(p, lambda text: text[::-1])
        assert isinstance(changed, bool)
        if changed:
            # Normalize newlines to avoid platform-specific CR/LF issues
            def normalize(t: str) -> str:
                """Normalize newlines to a single LF for cross-platform comparisons."""
                return t.replace("\r\n", "\n").replace("\r", "\n")

            assert normalize(await p.read_text()) == normalize(s[::-1])


# Property test: updater semantics
@st.composite
def text_and_updater(draw: st.DrawFn) -> tuple[str, Callable[[str], str]]:
    """Hypothesis strategy producing (text, updater) pairs for property tests."""
    s = draw(st.text(max_size=200))
    updater_choice = draw(
        st.sampled_from(["identity", "reverse", "prefix", "suffix", "shorten"])
    )
    if updater_choice == "identity":

        def _u_identity(x: str) -> str:
            """Identity updater - returns input unchanged."""
            return x

        updater = _u_identity
    elif updater_choice == "reverse":

        def _u_reverse(x: str) -> str:
            """Reverse updater - returns the reversed input string."""
            return x[::-1]

        updater = _u_reverse
    elif updater_choice == "prefix":
        prefix = draw(st.text(min_size=0, max_size=5))

        def _u_prefix(x: str, p: str = prefix) -> str:
            """Prefix updater - prepends the supplied prefix to the input."""
            return p + x

        updater = _u_prefix
    elif updater_choice == "suffix":
        suffix = draw(st.text(min_size=0, max_size=5))

        def _u_suffix(x: str, sfx: str = suffix) -> str:
            """Suffix updater - appends the supplied suffix to the input."""
            return x + sfx

        updater = _u_suffix
    else:
        a = draw(st.integers(min_value=0, max_value=5))
        b = draw(st.integers(min_value=a, max_value=a + 5))

        def shorten(x: str, a: int = a, b: int = b) -> str:
            """Shorten updater - removes the slice [a:b] from the input string."""
            if not x:
                return x
            a_clamped = min(a, len(x))
            b_clamped = min(b, len(x))
            if a_clamped > b_clamped:
                a_clamped, b_clamped = b_clamped, a_clamped
            return x[:a_clamped] + x[b_clamped:]

        updater = shorten
    return s, updater


@pytest.mark.asyncio
@given(text_and_updater())
async def test_file_update_if_changed_semantics(
    pair: tuple[str, Callable[[str], str]],
) -> None:
    """Property-based async test: updater semantics are preserved for random updaters.

    Uses a temporary file on-disk so the async updater runs against a
    concrete anyio.Path object and avoids mixing Hypothesis with pytest fixtures.
    """
    orig, updater = pair

    async with TemporaryDirectory() as td:
        p = Path(td) / "g.journal"
        await p.write_text(orig)

        changed = await files.file_update_if_changed(p, updater)
        expected = updater(orig)

        # Normalize newlines to avoid platform-specific CR/LF issues
        def normalize(t: str) -> str:
            """Normalize newlines to a single LF for cross-platform comparisons."""
            return t.replace("\r\n", "\n").replace("\r", "\n")

        if expected == orig:
            assert changed is False
            assert normalize(await p.read_text()) == normalize(orig)
        else:
            assert changed is True
            assert normalize(await p.read_text()) == normalize(expected)
