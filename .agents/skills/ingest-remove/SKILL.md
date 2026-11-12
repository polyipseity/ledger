---
name: ingest-remove
description: Rules for removing a wrong journal entry — the evidence that justifies it, the balances that depend on it, and the verbatim report that lets the owner restore it.
---

# ingest-remove

Removal is the rare action: an entry exists because a source claimed it, so it goes only when the claim is withdrawn or the entry is wrong outright. `../ingest/SKILL.md` owns the add/update/no-op decision and routes a case here; `../migrate/SKILL.md` owns the boundary blocks, `../fix-journals/SKILL.md` the check loop, and `../../instructions/transaction-format.instructions.md` the syntax.

## When to use

An entry duplicates one already booked, carries an amount the source contradicts, sits in a month the source's date does not support, or rests on a source the owner has withdrawn. A wrong month is a move rather than a deletion: the row is re-entered at its own date in the same change, or the case stops and asks. Nothing weaker qualifies — an entry missing a `duration:`, an item, or an identifier is incomplete, and incompleteness is an update.

## Rules

1. **The owner decides, and the run reports.** The case goes out with its evidence and the run stops at that entry; nothing removes a second entry by inference.
2. **Wrong, not merely thin.** Three conditions above delete — a duplicate, an amount the source contradicts, a withdrawn source — and the wrong-month case belongs to a move. An entry that under-records its source is corrected through `../ingest/SKILL.md`, and one whose document cannot be found stays until the owner says the claim was never made.
3. **Find every dependant before deleting.** The month's closing block, the next month's opening, every later `= balance` assertion naming an account the entry touched, and any shared bill's other half: the ledger holds 357 postings across the `equity:friends*` accounts in 33 files and 228 `liabilities:loans:` postings.
4. **Assertions do not repair themselves.** The closing block's amounts encode the month, so a deletion upstream of one leaves its `= 0.00` contradicted by the computed balance, and `bun run check:journal` fails on it.
5. **A boundary block is never hand-edited.** `scripts/clopen.py` writes the month's opening and closing and tags both `clopen:`; if the entry to remove is one of them, or the closing has to be recomputed, continue in `../migrate/SKILL.md`.
6. **Delete the whole block, never a posting.** Header, comment, and all postings go together: a transaction left with one posting either fails as unbalanced or, when that posting elides its amount, passes while booking a zero nobody claimed.
7. **Then verify the files, and the boundary only when it moved.** Name the touched journals to `uv run --locked -m scripts.check` by repository-relative path (`ledger/2025/2025-03/self.journal`), because it resolves each argument against the working directory rather than the ledger folder, and `bun run check:journal` needs no such care since it hands its arguments to the formatter and checks every journal anyway. When the deletion moved a boundary, `uv run --locked -m scripts.clopen_verify --period <YYYY-MM> --files <name>` scopes the chain to that month and matches the bare file name (`self.journal`) against the period's journals, and only the bare `bun run verify:migration` needs comparing against the run made before the deletion.
8. **Report the block, and compensate nowhere.** The report carries the file, date, payee, and amount verbatim so the owner can restore it; no neighbouring amount is edited to absorb the gap and no assertion is loosened to pass.

## Procedure

1. State the entry, the condition it meets, and the evidence, then wait for the owner.
2. Walk the dependants of rule 3, and route a boundary case to `../migrate/SKILL.md`.
3. Delete the block and nothing else, run the checks of rule 7, then report the block verbatim with their outcome.

## Worked example

One claim reached the journal twice: the first block is the entry the source first produced, and the second is the copy a later run added, so the second is what goes.

```hledger
2025-03-04 Example Cafe  ; activity: eating, time: 12:30:56, timezone: UTC+08:00
    expenses:food and drinks:dining       35.00 HKD
    assets:cash                          -35.00 HKD

2025-03-04 Example Cafe  ; activity: eating, time: 12:30:56, timezone: UTC+08:00
    expenses:food and drinks:dining       35.00 HKD
    assets:cash                          -35.00 HKD
```

## Stop and ask

- The entry looks wrong and no document contradicts it.
- Removing it would move a closing balance or the next opening.
- Another entry carries the same claim, so which of the two is the stray is undecided.
- The claim is one half of a shared bill or a loan whose settlement is still open.
