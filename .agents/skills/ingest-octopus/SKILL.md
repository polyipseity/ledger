---
name: ingest-octopus
description: Rules for transcribing Octopus card rows into hledger — the mandatory payee mapping, the reload pair and its references, and updating an entry without rewriting it.
---

# ingest-octopus

This aspect decides what one row of the card's own history contributes: the payee its printed merchant name resolves to, whether the row is a purchase or a reload, and which of an existing entry's fields the row may change. `ingest` owns intake, the add/update/no-op decision, and the validation gate; `../ingest-statement/SKILL.md` owns the match order a purchase row follows, `../ingest-import/SKILL.md` the parse of the source, `../ingest-transport/SKILL.md` a fare's reward pair, `../ingest-food/SKILL.md` a receipt's printed lines, and `../ingest-tags/SKILL.md` the tags; `../../instructions/transaction-format.instructions.md` owns the syntax and `../fix-journals/SKILL.md` the check loop.

## When to use

An app history, the card's own statement, a screenshot, or an emailed receipt for a purchase, a fare, a shop top-up, or a reload funded from the wallet. A bank alert about the wallet itself is `../ingest-statement/SKILL.md`'s and supplies the reload's credit; this aspect owns what the card side becomes.

## Rules

1. **No mapping, no entry.** Every printed merchant name resolves through `../ingest/payee_mappings.yml` before anything is written, and `../ingest-payee/SKILL.md` owns that rule: an unmatched name stops the entry until the owner names its target, and only then does the alias join the table, and only onto a payee the preludes already declare.
2. **One name can hold several payees.** A mapping's value is a list, and one alias in the file lists two targets. The row's amount, its meal or category, its venue, and its timestamp are what select between them — a 60.00 HKD lunch settles on the restaurant target rather than the bakery one — and nothing in the row means asking.
3. **A reload prints a name that maps to `self`.** The transfer names in the file resolve to the `self` payee, so a reload needs no special payee rule — and it never takes a merchant's: every card-to-wallet leg in `ledger/**` carries `self`, none a merchant payee.
4. **A reload is two legs of one movement.** A credit pushes money into the wallet and the wallet funds the card, so the pair is booked together when both sources exist. A card leg whose wallet already held the balance stands alone, so a card leg with no credit on its date is read as that case rather than as a missing row, and a leg with no wallet balance behind it is a question for the owner.
5. **A reload is matched by its own legs, never by a window.** The credit is the leg that carries the references and the card leg carries none, so the pair is found from the credit's own references, its exact date, and the card leg within a minute on either side — the two legs sit seconds apart, and a card leg that precedes its credit by under a minute is ordinary — and no reload has a second credit within two minutes. The amount usually agrees; where it does not, the wallet carried a balance and the card leg is one part of a larger push. Neither a widened purchase window nor the statement's day-wide fallback reaches a reload, and a second run of the same history finds the pair and adds nothing.
6. **The reload leg takes the `duration:`.** It equals the gap between the credit and the card leg — the reloads in `ledger/**` that carry one equal it exactly — and it sits on the card leg, never on the credit, which carries none. Because it measures that gap, a later edit to either leg's `time:` leaves it stale: both legs move together, so a credit that takes the statement's seconds carries the reload leg's `duration:` along in the same change. A reload's gap is under a minute, so the meal floor that omits short durations is not this tag's rule.
7. **An existing entry is updated, never rewritten.** When a row adds only a `duration:`, add it and change nothing else; where it sits in the comment is the formatter's, and `../ingest-tags/SKILL.md` gives the order. A `duration:` that already exists is left alone even when the row suggests another value.
8. **Seconds replace a coarser time.** The app prints `HH:MM:SS` where the entry may hold `HH:MM`, so the finer time is written. A change that moves a minute, an hour, or a date is reported and confirmed first, as `../ingest-statement/SKILL.md` requires.
9. **Update first, then add, in one run.** These are two actions rather than two sittings: every row is checked against the journal before any new entry is written, and a row that ends in an add is no evidence that the update action found nothing.
10. **A row does not choose its own keys.** A fare's reward pair is `../ingest-transport/SKILL.md`'s, a receipt's itemization `../ingest-food/SKILL.md`'s, and the keys `../ingest-tags/SKILL.md`'s.
11. **A reload leg carries no status marker**, and none in `ledger/**` carries one.
12. **An aggregate the shop charged for several payers is a question.** A row whose total matches no single posting, or matches several people's shares, is not split or applied to one of them by this aspect.

## Procedure

1. Read the source and take the merchant name as printed, the signed amount, the printed date and time, and any reference.
2. Resolve the payee through the mapping, and stop on a missing or undecided one.
3. Decide purchase or reload: a transfer name, or a wallet-to-card movement, makes it a reload.
4. Match and update a purchase through `../ingest-statement/SKILL.md`'s order, then hand the block to `../ingest/SKILL.md` for the action decision; the bank of worked blocks is `../ingest/examples.md`.
5. Find the credit a reload shares, then update or book both legs by rules 4–6.
6. Write the `duration:` and the finer time only on the fields the row actually adds.
7. Report every row as updated, added, unchanged, or stopped, and run the check loop through `../fix-journals/SKILL.md`.

## Worked example

The app printed the transfer name at 11:49:18 and the bank alert carried the credit at 11:49:13, so one movement becomes two legs: the references stay on the credit, the gap becomes the reload's `duration:`.

```hledger
2025-03-04 (C0000000000, FRN20250304PAYD0100000000) self  ; activity: transfer, time: 11:49:13, timezone: UTC+08:00, via: eDDA
    assets:digital:Octopus:<uuid>          200.00 HKD
    assets:banks:<bank-uuid>:HKD savings  -200.00 HKD

2025-03-04 self  ; activity: reload, duration: PT5S, time: 11:49:18, timezone: UTC+08:00
    assets:digital:Octopus cards:<uuid>   200.00 HKD
    assets:digital:Octopus:<uuid>        -200.00 HKD
```

## Stop and ask

- A merchant name missing from the mapping, or listing several targets the row cannot separate.
- A reload whose credit cannot be identified: no reference, no bank alert, or more than one candidate within the minute.
- A row whose amount matches an entry while its name points elsewhere, since one of the two is wrong.
- A card leg with no credit and no wallet balance behind it.
- A charged total that matches no single posting, or matches several payers' shares.
