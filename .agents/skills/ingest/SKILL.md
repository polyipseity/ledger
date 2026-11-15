---
name: ingest
description: Ingest financial source material (receipt, invoice, email, statement, app history, CSV, screenshot, OCR text) into the hledger ledger as new, updated, unchanged, or (rarely) removed transactions. Use for any request that brings outside data into the journals. Routes to ingest-* aspect skills for transaction-type rules.
---

# ingest

This skill takes one piece of outside material and settles what it becomes in the journal: which entries its claims match, which of four actions each claim takes, and what the run reports. It owns intake, matching, the action decision, the batching rule, and the verification gate. The accounting shape and the decision rules for one class of transaction belong to the twelve aspect skills beside it, reached through the routing table rather than restated here. Journal syntax is `../../instructions/transaction-format.instructions.md`'s, editing rules are `../../instructions/editing-guidelines.instructions.md`'s, and the command surface is `../../../AGENTS.md`'s.

## Inputs and claims

Take these fields off the source before anything is written, and note for each whether the source printed it or left it out: the date; the time and the precision it is printed at; the signed amount and its commodity; the payer or payee exactly as printed; the line items; every printed identifier; and the channel the row came through — the app, statement, alert, email, or page that produced it.

- **One source row is one claim**, and the claim is only what those fields hold. `../ingest-import/SKILL.md` turns an export, an email, or a history into claims; a row carrying two movements is two claims.
- **Transcribe printed characters exactly.** A character you cannot see is not normalised into one you can, a truncated name is not completed, and a field the source omits stays absent and is reported; a plausible guess is the same defect as an invented value.
- **A claim carries no accounting.** Accounts, payees, tags, and postings are an aspect skill's to add, and a status marker is `../../instructions/transaction-format.instructions.md`'s to define.

## Target journal

`ledger/<year>/<year>-<month>/<name>.journal`, and the month is the transaction's own date — the day the money moved, never the day the material was read or handed over. The monthly tree holds two file names, `self.journal` and `self.alternatives.journal`, and every transaction sits in a file named for its own month.

- **The liquid stream is the default.** `self.journal` takes banks, cash, cards, wallets, rewards, and objects; `self.alternatives.journal` takes the illiquid holdings alone, and `../../instructions/alternatives-journal.instructions.md` draws the line.
- **A year file, `ledger/index.journal`, and the preludes take no transaction.** The first two include and the third declares; `../../instructions/architecture.instructions.md` holds the tree and `../../instructions/editing-guidelines.instructions.md` the placement rules.

## Action decision

Four actions, decided per claim, each with the test that selects it:

1. **no action** when an existing entry already encodes every claim the source supplies — the same date, amount, payee, items, identifiers, and timing metadata. Report the matched entry and edit nothing.
2. **update** when a match exists and the source adds or corrects a field: seconds on `time:`, a `duration:`, item lines, a printed identifier, a payee mapping, an amount the source contradicts. Patch the minimum lines and preserve every line the source does not contradict; which fields a match may touch is the matching aspect's to say, and `../ingest-statement/SKILL.md` and `../ingest-octopus/SKILL.md` both state it for their own rows.
3. **add** when no entry in the ledger accounts for the claim.
4. **remove** only for a duplicate, a source the owner has withdrawn, or an entry no source can repair, always through `../ingest-remove/SKILL.md`, whose evidence test and balance sweep run before anything is deleted.

**A contradicting amount is an update.** The entry and the source still describe one claim, so the value is corrected in place; removal is reserved for a claim that should not exist at all, and the matching procedure below is what keeps a different merchant's entry out of that correction.

The run is idempotent by construction: a second pass over the same source reports zero add and zero update rows, and a claim that asks for an action it already took means the first pass's entry cannot be identified, which is a defect rather than a row to skip.

## Matching procedure

1. Take the candidates from the managed binary, scoped to the claim's own day: `node_modules/.bin/hledger print -f ledger/index.journal -O json 'date:<YYYY-MM-DD>'`. When the journal will not parse, fall back to `rg -n -e '<YYYY-MM-DD>' -e '<printed amount>'` over the month's file, and hand the parse failure to `../fix-journals/SKILL.md`.
2. Key the match on the date, the signed amount, and the payee the claim resolves to (`../ingest-payee/SKILL.md`). The amount is the one on the posting the money moved through — the bank, card, wallet, or cash side — never the entry's first or largest posting, because the source's one figure reaches the entry twice, positive on the expense side and negative on the side that paid, so "the entry's amount" names one posting rather than a sum. A candidate that disagrees on the date or the amount is not a candidate, and a claim with no candidate is an **add**; one that agrees on both while the payee disagrees stops the row instead, because one of the two is wrong.
3. Match the time at the tolerance its class allows: the printed minute for transport, and ±90 minutes from the printed time for dining and shopping. A statement row follows the weaker order `../ingest-statement/SKILL.md` sets out, and a reload is never matched by a window at all (`../ingest-octopus/SKILL.md`).
4. Re-read each surviving candidate's header line before acting. No decision rests on a read taken earlier in the run.
5. Pair one entry with one source row and one source row with one entry. A claim that several candidates fit equally stops the batch, and so does a second row reaching an entry another row already claimed — `./owner-notes.md` holds both cases.

