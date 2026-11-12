---
name: ingest-lending
description: Rules for transcribing loans, repayments, and shared bills into hledger — status markers, the loan account, and the three friend-sharing shapes.
---

# ingest-lending

This aspect decides what a loan, a repayment, or a bill shared with friends contributes: which account holds the balance, when a status marker is warranted, and which of the ledger's three sharing shapes the source calls for. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; `../../instructions/transaction-format.instructions.md` owns the syntax, `../../instructions/account-hierarchy.instructions.md` the accounts, and `../fix-journals/SKILL.md` the check loop. A bill's printed items are `../ingest-food/SKILL.md`'s and its tags are `../ingest-tags/SKILL.md`'s.

## When to use

A source that lends money, borrows it, repays it, or splits a bill with friends: a transfer to or from a person, an IOU, a group meal someone else paid for, a repayment notice, or a statement row naming a friend. A bill where everyone paid their own share on the spot is a plain expense and needs nothing here.

## Rules

1. **The loan account follows the money, not the person.** Money you hand over that will come back sits in the `assets:loans` tree; money a friend hands you that you will repay sits in `liabilities:loans`, with `friends` as the subaccount for a friend and `colleagues` or `kins` where the prelude says so. Both are declared in `preludes/self.journal`, so a friend with no `<uuid>` account gets a placeholder that the report names and the owner replaces.
2. **The loan convention marks the loan's own entries.** The originating entry carries `!` while the money is outstanding and is flipped to `*` once the settlement exists: `2026-04-01`'s loan still carries `!`, while `2026-01-01` 沙嗲王 and `2026-01-24` 快樂小羊 carry `*` because their repayments are in the journal. The repayment is what decides, not the split: a bill nobody repays carries no marker (TenRen's Tea, Sushiro), a share repaid the same evening is a loan and carries `*` (`2025-11-09`, rule 7), and the settlements cited here carry none — `2025-11-09`'s asserts `= 0.00`. What a marker means on any other kind of entry is `../../instructions/transaction-format.instructions.md`'s.
3. **The settlement brings the loan to zero.** The loan posting takes the positive amount with `= 0.00 <CUR>` on it and the account that paid takes the negative one, as the `2026-01-27` repayment of 快樂小羊's advance does; the originating entry then flips to `*`.
4. **Shape (a), a split you paid for.** Expenses stay whole, one `equity:friends:<uuid>` posting carries the friend's share, and the payment posting carries only what you actually paid: `2026-01-26` TenRen's Tea books the drink whole, the payment for your own part, and the friend's share on equity.
5. **Shape (b), a split someone else paid for.** No payment posting appears at all: the expenses stay whole, every account whose portion the others covered takes a negative offset, and your own share is the one `equity:friends:<uuid>` posting, as `2026-04-07` Sushiro does across its dining and fee accounts.
6. **Shape (c), an advance you will repay.** The advanced amount lands on `liabilities:loans:friends:<uuid>` with its assertion instead of `equity:friends`: `2026-01-01` 沙嗲王 puts the whole bill there and writes no `equity:friends` line, while `2026-01-24` 快樂小羊 writes positive `equity:friends` lines for two co-diners beside a liability for the friend's advance. Those two disagree about where co-diners' shares belong, so this rule states only what both support — the advance sits on the liability with an assertion — and a source where co-diners' shares and a friend's advance meet goes to the owner.
7. **A repayment entry, not the direction, tells a split from a loan.** Both directions of a split use `equity:friends`; what selects the loan accounts is a debt cleared by its own transfer. `2025-11-09` Saizeriya books a friend's share on `assets:loans:friends:<uuid>` with a `*` and a repayment later that evening, while TenRen's Tea books its friend's share on `equity:friends` with neither. A source that does not say whether the money comes back goes to the owner.
8. **The payee is what the entry is about.** A bill keeps the venue's payee; a lending or repayment entry takes the counterparty's `<uuid>` with `activity: lending` or `activity: repayment`, as `2026-04-01` and `2026-01-27` do. `activity: repayment` is wider than loans — it also settles credit-card bills and collects loans you made — so the tag alone never implies a friend.
9. **Interest is its own posting.** A charge for the loan itself never joins the principal, so the loan account still clears to zero on the amount actually lent or advanced; which account carries the interest is `../../instructions/account-hierarchy.instructions.md`'s.
10. **Shares are printed or agreed, never averaged.** An amount, a share, or a direction the source does not give is a question rather than a rounding.

## Procedure

1. Read the source and name the counterparty, the amount, the direction, and whether a repayment is expected.
2. Resolve the counterparty's account and payee, routing an unknown one through `../ingest-payee/SKILL.md`.
3. Choose the shape: a plain expense, (a), (b), (c), or a settlement of an earlier loan.
4. Write the block in the ledger's posting order with the marker rule 2 allows.
5. For a settlement, zero the loan account with its assertion and flip the originating entry to `*`.
6. Hand the block to `../ingest/SKILL.md` for the action decision; the check loop is `../fix-journals/SKILL.md`; the bank of worked blocks is `../ingest/examples.md`.

## Worked example

```hledger
2025-03-04 * Example Restaurant  ; activity: eating, eating: dinner, time: 19:30, timezone: UTC+08:00
    expenses:food and drinks:dining       120.00 HKD
    expenses:food and drinks:fees          12.00 HKD
    liabilities:loans:friends:<uuid>     -132.00 HKD = -132.00 HKD  ; advanced by friend

2025-03-06 (0000000000) <uuid>  ; activity: repayment, time: 09:15, timezone: UTC+08:00
    liabilities:loans:friends:<uuid>          132.00 HKD = 0.00 HKD
    assets:banks:<bank-uuid>:HKD savings     -132.00 HKD
```

## Stop and ask

- A friend with no declared account or `<uuid>`.
- A source that does not say whether the money comes back, leaving (a) and (c) both open.
- A bill where co-diners' shares and a friend's advance meet, which rule 6 cannot settle.
- A share that does not divide evenly, or a total that does not equal the printed lines.
- A repayment that does not equal the outstanding balance or would leave a residue on the loan.
