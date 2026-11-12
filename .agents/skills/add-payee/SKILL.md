---
name: add-payee
description: Register a new payee, merchant, person, organization, or confidential UUID in the correct preludes journal file, keeping strict lexicographical order. Use whenever a transaction names a payee that is not declared yet.
---

# add-payee

This skill adds one `payee` declaration to a prelude file. What a journal's payee line says — which declared payee a printed name resolves to, when that payee is a UUID, and how the identifiers ahead of it are ordered — is `../ingest-payee/SKILL.md`'s, and confidentiality is `../../instructions/security.instructions.md`'s.

## When to use

- A transaction names a payee that no prelude declares, which `bun run check:journal` reports as an undeclared payee.
- A row in `../ingest/payee_mappings.yml` names a canonical payee that is missing from the preludes.
- A person, institution, or account appears for the first time, and its name or UUID has to be declared before the entry carrying it can be written.

## Rules

1. **A `payee` line lives in a prelude, never in a journal.** `preludes/self.journal` takes the main stream's merchants, people, institutions, and UUIDs, and `preludes/self.alternatives.journal` an alternatives-only payee. The three prelude files declare every payee between them, and no journal under `ledger/**` declares one.
2. **`preludes/index.journal` gains none of them.** Its six declarations are the structural names that generated blocks and transfers carry — `opening balances`, `closing balances`, `self`, `unknown`, `adjustment`, `depreciation`.
3. **Insert at the name's own byte-lexicographic place.** The declarations form one alphabetical block, so the new line goes between the two it sorts between; digits and `*`-masked names sort by those characters, and a UUID by its first hex digit rather than beside the person it names.
4. **Add one line; ordering that is already broken is not this change's.** The insertion goes into its sorted position, `../../instructions/editing-guidelines.instructions.md` owns the ordering convention, and no neighbour is re-sorted to meet it. An inversion you notice is reported rather than repaired inside an unrelated edit, because restoring existing order is a change of its own. Nothing is reflowed, and no existing line is deleted or renamed as part of adding one.
5. **One line per canonical name.** A second spelling of one merchant passes the check and splits every report that groups by payee; a printed variant reaches the declared name through an alias row in `../ingest/payee_mappings.yml`, never through a second declaration.
6. **A confidential name is declared as its UUID.** The name never enters a prelude: the pair stays in `private.yaml`, the `payee` line carries the UUID alone, and the change is re-encrypted as `../../instructions/security.instructions.md` sets out.

## Procedure

1. Read the block and find the name's neighbours: `rg -n '^payee ' preludes/self.journal`, or the alternatives prelude when the entry lands there.
2. Insert `payee <name>` between them, touching no other line; `./examples.md` shows the same insertion for a simple name.
3. Run `bun run check:journal`: a compound over the whole ledger that takes no file argument, and the only automated check a prelude edit gets — it fails on a payee no prelude declares, though not on one merely out of order. The formatter covers the monthly journals alone, so it cannot rewrite a prelude and is not run for one.
4. Confirm the line is there exactly once, in place: `rg -n '^payee <name>$' preludes/self.journal`.

## Stop and ask

- The name fits two merchants, or one merchant is written two ways in the sources.
- The name is confidential and `private.yaml` holds no UUID for it.
- The merchant already resolves through `../ingest/payee_mappings.yml` to a declared payee, so what is missing is the alias rather than the declaration.

## Worked example

`payee Example Books` goes between the two declarations it sorts between, and no line around it moves:

```hledger
payee Example Bakery
payee Example Books
payee Example Cafe
payee Example Deli
```
