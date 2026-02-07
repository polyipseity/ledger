---
name: validate-journals
description: Validate hledger journal files using check/format scripts. Includes validation procedures and local hook (Husky + lint-staged) verification.
---

# Validate Journals Skill

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Prefer `typing.Self` for methods that return the instance type (for example: `def clone(self) -> typing.Self:`); if supporting Python versions older than 3.11, use `typing_extensions.Self`. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. Avoid using `Any` or `Unknown` in type annotations; prefer explicit types, Protocols, or TypedDicts. Exception: `Any` or `Unknown` may be used only when there is a very strong, documented justification (for example, interfacing with untyped third-party libraries or representing truly dynamic/opaque data structures). When used, include an inline comment explaining the justification and a `# TODO` to refine the type later. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

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

**Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical guidance — prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

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
