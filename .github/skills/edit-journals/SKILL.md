---
name: edit-journals
description: Edit hledger journal files following best practices and conventions. Includes prelude includes, balance assertions, tagging, formatting, and validation procedures with anti-patterns to avoid.
---



# Edit Journals Skill

**Note:** Use full path `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). See `AGENTS.md` and `.github/instructions/agent-quickstart.instructions.md` for workflow rules and a concise checklist.

**Note:** See `.github/instructions/developer-workflows.instructions.md` for canonical coding, testing, and formatting rules (type annotations, docstrings, `__all__`, test conventions). See `AGENTS.md` for agent workflow rules.

This skill provides comprehensive guidance for editing hledger journal files while maintaining consistency, validity, and adherence to project conventions.

## When to Use This Skill

- Adding, modifying, or removing transactions
- Creating new monthly journals
- Editing prelude definitions
- Maintaining opening/closing balances
- Correcting historical entries
- Updating confidential mappings

## Best Practices — At a Glance

- Include the appropriate prelude at the top of every monthly journal (`include ../../../preludes/self.journal` or `self.alternatives.journal`).
- Use balance assertions (`= balance CURRENCY`) for bank reconciliations, transfers, and loans where applicable.
- Always include required tags (`timezone: UTC+08:00`, `activity`, `time`); use `duration`, `food_or_drink`, `item`, `location` when relevant.
- Format and validate using canonical scripts: `pnpm run format` then `pnpm run check` (see `.github/instructions/developer-workflows.instructions.md`). Fix all errors before committing.
- Preserve monthly opening/closing patterns for reconciliation and migration.
- The formatter sorts comment properties; keep transaction comment keys ordered and concise.

For detailed examples and edge cases, see `.github/instructions/transaction-format.instructions.md` and `.github/instructions/editing-guidelines.instructions.md`.

### 8. Document Complex Transactions

For non-obvious transactions, add explanatory comments:

```hledger
2025-01-19 Insurance Adjustment  ; reason: coverage review
    liabilities:accrued expenses:insurances:life:<uuid>   -100.00 HKD
    equity:unaccounted                                      100.00 HKD
```

Helps future understanding of why transactions were recorded.

## Anti-Patterns to Avoid

### ❌ Do Not Edit Year-Level Journals Manually

The year-level `ledger/YYYY/self.journal` files should **only** contain include directives:

```hledger
include 2025-01/self.journal
include 2025-02/self.journal
include 2025-03/self.journal
...
```

**Never add transactions here.** Transactions belong in monthly journals.

**Why?** Year-level files are for organization only. Adding transactions here breaks the hierarchical structure.

### ❌ Do Not Commit Without Validation

Always run `python -m check` before committing:

```powershell
# ❌ Bad: Direct commit
git commit -m "Add transaction"

# ✅ Good: Validate first
python -m check
python -m format
git commit -m "Add transaction"
```

Invalid journals cause downstream problems.

### ❌ Do Not Use Inconsistent Formatting

Maintain consistent decimal and spacing:

```hledger
# ❌ Inconsistent
2025-01-19 Payment
    expenses:food                50 HKD      # Missing decimal
    assets:cash                  -50.0 HKD   # Only 1 decimal place
    
# ✅ Consistent (after python -m format)
2025-01-19 Payment
    expenses:food                50.00 HKD
    assets:cash                 -50.00 HKD
```

Always run `python -m format` to normalize.

### ❌ Do Not Create Transactions Without Timezone Tags

Every transaction must include timezone information:

```hledger
# ❌ Missing timezone
2025-01-19 Cafe  ; activity: eating, time: 12:30

# ✅ Includes timezone
2025-01-19 Cafe  ; activity: eating, time: 12:30, timezone: UTC+08:00
```

Timezone tags are essential for proper time tracking.

### ❌ Do Not Modify Prelude Definitions Lightly

Changes to [preludes/self.journal](../../../preludes/self.journal) affect **all** monthly journals:

```hledger
# Changes here impact all journals!
account assets:cash
commodity HKD
payee Example Payee
tag activity
```

**Before modifying prelude definitions:**

1. Understand the global impact
2. Check how many journals reference the definition
3. Test validation across all journals
4. Document the change in commit message

### ❌ Do Not Leave Unencrypted Confidential Files

**Note:** Never commit unencrypted `private.yaml`. See `.github/instructions/security.instructions.md` for the canonical encryption/decryption workflow and requirements.

### ❌ Do Not Remove Existing Accounts or Payees

Once an account or payee is used, removing it breaks historical references:

```hledger
# ❌ Bad: Removes existing definition
# (delete from preludes/self.journal)
account assets:cash

# ✅ Good: Keep definitions even if unused
# Let check script find any unused definitions separately
```

Payees and accounts are part of ledger history.

### ❌ Do Not Use Spaces in Account Names

Account paths must use colons, not spaces:

```hledger
# ❌ Invalid
account assets:cash on hand:HKD

# ✅ Valid
account assets:cash:HKD
```

Spaces break account parsing.

## Editing Workflow

Recommended workflow for any journal edits:

```powershell
# 1. Make edits to journal files
# [Edit ledger/2025/2025-01/self.journal or other files]

# 2. Format all journals
python -m format

# 3. Validate all journals
python -m check

# 4. If edited confidential data
# [Decrypt, edit private.yaml, then...]
python -m encrypt

# 5. Review changes
git status
git diff

# 6. Commit
# Use `.github/instructions/git-commits.instructions.md`. For ledger transaction commits use the ledger header and no body.
git add .
git commit -S -m "chore(edit): apply journal edits"

# 7. Push
git push
```

## Common Editing Tasks

### Adding a New Transaction

1. Find recent similar transaction as template
2. Copy template and adjust values
3. Add comprehensive tags
4. Run `python -m format`
5. Verify with `python -m check`
6. Commit

### Adding a New Merchant/Payee

1. Add payee to `preludes/self.journal` in alphabetical order
2. If confidential, add to `private.yaml` and encrypt
3. Run `python -m format` and `python -m check`
4. Commit

### Correcting Historical Transaction

1. Find the transaction in appropriate monthly journal
2. Edit values and/or tags
3. If correction affects balances, update subsequent balance assertions
4. Run `python -m format` and `python -m check`
5. Commit with explanatory message

## Related Documentation

- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md) - Transaction structure and formatting
- [Account Hierarchy & Meanings](../../instructions/account-hierarchy.instructions.md) - All available accounts
- [Security Practices](../../instructions/security.instructions.md) - Handling confidential data
- [Common Workflows](../../instructions/common-workflows.instructions.md) - Other practical procedures
