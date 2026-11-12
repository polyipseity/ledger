---
name: Developer workflows
description: "Use when changing a script under scripts/, a prek hook in prek.toml, or the pytest suite under tests/."
applyTo: "**"
---

# Developer workflows

`AGENTS.md` owns the command names and how they are invoked; this file covers what runs behind them. Journal syntax is `transaction-format`, journal editing is `editing-guidelines`, and commit messages are `git-commits`.

## Script internals

`scripts/` is one Python package: each top-level module is a command, `scripts/utils/` holds the shared helpers, and the modules import each other relatively (`from .utils.cache import JournalRunContext`), which is why they run only as modules of that package. `scripts/utils/files.py::get_ledger_folder` walks from the helper's own `__file__` up to the repository root and returns `<repo>/ledger`, so discovery does not depend on the process working directory, and a caller that wants another tree passes explicit journal paths, which `find_monthly_journals` returns already resolved.

- `find_monthly_journals` matches monthly journals under the ledger folder with a glob of the form `**/*<YYYY>-<MM>/*.journal`; `find_all_journals` matches every `*.journal` under a folder.
- `run_hledger` (`scripts/utils/journals.py`) invokes `hledger --file <journal> --strict <args>` and defaults `strict=True`, so every hledger call from a script is strict unless the caller opts out; a non-zero exit raises `CalledProcessError` unless the caller sets `raise_on_error=False`.
- The hledger binary is the managed `node_modules/.bin/hledger` that `bun install` provisions. `PATH` is consulted only when that file is absent, and no binary at all raises `FileNotFoundError` instead of running a different one.
- A helper that needs asynchronous file operations coerces the caller's `PathLike` to `anyio.Path` internally, so callers keep passing `pathlib` objects.
- `Any` and `Unknown` appear only with an inline justification and a `# TODO` to narrow or remove them, because `ty` runs with every rule as an error.
- An imported name keeps its own name, with no `ArgumentParser as _ArgParser` alias to keep it out of sight, and `__all__` alone decides what a module exports. The tuple sits at module top level, immediately after the docstring and imports, and is empty in a test module.

### Run cache

`scripts/utils/cache.py` keeps one JSON cache at `scripts/utils/__pycache__/cache.cache.json`, divided by script key. A script wraps its per-journal work in `async with JournalRunContext(Path(__file__), journals) as run:` and reads `run.to_process` and `run.skipped` from it, calling `run.report_success(journal)` for each journal it finished. On exit the context records the content hashes, prunes old entries, and writes the file back; a run that raised updates only the script's `last_access`, so the journals stay pending.

- A script key is `<script name>@<sha256 of the script>+preludes@<sha256 of preludes/>`, so editing a prelude invalidates the cached journals of every script.
- A helper that derives a cache key from a script path fails fast with `FileNotFoundError` when that path cannot be opened for reading, and never falls back to a default key.
- A journal's hash covers its text lines with leading and trailing blank lines trimmed, so a stray newline at either edge does not force reprocessing while interior spacing still does.
- A missing or blank cache file reads as an empty cache, an invalid one logs a warning and starts empty, and any other read error propagates to the caller.
- `evict_old_scripts` drops a script untouched for a day and a file entry untouched for thirty days.
- `scripts/clopen.py` builds its context with `cache=False`, because a month boundary must always do the full work.

### Concurrency

- The per-journal coroutines run through `gather_and_raise` (`scripts/utils/concurrency.py`), which wraps them in an `asyncer` task group and re-raises every failure as one `BaseExceptionGroup` carrying a per-command summary.
- hledger subprocesses are throttled by a module-level `anyio.Semaphore(cpu_count() or 4)`.

## Hook shapes

Hooks are declared in `prek.toml` and installed by `bun install`.

- `commit-msg` runs commitlint, which is what rejects a malformed message before the commit exists.
- `pre-commit` runs the pre-commit-hooks baseline (case conflicts, shebang executability, illegal Windows names, merge conflicts, symlinks, private keys, end-of-file and byte-order fixes, `name-tests-test` with `--pytest-test-first`, and `trailing-whitespace` with the Markdown line-break extension), `check-dependabot`, `check-github-workflows`, `markdownlint-cli2 --fix --no-globs`, `uv-lock`, `ruff-check --fix`, `ruff-format`, `ty`, `prettier --write` over the code and data files, and the journal formatter.
- `pre-push` runs `bun run test` through the local `test-bun` hook, with `pass_filenames = false` and `always_run = true`, so a push runs the whole suite rather than the files it touches.

A hook that declares a `files` glob receives the matching paths appended to its command. The journal formatter declares `ledger/<year>/<year>-<month>/**/*.journal` and runs the `scripts.format` module under `uv run --locked`, whose positional `files` argument restricts the run to those journals; to format chosen journals, name them after the module, as `uv run --locked -m scripts.format <path>`. A hook that must ignore paths, such as the test hook, sets `pass_filenames = false`.

## Tests

`tests/conftest.py` supplies the AnyIO backend `("asyncio", {"use_uvloop": True})` for every async test in the suite.

- A test module takes its name and place from the source module it covers: `tests/scripts_/test_check.py` covers `scripts/check.py`, `tests/scripts_/utils/test_journals.py` covers `scripts/utils/journals.py`, and `tests/tests/test_test_utils.py` covers the shared helper `tests/test_utils.py`.
- Documentation-contract tests belong under `tests/docs/`; they read the repository tree from their own location and assert what the docs claim about it.
- An `async def` test carries `@pytest.mark.anyio`, and the event loop comes from the backend fixture rather than a runner inside the test.
- A `tmp_path` parameter is annotated `PathLike[str]`, and the body wraps it as `Path(tmp_path)` when it needs a `pathlib` object.
- `pyproject.toml` adds `-n=auto` and `--dist=loadscope`, so the tests of one module share a worker, and coverage is reported by default.
- `tests/test_module_exports.py` and `tests/test_docstrings.py` read the modules' ASTs and fail on a missing `__all__`, a missing module or exported-symbol docstring, or an undocumented top-level constant, so the conventions are enforced by the suite.
