---
name: ingest-statement
description: Rules for matching a statement row to an entry that already exists — the match order, the seconds-only silent update, the reload pair, and the rows that stop the batch.
---

# ingest-statement

This aspect decides what a statement, alert, or history row does to a journal that already holds an entry: which entry it matches, which of that entry's fields it may change, and when the row stops the run instead. `../ingest/SKILL.md` owns intake and the decision to write a new entry, and a row that matches nothing is reported to it rather than booked here. `../../instructions/transaction-format.instructions.md` owns the syntax, `../ingest-tags/SKILL.md` the tags, `../ingest-octopus/SKILL.md` the reload pair, and `../fix-journals/SKILL.md` the check loop.

## When to use

A wallet statement, a card statement, a bank alert, or an app history handed over to be reconciled against entries the journal already holds — the month's rows against the month's journal. A row with no entry behind it and no second source to book it from is a gap for `../ingest/SKILL.md` to fill, not something this aspect writes.

## Rules

1. **A row matches or reports; it never writes an entry.** The only fields a match may change are that entry's `time:` and `duration:`; a row that would need an amount, a payee, a posting, or a new transaction leaves the journal alone and goes into the report.
2. **Match in this order and stop at the first hit.** The candidates come from the whole month's journal rather than a snippet of it, and the first hit wins: exact date, exact signed amount, and a detail both sides share — the payee the printed name maps to, or a reference the entry carries; then the signed amount with a reference alone; then the signed amount, the same payee, and a date within a day.
3. **The date-wide fallback is the weakest and never stands alone.** Two reloads of the same amount a day apart are ordinary — `2024-04-14` and `2024-04-15` each move 200.00 HKD — so the fallback is confirmed by the payee, and a reload never uses it at all (`../ingest-octopus/SKILL.md`).
4. **Seconds are silent; anything coarser is confirmed.** A row that adds seconds to an entry holding none, `12:34` to `12:34:56`, is applied without appearing in the report. A change that moves a minute, an hour, or the date is reported with both datetimes before it is written.
5. **The time is read in the zone the statement prints.** A document from abroad keeps its own hour rather than being shifted: 43 entries in `ledger/2024/2024-06`, `ledger/2025/2025-07`, and `ledger/2025/2025-09` carry `UTC+09:00` beside a home zone of `UTC+08:00`. The key's value for a home-zone source is `../ingest-tags/SKILL.md`'s.
6. **A bank credit that funds a wallet is not income.** The credit and the wallet's reload are two legs of one self-to-self transfer, no revenue posting arises — no bank-to-wallet entry in `ledger/**` touches `revenues:*` — and the reload leg is the one that carries the `duration:`. The pair's shape is `../ingest-octopus/SKILL.md`'s.
7. **Both legs move together.** When a credit takes the statement's seconds, the reload leg's own time comes from the wallet's row and its `duration:` stays equal to the gap; updating one leg alone leaves the pair disagreeing about the same movement.
8. **A number that identifies the wallet stays out.** Wallet, card, and bank account numbers reach no journal, file name, report, or `../ingest/id_mappings.yml`. Two entries in `ledger/2024/2024-11` and `ledger/2025/2025-01` carry one in their payee line; that is a defect to raise, never a shape to copy.
9. **An unmatched row is reported with its reason.** The report shows the row as the source renders it — its date, amount, and time — and says whether nothing matched or whether several candidates did.
10. **An ambiguous row stops the batch.** Several survivors that nothing distinguishes, or a row that could belong to two months, end the run at that row: a later row confirmed against a guess inherits the guess.

## Procedure

1. Name the statement, its period, the account it reports on, and the journal stream it reconciles against.
2. Take each row in the statement's own order, with its date, time, signed amount, and printed detail.
3. Resolve the match by rule 2, stopping at the first hit that survives rule 3.
4. Apply the seconds-only update, or report the coarser change and wait for confirmation.
5. Follow a credit to its reload leg by rules 6–7 before moving to the next row.
6. Report every unmatched and ambiguous row with its reason, then hand the entries this aspect cannot place to `../ingest/SKILL.md`.
7. Run the check loop through `../fix-journals/SKILL.md` once the batch is settled.

## Worked example

The entry stood at `time: 12:34`; the statement row printed `12:34:56`, so the seconds are applied and nothing else changes.

```hledger
2025-03-04 (00000000, 00) Example Cafe  ; activity: eating, time: 12:34:56, timezone: UTC+08:00
    expenses:food and drinks:dining       35.00 HKD
    assets:digital:Octopus cards:<uuid>  -35.00 HKD
```

## Stop and ask

- A row with no match, or with several candidates that the amount and the payee do not separate.
- A change that would move a minute, an hour, or a date.
- A credit with no reload leg, or a reload leg with no credit, where the other source is missing.
- A row whose amount disagrees with the entry it otherwise matches, as when the shop split or discounted the charge.
- A document that prints a wallet or card number in full: the row is identified another way, never by recording it.
