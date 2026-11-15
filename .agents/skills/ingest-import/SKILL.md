---
name: ingest-import
description: Rules for importing an external source into hledger — locating it, parsing it mechanically, turning each row into a claim, and proving a second run adds nothing.
---

# ingest-import

This aspect decides how an outside source becomes claims the ledger can act on: where the source is, how a row is parsed, what a row must carry before anyone writes to a journal, and how the import shows that repeating it changes nothing. `ingest` owns matching, the add/update/no-op decision, and the validation gate; `../../instructions/transaction-format.instructions.md` owns syntax, `../ingest-tags/SKILL.md` the tags, and `../fix-journals/SKILL.md` the check loop. What a claim becomes is an aspect skill's: `../ingest-food/SKILL.md`, `../ingest-transport/SKILL.md`, `../ingest-lending/SKILL.md`, `../ingest-currency/SKILL.md`, `../ingest-platform/SKILL.md`, `../ingest-octopus/SKILL.md`. The tag vocabulary — including which value a reload or a payout takes — is `../ingest-tags/SKILL.md`'s, so the example's `activity: reload` shows one value the ledger has written rather than a rule.

## When to use

A statement export, a bank alert, a platform report, an app history, or a month of receipts that has to become journal entries in one pass and again the next month. A single receipt handed over by hand needs none of this and goes straight to its aspect skill.

## Rules

1. **Locate the source before reading it.** Name the file, message, or screen, the period it covers, and the account it belongs to; a source whose period or account cannot be stated is not ready to import.
2. **Parsing is mechanical.** Every field comes from the source's own characters — its date, signed amount, commodity, counterparty, and references — never from a similar entry recalled from the journal, and never rounded, retyped, or converted.
3. **A row becomes a claim, not an entry.** A claim carries the source and its row number, the event's date and time, the signed amount and commodity, the counterparty as printed, every reference as printed, and the account the money moved through. Accounts, payees, tags, and postings are an aspect skill's to add.
4. **One row can be two claims.** A row that both funds a balance and applies it — a bank push into a wallet that then reloads a card — carries two timestamps and two movements, and neither is dropped.
5. **A row that will not parse is reported, never dropped.** The report shows the row as the source renders it and says what could not be read; a silently skipped row is a missing transaction.
6. **The journal is the only dedupe authority.** A source's own "new" or "imported" flag, its file name, and its running-balance column are not evidence that an entry exists; only a journal entry is.
7. **A second run adds nothing.** Importing the same source twice leaves every claim resolving to no action; a claim that asks for an action twice means the first pass's entry cannot be identified, which is a defect rather than a row to skip.
8. **Every claim is accounted for.** The import ends with each claim reported as an entry, an update, or a no-op naming the entry it matched; a claim in none of the three is an unfinished import.
9. **A CSV export is read by its header.** The column names decide what each field is, a column the file does not explain is reported rather than guessed, and the running-balance column checks the row above instead of becoming a posting.
10. **An email body is prose.** The amount, the reference, and the event's time are read out of its text, the message's own arrival time is not the event's time, and a token the provider repeats in every message identifies nothing.
11. **An app export is a screen, not a ledger.** A paginated history gives the counterparty, the amount, and the printed time, often no reference at all; take what it prints and let matching work from the date, the amount, and the time.
12. **A bank push is one message and two movements, and no more than claims.** The bank-to-wallet transfer and the wallet-to-card reload carry one amount seconds apart, so this skill's parse yields two claims; whether that pair is booked at all, how each leg is matched, and how close in time a match may be are `../ingest-octopus/SKILL.md`'s, which decides them once for every reload.
13. **The eDDA reference is the FRN, not the debtor token.** A provider's debtor-reference token repeats in every message it sends, so it identifies nothing: the FRN or transfer identifier is the reference to carry, and the debtor token never reaches a journal or `../ingest/id_mappings.yml`. Which carried references a match may combine belongs to `../ingest-octopus/SKILL.md`.

## Procedure

1. Name the source, its kind, its period, and the account it concerns.
2. Extract each row mechanically and turn it into a claim carrying the fields rule 3 lists.
3. Split a row that carries two movements into two claims that keep their shared reference.
4. Report every row that would not parse, as the source renders it.
5. Hand the claims to `../ingest/SKILL.md` in source order, one at a time; the bank of worked blocks is `../ingest/examples.md`.
6. Account for every claim as rule 8 requires, and report how many were entries, updates, and no-ops.
7. Re-read the same source and confirm every claim now resolves to no action.

## Worked example

```hledger
2025-03-04 (C0000000000, FRN20250304PAYD0100000000000) self  ; activity: transfer, time: 11:49:13, timezone: UTC+08:00, via: eDDA
    assets:digital:Octopus:<uuid>             200.00 HKD
    assets:banks:<bank-uuid>:HKD savings     -200.00 HKD

2025-03-04 self  ; activity: reload, duration: PT3S, time: 11:49:16, timezone: UTC+08:00
    assets:digital:Octopus cards:<uuid>      200.00 HKD
    assets:digital:Octopus:<uuid>           -200.00 HKD
```

## Stop and ask

- A row whose date, amount, commodity, or account cannot be read.
- A source whose rows do not sum to the total it prints.
- A row that could be one movement or two, as a push whose second leg is missing.
- A repeat that still asks for an action because the earlier entry cannot be identified.
- A column, a token, or a field the source does not explain.
