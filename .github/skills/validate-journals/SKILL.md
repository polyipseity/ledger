---
name: validate-journals
description: Validate hledger journal files using the check and format scripts. Includes validation procedures, error checking, and pre-commit verification to ensure data integrity and consistency.
---

# Validate Journals Skill

This skill guides you through validating hledger journals to catch errors early and ensure consistency across the entire ledger.

## When to Use This Skill

- Before committing changes to the repository
- After editing journal files
- When adding new transactions or accounts
- When modifying prelude definitions
- When troubleshooting validation errors
- When setting up monthly migrations

## Validation Commands

### Check Journals

Validate all journals before committing:

```powershell
python -m check
```

Output shows any errors found. Fix errors before proceeding.

### Format Journals

Auto-format all journals:

```powershell
python -m format
```

Always run after editing to ensure consistent formatting.

## What the Check Script Validates

The check script runs hledger with `--strict` mode checking:

- **accounts**: Verifies all accounts are defined in preludes
- **assertions**: Validates balance assertions match
- **autobalanced**: Ensures balanced postings
- **balanced**: Verifies double-entry bookkeeping (all transactions balance)
- **commodities**: Validates commodity usage matches definitions
- **ordereddates**: Checks date ordering is correct (no time travel)
- **parseable**: Confirms valid hledger syntax
- **payees**: Verifies payee definitions exist
- **tags**: Validates tag usage matches definitions

## Common Validation Errors

### Account Not Defined

```txt
Error: account "assets:unknown:account" is not defined
```

**Fix:** Add account definition to [preludes/self.journal](../../../preludes/self.journal)

### Balance Assertion Mismatch

```txt
Error: balance assertion failed
  Expected: 5000.00 HKD
  Actual:   4950.00 HKD
```

**Fix:** Update transaction to match actual balance or fix prior transactions

### Transaction Not Balanced

```txt
Error: transaction does not balance
  Total: 50.00 HKD
```

**Fix:** Add missing postings to make transaction balance to 0.00

### Payee Not Defined

```txt
Error: payee "Unknown Vendor" is not defined
```

**Fix:** Add payee to [preludes/self.journal](../../../preludes/self.journal)

### Tag Not Defined

```txt
Error: tag "unknown-tag" is not defined
```

**Fix:** Add tag definition to [preludes/self.journal](../../../preludes/self.journal)

### Date Ordering

```txt
Error: transaction date out of order
  Previous: 2025-01-19
  Current:  2025-01-15
```

**Fix:** Correct transaction date or reorder transactions chronologically

## Pre-Commit Validation Workflow

Run before every commit:

```powershell
# 1. Format all journals
python -m format

# 2. Validate all journals
python -m check

# 3. If no errors, review changes
git status
git diff --cached

# 4. Commit
# Use `.github/instructions/git-commits.instructions.md`. When adding/editing transactions use the ledger header and no body.
git commit -S -m "chore: apply validation fixes"
```

## Format Validation

The formatter normalizes journal files:

- Rewrites journals using `hledger print` for canonical format
- Sorts comment properties alphabetically
- Standardizes spacing and indentation
- Preserves include statements unchanged
- Converts amounts to consistent decimal precision (2 places)

**After formatting, verify:**

- All amounts have exactly 2 decimal places: `50.00 HKD`
- Large numbers have space separators: `16 966.42 HKD`
- Comment properties are alphabetically sorted: `activity:, eating:, time:, timezone:`
- Account UUIDs are preserved: `assets:banks:<bank-uuid>`

## Concurrent Validation

Both scripts use concurrent processing:

- **Concurrency limit**: BoundedSemaphore limits to CPU count or 4 (whichever is lower)
- **Prevents resource exhaustion**: Ensures system remains responsive
- **Glob pattern discovery**: Automatically finds all monthly journals (`**/*[0-9]{4}-[0-9]{2}/*.journal`)

## Fixing Validation Errors

### Step 1: Identify the Error

Run check to see which file and line has the error:

```powershell
python -m check
# Output will show specific file path and error message
```

### Step 2: Locate the Problem

Open the file indicated in the error message:

```powershell
# Example: Open the file with the error
code ledger/2025/2025-01/self.journal
```

### Step 3: Apply the Fix

Based on the error type, apply appropriate fix:

- **Account error**: Add account to preludes
- **Balance error**: Fix transaction amounts or prior balances
- **Payee error**: Add payee to preludes
- **Tag error**: Add tag definition to preludes
- **Date error**: Correct transaction date

### Step 4: Re-validate

Run check again to confirm fix:

```powershell
python -m check
```

## Validation Best Practices

### 1. Validate Frequently

Don't wait until end of day or week to validate:

```powershell
# After each transaction addition or edit
python -m format
python -m check
```

### 2. Test New Entries

Before committing, verify new accounts/payees/tags are properly defined:

```powershell
# Will fail if new account not in preludes
python -m check
```

### 3. Format Before Committing

Always format before validation to catch formatting issues early:

```powershell
python -m format    # Normalizes formatting
python -m check     # Then validates
```

### 4. Validate All Journals

The check and format scripts process all monthly journals:

```powershell
python -m check
# Validates: 2024-01, 2024-02, ..., 2025-01, 2025-02, ..., etc.
```

### 5. Keep Preludes Clean

Regularly review prelude definitions to remove unused entries:

```powershell
# Search for unused accounts
grep -r "assets:unused" ledger/
```

## Troubleshooting Validation

### If Check Takes Too Long

```powershell
# Check specific monthly journal instead
hledger -f ledger/2025/2025-01/self.journal --strict bal
```

### If Validation Passes But Something Seems Wrong

```powershell
# Use hledger queries to verify
hledger -f ledger/index.journal accounts | grep "your-account"
hledger -f ledger/index.journal register "assets:cash"
```

### If You Can't Find an Error

```powershell
# Run with verbose output
python -m check 2>&1 | more
```

## Related Documentation

- [Developer Workflows](../../instructions/developer-workflows.instructions.md) - Script patterns and testing
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices and anti-patterns
- [Common Workflows](../../instructions/common-workflows.instructions.md) - Pre-commit checklist
