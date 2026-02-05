"""File helpers (reading/writing/updating files, script folder detection)."""

from inspect import currentframe, getframeinfo

from anyio import Path


def get_script_folder() -> Path:
    """Return the Path of the folder containing the caller script.

    Inspects the current Python stack and returns the directory containing
    the calling module's source file. When used by modules under the
    `scripts` package this resolves to the repository's `scripts/` folder
    which is the intended caller behaviour.
    """
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    return Path(getframeinfo(frame).filename).parent


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
