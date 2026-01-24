---
name: validate-journals
description: Validate hledger journal files using check/format scripts. Includes validation procedures and pre-commit verification.
---

# Validate Journals Skill

Validate journals to catch errors and ensure consistency before committing.

## When to Use

- Before committing changes
- After editing journal files
- When adding new transactions or accounts
- When troubleshooting validation errors

## Quick Start

```powershell
python -m format       # Auto-format journals
python -m check        # Validate all journals

# Fix any errors shown, then commit
git commit -S -m "your message"
```

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

| Error | Fix |
|-------|-----|
| Account not defined | Add to `preludes/self.journal` |
| Balance mismatch | Fix transaction or prior balances |
| Transaction not balanced | Add missing postings |
| Payee not defined | Add to `preludes/self.journal` |
| Tag not defined | Add to `preludes/self.journal` |
| Date out of order | Correct date or reorder |

## Format Validation

The formatter normalizes:

- Amounts to 2 decimal places: `50.00 HKD`
- Large numbers with spaces: `16 966.42 HKD`
- Comment properties alphabetically: `activity:, eating:, time:, timezone:`
- Preserves UUIDs: `assets:banks:<bank-uuid>`

## Pre-Commit Workflow

```powershell
1. python -m format       # Normalize formatting
2. python -m check        # Validate
3. git status && git diff # Review changes
4. git commit             # Commit when clean
```

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
