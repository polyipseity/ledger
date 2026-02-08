---
name: monthly-migration
description: Perform monthly journal migration using hledger close --migrate to close the previous month and open the new month with proper balance assertions and account initialization.
---



# Monthly Migration Skill

**Note:** Use full path `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). See `AGENTS.md` for workflow rules.

**Note:** See `AGENTS.md` for agent workflow rules and use the Todo List Tool for multi-step tasks.

**Note:** See `.github/instructions/developer-workflows.instructions.md` for canonical coding, testing, and formatting rules (type annotations, docstrings, `__all__`, test conventions). See `AGENTS.md` for agent workflow rules.

Guide for migrating journals at the start of each month.

## When to Use

- Start of each month (typically 1st-3rd) before adding new transactions
- Previous month is complete and validated
- Setting up opening/closing balances

**Examples:** See `./examples.md` for canonical migration commands and verification steps.

**Quick reference:** See `.github/instructions/agent-glossary.instructions.md` for short definitions.

## Prerequisites

- All transactions for previous month finalized
- Both `self.journal` and `self.alternatives.journal` need migration
- Ran `python -m check` successfully

## Process (condensed)

- Run `hledger close --migrate -f ledger/YYYY/YYYY-MM/self.journal` for each journal to generate closing/opening transactions.
- Copy the generated closing balances into the previous-month journal and the opening balances into the new month (after the prelude include).
- Ensure the new month directory and `self.journal` exist and include the correct prelude (`include ../../../preludes/self.journal`).
- Verify closing timestamps and opening timestamps are correct (closing at 23:59:59, opening at 00:00:00).
- Validate and format (prefer `pnpm run format` and `pnpm run check`).
- Commit using a suitable `chore(migration):` header and include migration context in the commit message.

For detailed examples and edge cases, see `.github/instructions/developer-workflows.instructions.md` and `./examples.md`. (Examples and a short checklist are in `examples.md`.)

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
