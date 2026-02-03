---
name: Editing Guidelines
description: Best practices for editing and maintaining personal ledger journals.
applyTo: "**/*.journal"
---


# Editing Guidelines

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When editing journals, especially for multi-step or complex changes, use the todo list tool to plan, track, and complete each step.**

Break down editing tasks into actionable steps, mark each as in-progress and completed, and update the todo list after each change to ensure nothing is missed.

## Account and Payee Directive Ordering

When adding or editing `account` or `payee` directives in any journal or prelude file, always ensure that all such directives are listed in strict lexicographical (ASCII/Unicode) order. This applies to both new insertions and corrections of existing out-of-order lines. If a new directive is added, it must be inserted at the correct position to maintain this order. If any out-of-order lines are found, they must be moved to restore proper ordering as part of the edit.

This rule applies to all account, payee, and similar declaration blocks, regardless of account type or hierarchy depth. This ensures consistency, reduces merge conflicts, and supports automated validation tools.

**Example:**

```hledger
account equity:friends:bfa32943-960d-4df1-9997-e2391f5551a1 ; type: E
account equity:friends:dcc61afa-699f-4927-8ec5-8179d50f87d2 ; type: E
account equity:friends:e058a619-cd7a-4ef6-a859-3825f15e8cbc ; type: E
```

**Do not** append new accounts to the end of the block or leave out-of-order lines uncorrected.

See [edit-journals](../skills/edit-journals/) skill for complete guidance.

## Script Usage for Validation/Formatting

**Always use pnpm script wrappers if available for validation and formatting before commit.**

- Use `pnpm run check` and `pnpm run format` from the repository root for validation and formatting.
- Only use direct Python invocations (e.g., `python -m scripts.check`) or script wrappers in `scripts/` if no pnpm script is available, and set cwd to `scripts/`.

- Include preludes in monthly journals
- Maintain balance assertions
- Tag all transactions appropriately
- Format and validate before committing
- Maintain opening/closing patterns
- **Strictly maintain chronological order:** All transactions in every journal file must be strictly ordered by date, and by time within each date. Out-of-order entries are not permitted. Always insert new transactions in the correct chronological position. When adding or editing transactions, always check for and enforce correct time order within each date. If multiple transactions share the same date, they must be sorted by their time (using the `time:` tag or, if missing, by logical/expected sequence). Never leave or introduce out-of-order transactions. This rule must be checked and enforced every time transactions are added or edited.
- Register all payees in the appropriate `preludes/*.journal` file using `payee` lines. Never declare payees in monthly or yearly journals. Always insert new payees in strict lexicographical (ASCII/Unicode) order within the payee section. When adding a payee, check the entire payee section to ensure correct placement and move any out-of-order entries if found.
- When adding or moving account declarations in any prelude file, always insert the new account in strict lexicographical (ASCII/Unicode) order within its section. Never remove or alter unrelated lines. Before inserting, check the entire section to ensure correct placement and move any out-of-order entries if found.

### Shared Expense and Repayment Pattern

When a friend pays for a group meal or shared expense, the original transaction must:

- Itemize all expenses as usual.
- Add `equity:friends:<uuid>` lines for each friend's share (including yourself if you are not the payer).
- Add negative expense lines for the total of others' shares to offset the full amount.
- Add a `liabilities:loans:friends:<uuid>` line for the total amount paid by the friend for others, with a balance assertion (e.g., `= -654.00 HKD`).
- Annotate lines for clarity (e.g., `; paid by friend, other's share`).

When you repay the friend:

- Add a transaction debiting your asset account and crediting the liability, asserting the balance to zero (e.g., `= 0.00 HKD`).
- Include all relevant reference numbers and tags.

For new friends without UUIDs:

- Use a placeholder and update the prelude and transactions once the UUID is assigned.

This pattern ensures correct tracking of group expenses, liabilities, and repayments, and should be followed for all shared expense and group payment situations. See also the add-transactions and lending/borrowing skills for more details.

## Anti-Patterns to Avoid

- Manually editing year-level journals (use monthly journals only)
- Committing without validation (`python -m check`)
- Missing timezone tags (always use UTC+08:00)
- Spaces in account names (use colons)
- Unencrypted confidential files (encrypt before commit)
- **Out-of-order transactions:** Never insert or leave transactions out of chronological order (by date, then by time). This is a critical error and must be corrected immediately.
- Declaring payees anywhere except a `preludes/*.journal` file (never add `payee` lines to monthly or yearly journals). Adding payees out of lexicographical order, or failing to correct existing order mistakes.

## Related Documentation

- [edit-journals](../skills/edit-journals/) - Complete journal editing guidance
- [add-transactions](../skills/add-transactions/) - Adding transactions from raw data
- [validate-journals](../skills/validate-journals/) - Validation and formatting
- [Transaction Format Conventions](./transaction-format.instructions.md) - Transaction structure
- [Account Hierarchy](./account-hierarchy.instructions.md) - All available accounts
