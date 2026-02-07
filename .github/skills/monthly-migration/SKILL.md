---
name: monthly-migration
description: Perform monthly journal migration using hledger close --migrate to close the previous month and open the new month with proper balance assertions and account initialization.
---



# Monthly Migration Skill

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Prefer `typing.Self` for methods that return the instance type (for example: `def clone(self) -> typing.Self:`); if supporting Python versions older than 3.11, use `typing_extensions.Self`. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. Avoid using `Any` or `Unknown` in type annotations; prefer explicit types, Protocols, or TypedDicts. Exception: `Any` or `Unknown` may be used only when there is a very strong, documented justification (for example, interfacing with untyped third-party libraries or representing truly dynamic/opaque data structures). When used, include an inline comment explaining the justification and a `# TODO` to refine the type later. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

Guide for migrating journals at the start of each month.

## When to Use

- Start of each month (typically 1st-3rd) before adding new transactions
- Previous month is complete and validated
- Setting up opening/closing balances

## Prerequisites

- All transactions for previous month finalized
- Both `self.journal` and `self.alternatives.journal` need migration
- Ran `python -m check` successfully

## Process

### 1. Run Migration Commands

Close both journal types:

```powershell
# Example: Close December 2025, prepare for January 2026
hledger close -f ledger/2025/2025-12/self.journal --migrate
hledger close -f ledger/2025/2025-12/self.alternatives.journal --migrate
```

Run separately—one per journal file.

### 2. Understand Output

`hledger close --migrate` generates two transactions:

1. **Closing balances**: Zeroes all accounts at month-end

   ```hledger
   2025-12-31 closing balances  ; time: 23:59:59
       assets:banks:<uuid>:HKD     -5000.00 HKD = 0.00 HKD
       ...
       equity:opening/closing balances
   ```

2. **Opening balances**: Re-establishes for new month

   ```hledger
   2026-01-01 opening balances  ; time: 00:00:00
       assets:banks:<uuid>:HKD      5000.00 HKD = 5000.00 HKD
       ...
       equity:opening/closing balances
   ```

### 3. Add Closing to Old Month

Copy closing balances to **end** of previous month journal.

### 4. Create New Monthly Journal

If new month directory doesn't exist:

```powershell
mkdir ledger/2026/2026-01
New-Item ledger/2026/2026-01/self.journal
```

Include prelude:

```hledger
include ../../../preludes/self.journal
```

### 5. Add Opening to New Month

Copy opening balances to **start** of new month (after prelude).

### 6. Adjust Times if Needed

Verify dates/times are correct:

- Closing: last day of month at 23:59:59
- Opening: first day of month at 00:00:00

### 7. Validate

```powershell
python -m check   # set cwd to scripts/
python -m format  # set cwd to scripts/
```

**Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical guidance — prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

### 8. Commit

```powershell
git commit -S -m "chore(migration): migrate journals to 2026-01"
```

## Do's and Don'ts

**Do:**

- Run for both `self.journal` and `self.alternatives.journal`
- Create new directory/file if needed
- Include prelude in new journal
- Verify closing balances show `= 0.00 CURRENCY`
- Run check and format after

**Don't:**

- Edit hledger close output extensively
- Forget prelude include
- Skip validation before commit
- Perform migration multiple times for same month

## Reference Recent Examples

```powershell
cat ledger/2025/2025-12/self.journal | tail -50  # View closing
cat ledger/2026/2026-01/self.journal | head -50  # View opening
```

## Related Documentation

- [Architecture](../../instructions/architecture.instructions.md) - Journal structure
- [Common Workflows](../../instructions/common-workflows.instructions.md) - Other workflows
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices
