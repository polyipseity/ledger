---
name: validate-journals
description: Validate hledger journal files using check/format scripts. Includes validation procedures and local hook (Husky + lint-staged) verification.
---

# Validate Journals Skill

**Note:** Use full path `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`).

Validate journals to catch errors and ensure consistency before committing.

## When to Use

- Before committing changes
- After editing journal files
- When adding new transactions or accounts
- When troubleshooting validation errors

## Quick Start

**Note:** Use canonical scripts: `bun run format` then `bun run check` (or `python -m ...` with `cwd=scripts/` when required). See `.agents/instructions/developer-workflows.instructions.md` and `.agents/instructions/agent-quickstart.instructions.md` for details and quick commands.

**Examples:** See `./examples.md` for quick validation command examples and common fixes.

**Tip (integrated):** Run `bun run format` first to reduce noisy validation failures — advice reflected in `lessons.md`.

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

| Error                          | Fix                                                                                                |
| ------------------------------ | -------------------------------------------------------------------------------------------------- |
| Account not defined            | Add to `preludes/self.journal`                                                                     |
| Balance mismatch               | Fix transaction or prior balances                                                                  |
| Transaction not balanced       | Add missing postings                                                                               |
| Payee not defined              | Add to `preludes/self.journal`                                                                     |
| Tag not defined                | Add to `preludes/self.journal`                                                                     |
| Date out of order              | Correct date or reorder                                                                            |
| Small closing/opening mismatch | Compare the affected account running balance and adjust the matched opening/closing equity posting |

## Format Validation

The formatter normalizes:

- Amounts to 2 decimal places: `50.00 HKD`
- Large numbers with spaces: `16 966.42 HKD`
- Comment properties alphabetically: `activity:, eating:, time:, timezone:`
- Preserves UUIDs: `assets:banks:<bank-uuid>`

**Note:** See `.agents/instructions/common-workflows.instructions.md` for the canonical Pre-Commit Checklist (Husky + lint-staged) and setup instructions, including running `bun run format`, `python -m check`, and `bun run test`. Also see `.agents/instructions/developer-workflows.instructions.md` for `scripts/` working directory guidance.

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
- When fixing month-end balances, validate the corrected month and the following month together
- Always run `python -m check` before committing
