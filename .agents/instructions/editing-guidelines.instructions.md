---
name: Editing Guidelines
description: Best practices for editing and maintaining personal ledger journals.
applyTo: "**/*.journal"
---


# Editing Guidelines

## Account and Payee Directive Ordering

`account` and `payee` directives are listed in strict lexicographical (ASCII/Unicode) order, and a new directive is inserted at the position it sorts into. Restoring an order that is already broken is its own change: an inversion you notice is reported and repaired separately, never re-sorted inside the edit that found it.

The rule covers every declaration block, regardless of account type or hierarchy depth, so a new account also joins the correct position within its own section.

**Example:**

```hledger
account equity:friends:bfa32943-960d-4df1-9997-e2391f5551a1 ; type: E
account equity:friends:dcc61afa-699f-4927-8ec5-8179d50f87d2 ; type: E
account equity:friends:e058a619-cd7a-4ef6-a859-3825f15e8cbc ; type: E
```

**Do not** append a new account to the end of the block.

## Script Usage for Validation/Formatting

**Scripts & validation**: See `.agents/instructions/developer-workflows.instructions.md` for canonical guidance. Short: `bun run check` and `bun run format` from the repository root, or `uv run --locked -m scripts.<mod>` from that same root.

- Include preludes in monthly journals
- Maintain balance assertions
- Tag all transactions appropriately
- Format and validate before committing
- Maintain opening/closing patterns
- **Chronological order:** Always insert transactions in strict chronological order (date, then time). See `.agents/instructions/transaction-format.instructions.md` for the canonical rules.
- **Payees:** Register payees in `preludes/*.journal` (alphabetized). See `.agents/skills/add-payee/SKILL.md` and `transaction-format.instructions.md` for details.
- When adding or moving account declarations in any prelude file, always insert the new account in strict lexicographical (ASCII/Unicode) order within its section. Never remove or alter unrelated lines.

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

This pattern ensures correct tracking of group expenses, liabilities, and repayments, and should be followed for all shared expense and group payment situations. See also `.agents/skills/ingest-lending/SKILL.md` and `.agents/skills/ingest/SKILL.md` for more details.

## Anti-Patterns to Avoid

**For comprehensive anti-patterns reference, see [continuous-learning.instructions.md](./continuous-learning.instructions.md)** — consolidated guide to pitfalls and lessons learned across all skills.

Below are the most critical patterns specific to journal editing:

- Manually editing year-level journals (use monthly journals only)
- Committing without validation (`bun run format && bun run check`)
- Missing timezone tags (record the zone the source printed; `.agents/instructions/transaction-format.instructions.md` states the rule)
- Spaces in account names (use colons)
- Unencrypted confidential files (encrypt before commit)
- **Out-of-order transactions:** Never insert or leave transactions out of chronological order (by date, then by time). This is a critical error and must be corrected immediately.
- Declaring payees anywhere except a `preludes/*.journal` file (never add `payee` lines to monthly or yearly journals).
