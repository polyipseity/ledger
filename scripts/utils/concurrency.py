"""Small concurrency helpers."""

from collections.abc import Awaitable
from subprocess import CalledProcessError

from asyncer import create_task_group

"""Public symbols exported by this module."""
__all__ = ("gather_and_raise",)


def _coerce_process_stream(value: object | None) -> str:
    """Return a normalized text representation for subprocess stream content."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _summarize_exception(exc: BaseException) -> str:
    """Build a concise human-readable summary for an exception.

    For :class:`subprocess.CalledProcessError`, include command, return code,
    and captured stderr/stdout so CLI failures surface actionable context.
    """
    if isinstance(exc, CalledProcessError):
        cmd = repr(exc.cmd)
        stderr = _coerce_process_stream(exc.stderr).strip()
        stdout = _coerce_process_stream(exc.output).strip()

        details: list[str] = [f"Command {cmd} failed with exit code {exc.returncode}."]
        if stderr:
            details.append(f"stderr: {stderr}")
        elif stdout:
            details.append(f"stdout: {stdout}")
        return " ".join(details)

    return f"{type(exc).__name__}: {exc}"


async def gather_and_raise(*awaitables: Awaitable[object]) -> None:
    """Run many awaitables concurrently and raise grouped exceptions.

    This helper wraps structured concurrency task groups with exception
    gathering and converts any raised exceptions into a single :class:`BaseExceptionGroup`.

    Parameters
    ----------
    *awaitables: Awaitable[object]
        The awaitables (coroutines/futures) to run concurrently.

    Raises
    ------
    BaseExceptionGroup
        If any of the awaitables raised; the group's members will be the
        individual exceptions raised by those awaitables.
    """
    errs: list[BaseException] = []

    async def _await(a: Awaitable[object]) -> object:
        """Helper to await an awaitable and capture exceptions."""
        return await a

    try:
        async with create_task_group() as tg:
            for awaitable in awaitables:
                tg.soonify(_await)(awaitable)
    except BaseExceptionGroup as eg:
        errs.extend(eg.exceptions)
    except BaseException as e:
        errs.append(e)

    if errs:
        details = "\n".join(f"- {_summarize_exception(err)}" for err in errs)
        raise BaseExceptionGroup(f"One or more tasks failed:\n{details}", errs)
