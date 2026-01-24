---
name: Developer Workflows
description: Development workflows, utility scripts, code patterns, and testing/validation practices.
---

# Developer Workflows

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
python -m format       # Normalize formatting
python -m check        # Validate  all journals
# Fix any errors before commit
git commit -m "message"
```

Validation checks:

- accounts, assertions, autobalanced, balanced, commodities, ordereddates, parseable, payees, tags

## Commit Message Format

See [git-commits.instructions.md](./git-commits.instructions.md)

For ledger transaction commits only: `ledger(<list>): add N / edit M transaction(s)` (single-line header, no body)
