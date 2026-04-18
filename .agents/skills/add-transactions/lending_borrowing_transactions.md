# Lending and Borrowing Transactions Theme

This file contains rules, clarifications, and examples specific to lending, borrowing, and repayment transactions. Use this file whenever a transaction involves loans, repayments, or pending/cleared status markers.

## When to Use

- Any transaction involving lending money, borrowing, or repaying debts
- Transactions that require `!` (pending) or `*` (cleared) status markers

## Key Rules

**Status markers (`!` for pending, `*` for cleared) must be used ONLY for lending, borrowing, and repayment transactions.**

- For shared/group expenses, use `!` only for the initial transaction where a loan or reimbursement is expected, and `*` only when the loan is repaid or settled.
- All other transaction types should NOT use status markers unless directly related to a loan or debt that is pending or cleared.
- Pending transactions (`!`) must be updated to cleared (`*`) when the related repayment or settlement occurs.
- Status markers should be extremely rare and only appear for the first transaction of borrowing/lending away anything of financial value.

If you see a status marker in any transaction that is not a loan/repayment, it is an error and must be corrected.

Repayments must update status of related pending transactions. Use liability assertion (`= 0.00 <CURRENCY>`) when settling a liability. Always use canonical payee names or UUIDs as per SKILL.md. **Note:** Insert transactions in strict chronological order; see `.agents/instructions/transaction-format.instructions.md`.

**Examples:** See `./examples.md` for canonical lending/borrowing and shared expense patterns.

### Shared Expense and Repayment Pattern

For group meals or shared expenses, the pattern depends on whether the expense is settled **immediately** (same-day split with friends present) or **deferred** (you paid first, repayment pending):

#### Immediate Same-Day Split (Use `equity:friends:`)

If the expense is split on the spot among friends who are co-diners and settlement is immediate:

- In the original transaction, itemize all expenses, add `equity:friends:<uuid>` lines with **negative amounts** for each friend's share (representing their equity in the shared meal).
- This is NOT a loan; the friends' shares are recorded as offsets to the expense.
- The payee is the venue (e.g., restaurant name or UUID), not the friend.
- Use `equity:friends:<uuid>` only for immediate splits where ownership/cost is clarified at the time of transaction.
- Example: 2026-04-17 HKUST ramen venue transaction with friend UUID `4491140b-7e34-48fe-8e3d-aca591ed6d6e`: itemizes 36.50 + 10.00 + 4.00 HKD across dining and drinks accounts, then adds a single `equity:friends:4491140b-7e34-48fe-8e3d-aca591ed6d6e` posting with -50.50 HKD (their entire share). This balances the transaction and clarifies that half the expense belongs to the friend by agreement at the time.

#### Deferred Settlement or Reimbursement (Use `liabilities:` and Status Markers)

If the expense is paid by you but repayment is deferred or you expect reimbursement:

- In the original transaction, itemize all expenses and add a `liabilities:` posting (e.g., `liabilities:loans:friends:<uuid>` or `liabilities:credit cards:` if credit was extended).
- Mark the original transaction as pending (`!`) if repayment is outstanding.
- When repaying, add a transaction debiting your asset and crediting the liability, asserting the balance to zero.
- Use placeholders for new friends without UUIDs and update later.
- Example: 2026-04-04 DZô DZô shared meal: if you paid on credit and a friend owes you reimbursement, use `liabilities:credit cards:` and mark as pending (`!`) until repaid.

**Key Distinction:**

- `equity:friends:` = immediate same-day split, no loan involved, friends present, cost clarified at transaction time
- `liabilities:` = deferred settlement, reimbursement expected or pending, possibly on credit, tracked with status markers

See editing-guidelines and add-transactions SKILL.md for full details and rationale.

### Status Markers

- `!` = pending (awaiting confirmation, repayment, or follow-up)
- `*` = cleared (verified, all parties settled)
- no marker = normal transaction

**Update status:** Change `!` to `*` when a pending transaction completes. The repayment transaction (the second in a borrowing/lending pair) must NOT have any status marker. Only the original pending transaction should have a status marker, which is updated to `*` when cleared. The repayment transaction itself should have no status marker.

```hledger
2025-01-15 ! Friend Lunch                    # Pending
 assets:loans:friends:<uuid>      50.00 HKD
 assets:cash                     -50.00 HKD

2025-01-20 Friend Lunch                      # Repayment, no status marker
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
