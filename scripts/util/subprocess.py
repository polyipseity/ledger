"""Subprocess helpers (hledger invocation)."""

from asyncio import BoundedSemaphore, create_subprocess_exec
from asyncio.subprocess import DEVNULL, PIPE
from os import cpu_count
from shutil import which
from subprocess import CalledProcessError

_SUBPROCESS_SEMAPHORE = BoundedSemaphore(cpu_count() or 4)


async def run_hledger(
    journal, *args: str, raise_on_error: bool = True, strict: bool = True
) -> tuple[str, str, int]:
    hledger_prog = which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError("hledger executable not found in PATH")

    async with _SUBPROCESS_SEMAPHORE:
        cli = (
            hledger_prog,
            "--file",
            str(journal),
            *(("--strict",) if strict else ()),
            *args,
        )
        proc = await create_subprocess_exec(
            *cli,
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
        )
        out_bytes, err_bytes = await proc.communicate()
        stdout = out_bytes.decode().replace("\r\n", "\n")
        stderr = err_bytes.decode().replace("\r\n", "\n")
        returncode = await proc.wait()
        if raise_on_error and returncode:
            raise CalledProcessError(
                returncode,
                cli,
                output=stdout,
                stderr=stderr,
            )
        return stdout, stderr, returncode
