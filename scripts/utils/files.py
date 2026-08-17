"""File helpers (reading/writing/updating files, script folder detection)."""

from collections.abc import Callable
from inspect import currentframe, getframeinfo
from os import PathLike
from re import sub

from anyio import Path

"""Public symbols exported by this module."""
__all__ = ("get_script_folder", "get_ledger_folder", "file_update_if_changed")


def _collapse_trailing_newlines(text: str) -> str:
    """Collapse two or more trailing newlines in `text` to a single newline.

    Content ending with zero or one newline is returned unchanged, so the
    function never adds a trailing newline where none existed. This keeps
    updater output free of multiple blank lines (e.g. an empty body) without
    altering files that intentionally have no terminating newline.
    """
    return sub(r"\n{2,}$", "\n", text)


def get_script_folder(depth: int = 0) -> PathLike[str]:
    """Return the Path of the folder containing the caller script.

    Inspects the current Python stack and returns the directory containing
    the calling module's source file. When used by modules under the
    `scripts` package this resolves to the repository's `scripts/` folder
    which is the intended caller behaviour.

    Parameters
    ----------
    depth: int
        How many parent directories to ascend from the caller's folder.
        ``0`` returns the caller's folder, ``1`` returns its parent, etc.
    """
    if depth < 0:
        raise ValueError("depth must be non-negative")

    frame = currentframe()
    if frame is None:
        raise ValueError(frame)

    caller = frame.f_back
    if caller is None:
        raise ValueError("no caller frame")

    p = Path(getframeinfo(caller).filename).parent
    for _ in range(depth):
        p = p.parent
    return p


def get_ledger_folder() -> PathLike[str]:
    """Return the repository `ledger/` folder discovered relative to the scripts folder.

    The helper uses :func:`get_script_folder` with ``depth=1`` to locate the
    repository root and returns ``<repo_root>/ledger`` as a :class:`os.PathLike`.
    """
    return Path(get_script_folder(depth=1)).parent / "ledger"


async def file_update_if_changed(
    journal: PathLike[str], updater: Callable[[str], str]
) -> bool:
    """Open `journal`, run `updater` on its current content and write only if changed.

    The function opens ``journal`` for read/write, reads the full content and
    passes it to ``updater``. If the returned text differs from the original
    content the file is overwritten (seek/write/truncate) and the function
    returns ``True``.

    Parameters
    ----------
    journal: PathLike
        The journal file to update.
    updater: Callable[[str], str]
        A function that receives the current file text and returns the new
        file text.

    Returns
    -------
    bool
        ``True`` if the file was changed, otherwise ``False``.
    """
    path = Path(journal)
    async with await path.open(
        mode="r+t", encoding="UTF-8", errors="strict", newline=None
    ) as file:
        read = await file.read()
        await file.seek(0)

        text = updater(read)
        # Collapse two or more trailing newlines to a single one so callers
        # never emit multiple trailing newlines (e.g. an empty updater body),
        # while leaving content with zero or one trailing newline untouched.
        text = _collapse_trailing_newlines(text)
        if text != read:
            await file.write(text)
            await file.truncate()
            return True
        return False
