---
name: Developer Workflows
description: Development workflows, utility scripts, code patterns, and testing/validation practices.
---


# Developer Workflows

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When performing development, scripting, or validation tasks, use the todo list tool to break down multi-step operations.**

Plan actionable steps, mark each as in-progress and completed, and update the todo list after each change to ensure all steps are completed and nothing is forgotten.

## Available Scripts

All scripts have three versions: `.sh`, `.bat`, `.py`. Run as `python -m <script>` on all platforms.

### Validation and Formatting

- `python -m check` - Validate journals (hledger strict checking)
- `python -m format` - Auto-format journals (hledger print, sort properties)
- `python -m format --check` - Validate formatting without modifying

### Modifications

- `python -m depreciate [--from YYYY-MM] [--to YYYY-MM] ITEM AMOUNT CURRENCY` - Depreciate asset
- `python -m shift [--from YYYY-MM] [--to YYYY-MM] ACCOUNT AMOUNT CURRENCY` - Shift balances
- `python -m replace FIND REPLACE` - Find/replace across journals

### Security

- `python -m encrypt` - Encrypt private.yaml
- `python -m decrypt` - Decrypt private.yaml.gpg

## pnpm Tasks

- `pnpm install` - Install dependencies
- `pnpm run markdownlint` - Lint markdown
- `pnpm run markdownlint:fix` - Auto-fix markdown
- `pnpm run hledger:check` - Validate journals
- `pnpm run hledger:format` - Format journals
- `pnpm run hledger:format:check` - Check formatting
- `pnpm run commitlint` - Lint commit messages

## Monthly Journal Discovery

Scripts use glob `**/*[0-9]{4}-[0-9]{2}/*.journal` to find all monthly journals recursively.

## Python Code Patterns

- Frozen dataclasses: `@dataclass(frozen=True, slots=True, kw_only=True, match_args=False)`
- Concurrency: `asyncio.BoundedSemaphore` limited to CPU count (or 4)
- I/O: `anyio.Path` for async file operations

## Pre-Commit Validation

```powershell
python -m format       # Normalize formatting (set cwd to scripts/)
python -m check        # Validate all journals (set cwd to scripts/)
# Fix any errors before commit
git commit -m "message"
```

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
