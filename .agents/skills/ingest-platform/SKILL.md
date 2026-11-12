---
name: ingest-platform
description: Rules for transcribing a platform sale and its payout into hledger — the gross revenue, the platform fee, the net balance, and the transfer that empties it.
---

# ingest-platform

This aspect decides what a digital-platform source contributes: how a sale divides into revenue, fee, and balance, what a payout moves, and which of the platform's identifiers reach the payee line. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; `../../instructions/transaction-format.instructions.md` owns syntax, `../../instructions/account-hierarchy.instructions.md` the accounts, `../ingest-tags/SKILL.md` the tags, and `../fix-journals/SKILL.md` the check loop. A sale settled in a second commodity is `../ingest-currency/SKILL.md`'s.

## When to use

A notice, export, or API record from a payment platform — Stripe, PayPal, Square, a donation platform, an app store — that reports a sale, a donation, a fee, a refund, or a payout to your bank. A card purchase made through a platform's own checkout is an ordinary expense and needs nothing here.

## Rules

1. **A sale is three amounts.** The gross sits on the revenue account in the commodity the counterparty paid, the platform's own fee sits on its fee account, and only the net reaches the platform asset; the gross is never posted as received, and a fee never nets into revenue.
2. **A payout is a transfer.** Equal and opposite amounts on the platform asset and the bank, with revenue untouched, because the money earned its revenue at the sale.
3. **The payout asserts the balance it leaves.** The platform posting carries `= 0.00 <CUR>` when the payout empties the account and the remaining balance when it does not; a zero written to tidy a line fails the check.
4. **The sale's payee is the counterparty, the payout's is the platform.** A sale names the donor or buyer, masked to one `*` per hidden character with only an address's `@`, dot, and TLD left legible; a payout names the platform itself, never the transaction type.
5. **Identifiers keep the mapped order.** `../ingest/id_mappings.yml` orders each platform's identifiers; a bank-account identifier and a payout trace code never appear, and an identifier the source omits shortens the list rather than being invented.
6. **A refund reverses; it never expenses.** Money returned to a counterparty takes the platform asset down and puts the revenue back with a positive revenue posting, undoing the sale it reverses.
7. **Only a settled movement is booked.** A pending, authorised, failed, or reversed row is not a posting, and a platform balance the platform's own statement does not show is never booked.
8. **A sale carries `*`; a payout carries no marker**, as every sale and payout in `ledger/**` does.
9. **The event's clock, not the document's.** A document's generation stamp, an export's run time, and the day a file was downloaded are none of them the sale's or the payout's own date and time.

## Procedure

1. Read the source for the counterparty, the gross, each fee, the net, the currency, the event's timestamp, and the payout a sale settled in.
2. Mask the counterparty, resolve its payee through `../ingest/payee_mappings.yml`, and hand a record with no mapped payee to `../ingest-payee/SKILL.md`.
3. Select the platform asset and the fee accounts; a fee with no account is a question rather than a new account.
4. Write the sale or the payout with the identifiers in mapped order, applying rules 1–9.
5. Hand the block to `../ingest/SKILL.md` for the action decision; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 * (0000000000, pi_000000000000000000000000) ********@*******.com  ; activity: donation, time: 10:12:03, timezone: UTC+08:00
    revenues:donations:Buy Me a Coffee:<uuid>       -5.00 USD
    equity:conversions:HKD-USD:USD                   5.00 USD  ; rate: 7.80000
    equity:conversions:HKD-USD:HKD                 -39.00 HKD
    expenses:fees:Buy Me a Coffee                    1.00 HKD
    expenses:fees:Stripe                             2.00 HKD
    assets:digital:Stripe:<uuid>                    36.00 HKD

2025-03-06 (FRN20250306PAYC0100000000000, po_000000000000000000000000) Stripe  ; activity: payout, time: 15:10:10, timezone: UTC+08:00
    assets:banks:<bank-uuid>:HKD savings       36.00 HKD
    assets:digital:Stripe:<uuid>              -36.00 HKD = 0.00 HKD
```

## Stop and ask

- A fee, tax, or adjustment with no declared account.
- A payout that does not equal what the sales left on the platform.
- A counterparty whose mask would still identify it, or a platform with no prelude `payee` line.
- A refund, a chargeback, or a negative payout: `ledger/**` holds none yet, so nothing here says how one is shaped.
- A currency or rate the source does not print, leaving the gross and the net incomparable.
