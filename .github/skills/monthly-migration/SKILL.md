---
name: monthly-migration
description: Perform monthly journal migration using hledger close --migrate to close the previous month and open the new month with proper balance assertions and account initialization.
---

# Monthly Migration Skill

This skill guides you through the monthly journal migration process to properly close one month and initialize the next month.

## When to Use This Skill

- At the start of each month (typically 1st-3rd) before adding new transactions
- After the previous month is complete and all transactions are finalized
- When setting up opening/closing balances for the month
- When preparing both main and alternatives journals for new month

## Prerequisites

- All transactions for the previous month are finalized and validated
- Both `self.journal` and `self.alternatives.journal` journals need migration
- You have run `python -m check` to validate the previous month

## Step-by-Step Process

### 1. Run Migration Commands

Close both journal types for the previous month:

```powershell
# Example: Close December 2025, prepare for January 2026
hledger close -f ledger/2025/2025-12/self.journal --migrate
hledger close -f ledger/2025/2025-12/self.alternatives.journal --migrate
```

**Note:** Commands are run separately, one per journal file.

### 2. Understand the Output

The `hledger close --migrate` command generates two transactions:

1. **Closing balances**: Zeroes out all accounts at month-end

   ```hledger
   2025-12-31 closing balances  ; time: 23:59:59
       assets:banks:<uuid>:HKD     -5000.00 HKD = 0.00 HKD
       assets:cash                 -1000.00 HKD = 0.00 HKD
       ...
       equity:opening/closing balances
   ```

2. **Opening balances**: Re-establishes account balances for new month

   ```hledger
   2026-01-01 opening balances  ; time: 00:00:00
       assets:banks:<uuid>:HKD      5000.00 HKD = 5000.00 HKD
       assets:cash                  1000.00 HKD = 1000.00 HKD
       ...
       equity:opening/closing balances
   ```

### 3. Add Closing Balances to Old Month

Copy the closing balances transaction to the **end** of the old month's journal:

```hledger
# At end of ledger/2025/2025-12/self.journal
2025-12-31 closing balances  ; time: 23:59:59
    assets:banks:<uuid>:HKD     -5000.00 HKD = 0.00 HKD
    ...
    equity:opening/closing balances
```

### 4. Create New Monthly Journal (if needed)

Create new directory and file:

```powershell
mkdir ledger/2026/2026-01
New-Item ledger/2026/2026-01/self.journal
```

Include the prelude:

```hledger
include ../../../preludes/self.journal
```

### 5. Add Opening Balances to New Month

Copy opening balances to the **start** of the new month's journal (after the prelude include):

```hledger
# At start of ledger/2026/2026-01/self.journal
include ../../../preludes/self.journal

2026-01-01 opening balances  ; time: 00:00:00
    assets:banks:<uuid>:HKD      5000.00 HKD = 5000.00 HKD
    assets:cash                  1000.00 HKD = 1000.00 HKD
    ...
    equity:opening/closing balances

# Then add new transactions below...
```

### 6. Adjust Entry Dates (if needed)

The hledger close command generates standard times. Adjust to actual month boundaries:

- **Closing balances**: Should be last day of month at 23:59:59 (e.g., `2025-12-31 23:59:59`)
- **Opening balances**: Should be first day of month at 00:00:00 (e.g., `2026-01-01 00:00:00`)

Adjust if hledger generated different dates.

### 7. Verify Balance Assertions

Closing balances entry should show all accounts with `= 0.00 CURRENCY` assertions:

```hledger
2025-12-31 closing balances
    assets:banks:<uuid>:HKD              -5000.00 HKD = 0.00 HKD
    assets:digital:Octopus:<uuid>         -500.00 HKD = 0.00 HKD
    assets:cash                          -1000.00 HKD = 0.00 HKD
    ...
    equity:opening/closing balances
```

All lines should balance to zero.

### 8. Validate and Format

Validate the migration with:

```powershell
python -m check              # Check for errors
python -m format             # Format both journals
```

### 9. Reference Recent Examples

Examine recent monthly journals for exact formatting and structure:

```powershell
cat ledger/2025/2025-12/self.journal | tail -50  # View closing balances
cat ledger/2026/2026-01/self.journal | head -50  # View opening balances
```

## Do's and Don'ts

**Do:**

- Run for both `self.journal` and `self.alternatives.journal`
- Create new directory and file if new month's journal doesn't exist
- Include prelude in new monthly journal
- Verify closing balances show `= 0.00 CURRENCY` for all accounts
- Run check and format after migration

**Don't:**

- Edit `hledger close` output extensively—trust its calculations
- Forget to create new month's journal before adding transactions
- Skip the prelude include in new monthly journals
- Commit without running check and format
- Perform migration multiple times for same month

## Post-Migration Checklist

```powershell
# 1. Validate all journals
python -m check

# 2. Format all journals
python -m format

# 3. Review changes
git status
git diff

# 4. Commit
git commit -S -m "Migrate journals to new month (Jan 2026)"

# 5. Verify you can now add transactions to new month
```

## Related Documentation

- [Architecture & File Organization](../../instructions/architecture.instructions.md) - Journal hierarchy and structure
- [Common Workflows](../../instructions/common-workflows.instructions.md) - Other practical workflows
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices for journal editing
