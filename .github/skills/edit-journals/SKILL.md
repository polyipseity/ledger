---
name: edit-journals
description: Edit hledger journal files following best practices and conventions. Includes prelude includes, balance assertions, tagging, formatting, and validation procedures with anti-patterns to avoid.
---

# Edit Journals Skill

This skill provides comprehensive guidance for editing hledger journal files while maintaining consistency, validity, and adherence to project conventions.

## When to Use This Skill

- Adding, modifying, or removing transactions
- Creating new monthly journals
- Editing prelude definitions
- Maintaining opening/closing balances
- Correcting historical entries
- Updating confidential mappings

## Best Practices

### 1. Always Include Preludes

Monthly journals must start with the prelude include:

```hledger
include ../../../preludes/self.journal

2025-01-01 opening balances
    ...
```

This ensures all account definitions, commodity formats, payees, and tags are available.

**For alternatives journals:**

```hledger
include ../../../preludes/self.alternatives.journal

2025-01-01 opening balances
    ...
```

### 2. Maintain Balance Assertions

Use `= balance CURRENCY` on important accounts to validate data integrity:

```hledger
2025-01-19 Payment
    assets:banks:<bank-uuid>:HKD      -100.00 HKD = 4900.00 HKD
    expenses:food:dining               100.00 HKD
```

Balance assertions:

- Catch data entry errors early
- Provide checkpoints for reconciliation
- Document expected balances at specific points

**When to assert:**

- Bank transactions (against statement balances)
- Account transfers (verify both sides)
- End-of-month (document closing balances)
- Loan repayments (verify zero balance when paid)

### 3. Tag Appropriately

Include essential metadata tags in transaction comments:

```hledger
2025-01-19 Example Cafe  ; activity: eating, eating: lunch, time: 12:30, timezone: UTC+08:00
    expenses:food and drinks:dining     50.00 HKD
    assets:digital:Octopus:<uuid>      -50.00 HKD
```

**Required tags:**

- `timezone`: Always UTC+08:00
- `activity`: Category of activity
- `time`: Transaction timestamp

**Recommended tags:**

- `duration`: For activities with time spans (e.g., `PT1H30M`)
- `food_or_drink`: Detailed item descriptions
- `item`: Product/item identifiers
- `location`: Geographic location

Posting order: list credit postings before debit postings within each transaction.

### 4. Format After Editing

Always run the format script after editing:

```powershell
python -m format
```

The formatter:

- Rewrites journals using `hledger print` for canonical format
- Sorts comment properties alphabetically
- Standardizes spacing and indentation
- Preserves include statements unchanged

Running format ensures:

- Consistent style across the ledger
- Canonical hledger representation
- Compatibility with validation scripts

### 5. Validate Before Commit

Always validate before committing:

```powershell
python -m check
```

The check script validates:

- All referenced accounts are defined
- All balance assertions balance
- All commodities are properly declared
- All postings balance within transactions
- Date ordering is correct
- All payees are registered
- All tags are defined

**Fix all errors before committing.**

### 6. Maintain Opening/Closing Pattern

The first and last transactions of each month have special meaning:

- **First transaction**: `opening balances` - Lists starting balance for each account
- **Last transaction**: `closing balances` - Zeroes out accounts at month end

```hledger
# First transaction of month
2025-01-01 opening balances
    assets:cash                       1000.00 HKD = 1000.00 HKD
    assets:banks:<uuid>:HKD           5000.00 HKD = 5000.00 HKD
    ...
    equity:opening/closing balances

# ... regular transactions throughout month ...

# Last transaction of month
2025-01-31 closing balances
    assets:cash                      -1050.00 HKD = 0.00 HKD
    assets:banks:<uuid>:HKD          -4900.00 HKD = 0.00 HKD
    ...
    equity:opening/closing balances
```

Preserving this pattern:

- Enables monthly reconciliation
- Makes month boundaries clear
- Facilitates `hledger close --migrate`

### 7. Sort Properties in Comments

The format script automatically sorts comment properties alphabetically:

```hledger
# Before formatting
2025-01-19 Cafe  ; time: 12:30, activity: eating, timezone: UTC+08:00

# After formatting (properties sorted)
2025-01-19 Cafe  ; activity: eating, time: 12:30, timezone: UTC+08:00
```

This ensures consistent ordering and readability.

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

Never commit unencrypted `private.yaml`:

```powershell
# ❌ Bad: Unencrypted file committed
git add private.yaml
git commit -m "Update confidential data"

# ✅ Good: Only encrypted version committed
python -m encrypt              # Encrypt first
git add private.yaml.gpg       # Add encrypted
git commit -m "Update mappings"
```

See [Security Practices](../../instructions/security.instructions.md) for encryption workflow.

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
git add .
git commit -S -m "Description of changes"

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
