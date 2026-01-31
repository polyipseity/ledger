# Lending and Borrowing Transactions Theme

This file contains rules, clarifications, and examples specific to lending, borrowing, and repayment transactions. Use this file whenever a transaction involves loans, repayments, or pending/cleared status markers.

## When to Use

- Any transaction involving lending money, borrowing, or repaying debts
- Transactions that require `!` (pending) or `*` (cleared) status markers

## Key Rules

- Use `!` for pending lending/borrowing, `*` for cleared
- Repayments must update status of related pending transactions
- Use liability assertion (`= 0.00 <CURRENCY>`) when settling a liability
- Always use canonical payee names or UUIDs as per SKILL.md
- Insert transactions in strict chronological order

### Shared Expense and Repayment Pattern

For group meals or shared expenses paid by a friend, follow the shared expense and repayment pattern:

- In the original transaction, itemize all expenses, add `equity:friends:<uuid>` lines for each friend's share, negative expense lines for others' shares, and a `liabilities:loans:friends:<uuid>` line for the total paid by the friend (with balance assertion).
- When repaying, add a transaction debiting your asset and crediting the liability, asserting the balance to zero.
- Use placeholders for new friends without UUIDs and update later.

See editing-guidelines and add-transactions SKILL.md for full details and rationale.

### Status Markers

- `!` = pending (awaiting confirmation, repayment, or follow-up)
- `*` = cleared (verified, all parties settled)
- no marker = normal transaction

**Update status:** Change `!` to `*` when a pending transaction completes:

```hledger
2025-01-15 ! Friend Lunch                    # Pending
 assets:loans:friends:<uuid>      50.00 HKD
 assets:cash                     -50.00 HKD

2025-01-20 * Friend Lunch                    # Update to cleared when repaid
 assets:loans:friends:<uuid>      50.00 HKD = 0.00 HKD
 assets:banks:<bank-uuid>        -50.00 HKD
```

### Liability Assertions

- When recording a repayment that settles a liability (any `liabilities:*` account), append an assertion `= 0.00 <CURRENCY>` to the liability posting. This makes the debt clearance explicit and helps catch inconsistencies. Related pending transactions (`!`) with the same counterparty should be marked as cleared (`*`) once repayment is confirmed.

### Pending Transaction State Transitions

- When a repayment transaction is added and settles one or more pending (`!`) transactions, update those pending transactions to cleared (`*`) status to reflect the completed settlement.

### Clarification Patterns (Lending/Borrowing)

- Shared meal: If reimbursement is expected, use `assets:loans` and mark as pending. If fully covered, record as a single transaction. If already split, record only your portion.

See SKILL.md for general procedures and cross-theme rules.

## Examples

(Include detailed examples from SKILL.md and user feedback here)

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [id_mappings.yml](./id_mappings.yml)
- [SKILL.md](./SKILL.md)