## Aspect routing table

| the source or the claim carries | the aspect to read |
| --- | --- |
| food, drink, dining, or a receipt with item lines | `../ingest-food/SKILL.md` |
| a fare, toll, transit payment, or its reward accrual | `../ingest-transport/SKILL.md` |
| a loan, an IOU, a shared bill, or a settlement | `../ingest-lending/SKILL.md` |
| a second commodity, an exchange, or a points redemption | `../ingest-currency/SKILL.md` |
| a platform sale, fee, refund, or payout | `../ingest-platform/SKILL.md` |
| a CSV, an email, an export, or a run that repeats monthly | `../ingest-import/SKILL.md` |
| a bank or wallet statement row | `../ingest-statement/SKILL.md` |
| Octopus card history | `../ingest-octopus/SKILL.md` |
| an unknown merchant name, an alias, or a UUID question | `../ingest-payee/SKILL.md` |
| a tag, a comment key, or a posting's shape | `../ingest-tags/SKILL.md` |
| a photo, PDF, screenshot, or the OCR text taken from one | `../ingest-attachments/SKILL.md` |
| an existing entry to delete | `../ingest-remove/SKILL.md` |

Read this file, then exactly the aspects the route names — a photographed receipt routes twice, `../ingest-attachments/SKILL.md` for the page and `../ingest-food/SKILL.md` for its lines, and a wallet statement row routes twice as well, `../ingest-statement/SKILL.md` for the credit and `../ingest-octopus/SKILL.md` for the card leg — and never all twelve. A rule that holds for one class of transaction belongs in that aspect, not here.

## Batching and delegation

One to three claims are written here directly, one at a time, each settled before the next is read. Four or more are one `ledger-entry-writer` child per claim: each returns a formatted block plus its status, and this session merges the blocks, sorts them into the target journal's chronological order, and runs the single verification pass below. In this mode a child never edits a journal, because the merge and the ordering are what the batch has to get right once.

## Verification gate

`bun run check:journal` over the ledger, then `bun run format:journal`, then `bun run check` once per batch. Never `bun run format` mid-batch, because it reaches files the batch never touched.

- **A check scoped to files takes the module form.** `bun run check:journal` is a compound (`uv run --locked -m scripts.check && uv run --locked -m scripts.format --check`), so an argument handed to the bun name lands on the formatter half while the checker still sweeps the whole ledger. Name the files repository-relative and run the checker itself: `uv run --locked -m scripts.check ledger/<year>/<year>-<month>/self.journal`.
- **A failing check is not the run's to argue with.** `../fix-journals/SKILL.md` classifies it before anything else proceeds. A month's opening and closing blocks are generated rather than edited, and `../migrate/SKILL.md` owns them.

## Report

Every run closes with a table of its source rows — action, date, payee, amount, file — together with the unmatched rows and every question held for the owner. `./owner-notes.md` holds the columns, the unmatched-row rule, the confidentiality rule, and the cases that stop a batch and ask.

## Learn as you go

A merchant, an alias, an identifier shape, or an item translation that the sources have not carried before is settled in the same change that writes the entry: `./payee_mappings.yml` and `./id_mappings.yml` are `../ingest-payee/SKILL.md`'s, `./food_translations.yml` is `../ingest-food/SKILL.md`'s, and a rule that only one class of transaction needs goes into that aspect's Rules section. Never add a lessons file, and never record in prose a rule that a test could assert. An unmatched payee stops the entry until the owner names its target; the alias joins `./payee_mappings.yml` in that same change and the entry proceeds only afterwards.

## Data files

- `./payee_mappings.yml` — each printed name's mapping onto a payee the preludes declare, one target unless the row separates several.
- `./id_mappings.yml` — each mapped payee's identifier order, with regex hints for the shapes it accepts.
- `./food_translations.yml` — item translations, added only with the owner's approval.
- `./examples.md` — the shared bank of worked examples, one per shape the aspects describe; read the case matching the aspect before writing rather than reconstructing it from a finished entry.
- `./owner-notes.md` — the report's columns, the confidentiality rule, and the cases that stop a batch and ask.

Nothing in this directory is named with the `ingest-` prefix, because that prefix names the aspect skill directories beside it and a file wearing one reads as a skill to every reference check.
