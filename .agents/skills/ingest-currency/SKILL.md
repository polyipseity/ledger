---
name: ingest-currency
description: Rules for transcribing a currency or points conversion into hledger — the conversion equity pair, the printed rate, and the fee that stays out of it.
---

# ingest-currency

This aspect decides what an exchange contributes: the pair of postings that carry both commodities, the rate the source prints, and the postings around them. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; `../../instructions/transaction-format.instructions.md` owns the syntax, `../ingest-tags/SKILL.md` the tags, and `../fix-journals/SKILL.md` the check loop.

## When to use

A source that exchanges one commodity for another: a bank or card foreign-exchange notice, a platform payout settled in a second currency, a points redemption, or a statement row whose two amounts sit in different commodities. A purchase made abroad that is simply charged in another commodity is an expense in that commodity and needs nothing here.

## Rules

1. **Every conversion is one pair.** Both commodities, equal and opposite, on `equity:conversions:<PAIR>`, inside the transaction that moved the money — a payout, a redemption, an exchange — rather than in an entry of its own, as the `2026-01-19` payout and the `2026-04-13` redemption carry theirs.
2. **The pair name is a declared account.** `<PAIR>` is the two commodities in the order `preludes/self.journal` declares them (`HKD-USD`, `EUR-HKD`, `HKD-KRW`, `HKD-_PT/B`, `HKD-_PT/D`, `_PT/E-_PT/F`); a pair with no `account` line stops the entry.
3. **The legs cancel, and neither is asserted.** They are equal and opposite in their own commodity, so the pair nets to zero and `bun run check:journal` is the proof; no balance assertion goes on a conversion posting, because the pair account accumulates across months — `2026-01` opens with a non-zero USD balance on it.
4. **`rate:` is copied, not computed.** Write the rate the source prints on the conversion posting it prices; never divide two rounded amounts into a rate the source never gave, and never rescale one — the `HKD-USD` entries carry HKD per USD while the `_PT/E-_PT/F` entry carries `_PT/F` per `_PT/E`, each as its source printed it.
5. **A conversion is not an expense.** Nothing about the exchange itself lands in `expenses:*`; the postings beside the pair are the account that gave up one commodity and the one that took the other.
6. **A fee is its own posting.** A commission or spread charged beside the exchange goes on the payment-fee account — `expenses:fees:Stripe` and `expenses:fees:Buy Me a Coffee` in the `2026-01-19` payout — never folded into a leg, which would corrupt the rate.
7. **Points convert the same way.** A points-for-currency or point-to-point conversion takes the same pair, with `rate: 1` where the source converts one for one (`2026-04-13` turns `_PT/D` into HKD that way), and each points commodity stays in the account that holds it.
8. **No status marker on a conversion.** A conversion is a completed movement, and a marker belongs to an unsettled loan (`../ingest-lending/SKILL.md`).

## Procedure

1. Read the source for both amounts, both commodities, the printed rate, and any fee.
2. Match the pair to a declared `equity:conversions` account.
3. Write the legs equal and opposite, with the rate on the leg the source prices.
4. Add the fee posting, then the accounts the money moved between, and set the activity to `transfer`, since value moves between your own holdings.
5. Hand the block to `../ingest/SKILL.md` for the action decision; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 Example Exchange  ; activity: transfer, time: 10:15, timezone: UTC+08:00
    assets:cash                               100.00 USD
    equity:conversions:HKD-USD:USD           -100.00 USD  ; rate: 7.78000
    equity:conversions:HKD-USD:HKD            778.00 HKD
    expenses:fees:banking                       5.00 HKD
    assets:banks:<bank-uuid>:HKD savings     -783.00 HKD
```

## Stop and ask

- A pair with no declared `equity:conversions` account.
- A source that prints no rate, or a rate that contradicts its own amounts.
- A fee the source does not print separately, so the rate and the charge cannot be told apart.
- Two amounts of which only the converted total is legible.
