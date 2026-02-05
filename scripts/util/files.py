"""File helpers (reading/writing/updating files, script folder detection)."""

from inspect import currentframe, getframeinfo

from anyio import Path


def get_script_folder() -> Path:
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    return Path(getframeinfo(frame).filename).parent


async def file_update_if_changed(journal: Path, updater):
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
