---
name: Developer Workflows
description: Development workflows, utility scripts, code patterns, and testing/validation practices.
---

# Developer Workflows

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When performing development, scripting, or validation tasks, use the todo list tool to break down multi-step operations.**

Plan actionable steps, mark each as in-progress and completed, and update the todo list after each change to ensure all steps are completed and nothing is forgotten.

## Script Usage Policy

**Always use pnpm script wrappers if available.**

- For all operations, prefer `pnpm run <script>` (e.g., `pnpm run check`, `pnpm run format`, `pnpm run hledger:check`, `pnpm run hledger:format`, etc.) from the repository root. This ensures the correct environment, dependencies, and working directory are set automatically.
- Only use direct Python invocations (e.g., `python -m scripts.check`) or script wrappers in `scripts/` (e.g., `./check`, `check.bat`) if no pnpm script is available for the required operation. When using these, always set the working directory to `scripts/` using the tool's `cwd` parameter.
- **Exception for lint-staged:** when a command is invoked by `lint-staged` and must receive the list of staged file paths (for example, formatting only staged files), invoke the underlying command directly (for example `python -m scripts.format`) rather than `pnpm run <script>` so the staged file paths are forwarded as argv. `pnpm run` does not reliably forward arbitrary file arguments in this context. Recommended lint-staged invocations in this repository:
  - **Markdown:** `markdownlint-cli2 --fix`
  - **Prettier:** `prettier --write`
  - **Python formatters:** run each as a separate command so each receives the file list:
    - `python -m ruff check --fix`
    - `python -m isort`
    - `python -m black`
  - **Journals:** `python -m scripts.format` (accepts file args)

  Note: When listing multiple commands for the same glob in `lint-staged`, provide them as an array so each command is executed with the staged file list appended.
- **Never run scripts from the wrong directory.** Running from the wrong location will cause include errors, missing file errors, or incorrect results.
- For `hledger close --migrate`, run from the repository root as well.

**Critical:** Always use the pnpm script wrapper if it exists. Only fall back to direct invocation or script wrappers if no pnpm script is available. Always double-check the working directory before running any script command.

### Validation and Formatting (fallback if no pnpm script)

- `python -m scripts.check` - Validate journals (hledger strict checking)
- `python -m scripts.format` - Auto-format journals (hledger print, sort properties)
- `python -m scripts.format --check` - Validate formatting without modifying

### Modifications (fallback if no pnpm script)

- `python -m scripts.depreciate [--from YYYY-MM] [--to YYYY-MM] ITEM AMOUNT CURRENCY` - Depreciate asset
- `python -m scripts.shift [--from YYYY-MM] [--to YYYY-MM] ACCOUNT AMOUNT CURRENCY` - Shift balances
- `python -m scripts.replace FIND REPLACE` - Find/replace across journals

### Security (fallback if no pnpm script)

- `python -m scripts.encrypt` - Encrypt private.yaml
- `python -m scripts.decrypt` - Decrypt private.yaml.gpg

## pnpm Tasks

- `pnpm install` - Install dependencies
- `pnpm run check` - Validate journals and run all checks
- `pnpm run format` - Run all formatters (journals, markdown, prettier, python)
- `pnpm run hledger:check` - Validate journals
- `pnpm run hledger:format` - Format journals
- `pnpm run hledger:format:check` - Check journal formatting
- `pnpm run check:md` - Markdown lint
- `pnpm run check:prettier` - Prettier check
- `pnpm run check:py` - Python checks (ruff, isort, black)
- `pnpm run format:md` - Markdown auto-fix
- `pnpm run format:prettier` - Prettier auto-fix
- `pnpm run format:py` - Python auto-fix
- `pnpm run commitlint` - Lint commit messages

  Note: Prettier is invoked via CLI using explicit file globs in `package.json`. Lint-staged specifies file globs directly; we no longer export a shared `FILE_GLOBS` constant from `.prettierrc.mjs`. The Prettier file globs have been expanded to include additional file types (for example: astro, graphql, json5, mdx, svelte, vue, xml) to ensure broader formatting coverage.

## Monthly Journal Discovery

Scripts use glob `**/*[0-9]{4}-[0-9]{2}/*.journal` to find all monthly journals recursively.

## Python Code Patterns

- Frozen dataclasses: `@dataclass(frozen=True, slots=True, kw_only=True, match_args=False)`
- Concurrency: `asyncio.BoundedSemaphore` limited to CPU count (or 4)
- I/O: `anyio.Path` for async file operations
- Module exports: All Python modules in `scripts/` MUST define a module-level `__all__` tuple listing public symbols; use `()` if there are no exports.

## Pre-Commit Validation (Husky + lint-staged)

```powershell
pnpm run format        # Run all formatters (formats files repo-wide)
pnpm run check         # Validate all journals and run all checks
# Fix any errors before commit
git commit -m "message"
```

**Setup:** after `pnpm install` the `postinstall` script will run `python -m pip install -e . --group dev` to install development extras declared in `pyproject.toml` using the new dependency group syntax. We removed `requirements.txt` to avoid duplication: the canonical source of dependency metadata is `pyproject.toml` (use `pip install -e . --group dev` to reproduce the behavior locally). Because `pyproject.toml` declares no installable packages, installing dev extras will not place project packages into the environment (it only installs extras).
**Script commands: Always run from the `scripts/` directory**

- For all Python scripts (e.g., `python -m check`, `python -m format`, `python -m depreciate`, `python -m shift`, `python -m replace`, `python -m encrypt`, `python -m decrypt`), **always set the working directory to `scripts/` using the tool's `cwd` parameter**. This applies to both direct Python invocations and all script wrappers (e.g., `./check`, `check.bat`, etc.).
- **Never run scripts from the root directory or any other location.** Running from the wrong directory will cause include and file discovery errors.
- Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.

**Critical:** If you run any script or wrapper from the wrong directory, you will encounter include errors, missing file errors, or incorrect results. Always double-check the working directory before running any script command.

Validation checks:

- accounts, assertions, autobalanced, balanced, commodities, ordereddates, parseable, payees, tags

## Commit Message Format

See [git-commits.instructions.md](./git-commits.instructions.md)

For ledger transaction commits only: `ledger(<list>): add N / edit M transaction(s)` (single-line header, no body)
