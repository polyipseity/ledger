"""File helpers (reading/writing/updating files, script folder detection)."""

from inspect import currentframe, getframeinfo

from anyio import Path

__all__ = ("get_script_folder", "get_ledger_folder", "file_update_if_changed")


def get_script_folder(depth: int = 0) -> Path:
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


def get_ledger_folder() -> Path:
    """Return the repository `ledger/` folder discovered relative to the scripts folder.

    The helper uses :func:`get_script_folder` with ``depth=1`` to locate the
    repository root and returns ``<repo_root>/ledger`` as an :class:`anyio.Path`.
    """
    return get_script_folder(depth=1).parent / "ledger"


async def file_update_if_changed(journal: Path, updater):
    """Open `journal`, run `updater` on its current content and write only if changed.

    The function opens ``journal`` for read/write, reads the full content and
    passes it to ``updater``. If the returned text differs from the original
    content the file is overwritten (seek/write/truncate) and the function
    returns ``True``.

    Parameters
    ----------
    journal: Path
        The journal file to update.
    updater: Callable[[str], str]
        A function that receives the current file text and returns the new
        file text.

    Returns
    -------
    bool
        ``True`` if the file was changed, otherwise ``False``.
    """
    async with await journal.open(
        mode="r+t", encoding="UTF-8", errors="strict", newline=None
    ) as file:
        read = await file.read()
        await file.seek(0)

        text = updater(read)
        if text != read:
            await file.write(text)
            await file.truncate()
            return True
        return False
