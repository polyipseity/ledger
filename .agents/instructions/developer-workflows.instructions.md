---
name: Developer Workflows
description: Development workflows, utility scripts, code patterns, and testing/validation practices.
---

# Developer Workflows

## Script Usage Policy

**Always use bun script wrappers if available.**

- For all operations, prefer `bun run <script>` (e.g., `bun run check`, `bun run format`, `bun run hledger:check`, `bun run hledger:format`, etc.) from the repository root. This ensures the correct environment, dependencies, and working directory are set automatically.
- Only use direct Python invocations (e.g., `python -m scripts.check`) or script wrappers in `scripts/` (e.g., `./check`, `check.bat`) if no bun script is available for the required operation. When using these, always set the working directory to `scripts/` using the tool's `cwd` parameter.
- **Exception for lint-staged:** when a command is invoked by `lint-staged` and must receive the list of staged file paths (for example, formatting only staged files), invoke the underlying command directly (for example `python -m scripts.format`) rather than `bun run <script>` so the staged file paths are forwarded as argv. `bun run` does not reliably forward arbitrary file arguments in this context. Recommended lint-staged invocations in this repository:
  - **Markdown:** `markdownlint-cli2 --fix`
  - **Prettier:** `prettier --write`
  - **Python formatters:** run each as a separate command so each receives the file list:
    - `uv run --locked ruff check --fix`
    - `uv run --locked ruff format`
  - **Journals:** `python -m scripts.format` (accepts file args)

  Note: When listing multiple commands for the same glob in `lint-staged`, provide them as an array so each command is executed with the staged file list appended.

  **Formatting policy change:** This repository uses **Ruff** as the single authority for Python formatting and import sorting (Ruff provides Black-compatible formatting and import ordering features). **Black** and **isort** are intentionally **not used**; do not add them to dependencies or workflow steps. Use `uv run --locked ruff format` and `uv run --locked ruff check --fix` for formatting and import sorting.
- **Never run scripts from the wrong directory.** Running from the wrong location will cause include errors, missing file errors, or incorrect results.- Be mindful of shell syntax differences. In PowerShell, avoid Bash-style command patterns such as `cd /d ...` and heredoc blocks like `python - <<'PY'`; prefer `Set-Location` or using a temporary Python script file for multi-line diagnostics.
- When creating temporary diagnostic journals, place them adjacent to the original monthly journal so relative `include` statements resolve correctly.- For `hledger close --migrate`, run from the repository root as well.

**Critical:** Always use the bun script wrapper if it exists. Only fall back to direct invocation or script wrappers if no bun script is available. Always double-check the working directory before running any script command.

### Validation and Formatting (fallback if no bun script)

- `python -m scripts.check` - Validate journals (hledger strict checking)
- `python -m scripts.format` - Auto-format journals (hledger print, sort properties)
- `python -m scripts.format --check` - Validate formatting without modifying

### Modifications (fallback if no bun script)

- `python -m scripts.depreciate [--from YYYY-MM] [--to YYYY-MM] ITEM AMOUNT CURRENCY` - Depreciate asset
- `python -m scripts.shift [--from YYYY-MM] [--to YYYY-MM] ACCOUNT AMOUNT CURRENCY` - Shift balances
- `python -m scripts.replace FIND REPLACE` - Find/replace across journals

### Security (fallback if no bun script)

- `python -m scripts.encrypt` - Encrypt private.yaml
- `python -m scripts.decrypt` - Decrypt private.yaml.gpg

## bun Tasks

- `bun install` - Install dependencies
- `bun run check` - Validate journals and run all checks
- `bun run format` - Run all formatters (journals, markdown, prettier, python)
- `bun run hledger:check` - Validate journals
- `bun run hledger:format` - Format journals
- `bun run hledger:format:check` - Check journal formatting
- `bun run check:md` - Markdown lint (when running on specific files, add `--no-globs` and list the filenames to avoid scanning the whole repo)
- `bun run check:prettier` - Prettier check
- `bun run check:py` - Python checks (ruff)
- `bun run format:md` - Markdown auto-fix (add `--no-globs` with explicit filenames when targeting a subset)
- `bun run format:prettier` - Prettier auto-fix
- `bun run format:py` - Python auto-fix
- `bun run commitlint` - Lint commit messages

  Note: Prettier is invoked via CLI using explicit file globs in `package.json`. Lint-staged specifies file globs directly; we no longer export a shared `FILE_GLOBS` constant from `.prettierrc.mjs`. The Prettier file globs have been expanded to include additional file types (for example: astro, graphql, json5, mdx, svelte, vue, xml) to ensure broader formatting coverage.

## Monthly Journal Discovery

Scripts use glob `**/*[0-9]{4}-[0-9]{2}/*.journal` to find all monthly journals recursively.

## Python Code Patterns

Concrete script-specific patterns used in `scripts/`:

- Frozen dataclasses: `@dataclass(frozen=True, slots=True, kw_only=True, match_args=False)`
- Concurrency: `asyncio.BoundedSemaphore` limited to CPU count (or 4)

All other code conventions (PathLike, type hints, docstrings, `__all__`, no `Any`, Ruff) are defined in **Agent Code Conventions** in `AGENTS.md`.

### Testing

- Run: `bun run test` (full suite) or `bun run test:py` (pytest only).
- One test file per source file; mirror source structure under `tests/`.
- Async tests: use `@pytest.mark.anyio` on `async def` test functions; never use `asyncio.run` or similar event-loop runners inside pytest.
- Add or update tests whenever scripts, instructions, or validator behaviour change.
- CI and Husky `pre-push` both run the test suite — run locally to avoid blocked pushes.

## Pre-Commit Validation (Husky + lint-staged)

```powershell
bun run format        # Run all formatters (formats files repo-wide)
bun run check         # Validate all journals and run all checks
# Fix any errors before commit
git commit -m "message"
```

**Setup:** `bun install` runs `prepare`, which runs `uv sync` to install dev extras from `pyproject.toml`/`uv.lock`. CI uses `bun install --frozen-lockfile --ignore-scripts && uv sync --locked`. No `requirements.txt` — `pyproject.toml` is canonical.

Validation checks run by `bun run check`: `accounts`, `assertions`, `autobalanced`, `balanced`, `commodities`, `ordereddates`, `parseable`, `payees`, `tags`.

## Commit Message Format

See [git-commits.instructions.md](./git-commits.instructions.md)

For ledger transaction commits only: `ledger(<list>): add N / edit M transaction(s)` (single-line header, no body)
