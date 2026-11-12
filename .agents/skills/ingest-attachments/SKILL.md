---
name: ingest-attachments
description: Rules for transcribing a scan, photo, or PDF into a journal entry — printed text only, identifiers bounded by the mappings, and what an uncertain read must never become.
---

# ingest-attachments

This aspect decides what may be taken out of an image or a PDF and what may not: the printed text, never a value inferred from the layout, a logo, or memory, and never a string that identifies an account. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; `../ingest-tags/SKILL.md` owns the metadata the transcribed entry carries; `../ingest-payee/SKILL.md` owns resolving the name printed on the page.

## When to use

A photographed receipt, a wallet or banking-app screenshot, a statement exported as a PDF, an e-ticket, an invoice, or the OCR text produced from one. The originals belong under `sources/`, which git ignores, and their transcriptions under `sources/output/`.

## Rules

1. **Only what the page prints.** Transcribe the payee text, the date, the time, the amounts, the item names, and the printed identifiers; a value you cannot point at on the page — an item, a price, a time — is not transcribed, and a plausible guess is the same defect as an invented one.
2. **The ledger keeps the transcription, not the image.** No attachment, page rendering, or OCR text is copied into `ledger/**` or anywhere else tracked; the scan stays where it was read, and only its text reaches the journal.
3. **Identifiers come from the mapping.** Record the printed keys that `../ingest/id_mappings.yml` names for that payee, in its order. One it excludes — a bank account identifier, a constant debtor-reference token — and any bare card, wallet, or account number on the page stay out of the journal, the filename, and the report.
4. **The filename is not an identifier.** A scan name never stands in for a receipt, order, or transaction id, and never becomes part of an account.
5. **A page can hold several receipts, and an entry several pages.** Match each receipt on the page to its own entry, and pair the pages of one long receipt as a single entry.
6. **An unreadable field goes to the owner, not to a fabricated value.** Where the merchant, the amount, or the tender cannot be read, the entry is pending (`!`) with `0.00` or the amount that is known, and its header carries the scan name as a bare note so the pair can be found again; then ask.
7. **Two readings are reported, not chosen.** A character that could be read two ways, and whose reading would change an amount, a date, or a payee, is quoted both ways in the report.
8. **Nothing is dropped silently.** Every attachment either produces an entry or is named in the report as unprocessed.

## Procedure

1. Read every page and list the receipts it holds, with the text each one prints.
2. Transcribe the printed fields of each receipt: payee, date, time, amounts, item names, identifiers, tender.
3. Resolve the payee (`../ingest-payee/SKILL.md`) and the printed key set (`../ingest/id_mappings.yml`).
4. Build each entry, leaving the metadata to `../ingest-tags/SKILL.md` and the itemization to the aspect that owns the accounts involved.
5. Flag every page you could not read, quoting both readings.
6. Hand the entries to `../ingest/SKILL.md` and the unprocessed attachments to the report; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 ! unknown  ; scan 0000.pdf, activity: consumption, time: 12:00, timezone: UTC+08:00
    equity:unknown                             0.00 HKD
    assets:digital:Octopus cards:<uuid>        0.00 HKD
```

## Stop and ask

- A field that decides money — an amount, a date, or a payee — is illegible, or two readings disagree in a digit.
- The page shows a card, wallet, or account number that no mapping covers; name the kind of number, never the number.
- An attachment produces no entry, or an entry rests on a page that is missing.
- A receipt and its scan disagree on the payee, the date, or the total.
