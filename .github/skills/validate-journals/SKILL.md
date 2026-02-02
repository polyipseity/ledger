---
name: validate-journals
description: Validate hledger journal files using check/format scripts. Includes validation procedures and local hook (Husky + lint-staged) verification.
---

# Validate Journals Skill

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When validating or formatting journals, use the todo list tool to break down the process into actionable steps.**

Mark each step as in-progress and completed, and update the todo list after each change to ensure all validation steps are completed and nothing is missed.

Validate journals to catch errors and ensure consistency before committing.

## When to Use

- Before committing changes
- After editing journal files
- When adding new transactions or accounts
- When troubleshooting validation errors

## Quick Start

```powershell
python -m format       # Auto-format journals (set cwd to scripts/)
python -m check        # Validate all journals (set cwd to scripts/)

# Fix any errors shown, then commit
git commit -S -m "your message"
```

**Script commands: Always run from the `scripts/` directory**

- For all Python scripts (e.g., `python -m check`, `python -m format`, `python -m depreciate`, `python -m shift`, `python -m replace`, `python -m encrypt`, `python -m decrypt`), **always set the working directory to `scripts/` using the tool's `cwd` parameter**. This applies to both direct Python invocations and all script wrappers (e.g., `./check`, `check.bat`, etc.).
- **Never run scripts from the root directory or any other location.** Running from the wrong directory will cause include and file discovery errors.
- Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.

**Critical:** If you run any script or wrapper from the wrong directory, you will encounter include errors, missing file errors, or incorrect results. Always double-check the working directory before running any script command.

## What Check Validates

The `python -m check` script runs hledger `--strict` mode checking:

- **accounts** - All accounts defined in preludes
- **assertions** - Balance assertions match
- **autobalanced** - Postings balanced
- **balanced** - Double-entry bookkeeping (transactions balance)
- **commodities** - Commodity usage matches definitions
- **ordereddates** - Date ordering correct
- **parseable** - Valid hledger syntax
- **payees** - Payee definitions exist
- **tags** - Tag usage matches definitions

## Common Errors & Fixes

| Error                    | Fix                               |
| ------------------------ | --------------------------------- |
| Account not defined      | Add to `preludes/self.journal`    |
| Balance mismatch         | Fix transaction or prior balances |
| Transaction not balanced | Add missing postings              |
| Payee not defined        | Add to `preludes/self.journal`    |
| Tag not defined          | Add to `preludes/self.journal`    |
| Date out of order        | Correct date or reorder           |

## Format Validation

The formatter normalizes:

- Amounts to 2 decimal places: `50.00 HKD`
- Large numbers with spaces: `16 966.42 HKD`
- Comment properties alphabetically: `activity:, eating:, time:, timezone:`
- Preserves UUIDs: `assets:banks:<bank-uuid>`

## Pre-Commit Workflow (Husky + lint-staged)

```powershell
1. pnpm run format        # Format all files (or rely on lint-staged for staged files configured in `.lintstagedrc.mjs`)
2. python -m check        # Validate (set cwd to scripts/)
3. git status && git diff # Review changes
4. git commit             # Commit when clean
```

**Setup note:** `pnpm install` will run `python -m pip install -e . --group dev` to install development extras declared in `pyproject.toml` using the new dependency group syntax. Because `pyproject.toml` declares no installable packages, this will only install extras and will not add project packages to the environment.

**Important:** Always set the working directory to `scripts/` using the tool's `cwd` parameter when running any script or wrapper (including `./check`, `check.bat`, etc.). Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default. Running from the wrong directory will cause include and file discovery errors.

## Checking Specific Months

```powershell
# Check single month instead of all
hledger -f ledger/2025/2025-01/self.journal --strict bal

# Verify specific account
hledger -f ledger/index.journal accounts | grep "your-search"
hledger -f ledger/index.journal register "assets:cash"
```

## Best Practices

- Validate frequently (not just before commit)
- Format before validation
- Fix errors immediately
- Keep preludes clean
- Always run `python -m check` before committing

## Related Documentation

- [Developer Workflows](../../instructions/developer-workflows.instructions.md) - Script patterns
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices
- [Common Workflows](../../instructions/common-workflows.instructions.md) - Workflows overview
