---
name: ingest-payee
description: Rules for turning a printed or statement name into the payee a line carries — the mapping table's authority, the UUID mask, and the identifiers before it.
---

# ingest-payee

This aspect decides what a journal's payee line says: which declared payee a printed or statement name resolves to, when that payee is a UUID rather than a name, and how the identifiers ahead of it are ordered. `../ingest/SKILL.md` owns intake and the add/update/no-op decision, `../add-payee/SKILL.md` registering a new `payee` directive and its `private.yaml` entry, `../../instructions/transaction-format.instructions.md` the syntax, and `../fix-journals/SKILL.md` the check loop. Two of the three data files under `../ingest/` are this aspect's — `payee_mappings.yml` and `id_mappings.yml`; `food_translations.yml` is `../ingest-food/SKILL.md`'s.

## When to use

A source prints a merchant, a person, an institution, or a transfer label that no entry has carried before, or prints one the mapping lists without settling. Settle the payee before the block is written: `bun run check:journal` rejects an undeclared payee, and a name that reaches a journal unresolved stays in the file for good.

## Rules

1. **The table decides, and there is one table.** `../ingest/payee_mappings.yml` holds 46 aliases onto 34 distinct payees, every one declared in `preludes/*.journal`. A printed name resolves through it, and an alias does not survive into a journal: six aliases checked across `ledger/**` — `麥當勞`, `大家樂`, `759阿信屋`, `八達通轉賬`, `餐飲 / 會所`, `九巴 / 龍運` — appear in no header, 0 occurrences each.
2. **An unmatched name stops that entry until the owner names its target.** A guess writes nothing: once the owner confirms a target, the alias joins `payee_mappings.yml` in the same change when that target is already declared, and goes through `../add-payee/SKILL.md` when it is not. `../ingest-octopus/SKILL.md` defers to this rule.
3. **A value is a list, and two targets are a question.** One of the 46 aliases lists two (`餐飲 / 會所` → `A-1 Bakery`, `Saizeriya`), so the row's amount, its items, and its venue select between them — the table cannot. Where they do not, the row stops.
4. **An alias equal to its only target is not listed.** 0 of the 46 is an identity, and adding one would hide that the name already resolves.
5. **A confidential merchant becomes its UUID.** `private.yaml` holds the UUID-to-name pairs, and the journal, the report, and the commit message carry the UUID alone, with the name never written beside it. 90 of the preludes' 265 `payee` lines are UUIDs, and 83 distinct UUID payees appear across 1,414 of the ledger's 6,862 headers.
6. **The mapping is looked up, not decrypted.** `private.yaml` is the owner's to open; an unresolved confidential name is a question, and an authorized lookup yields the UUID without the value being echoed anywhere.
7. **Identifier order and shape come from `id_mappings.yml`.** Its 43 entries give each mapped payee a list of acceptable orders plus regex hints, and identifiers sit in parentheses before the payee, never in a tag: 2,133 of the ledger's headers carry such a group. `../ingest-tags/SKILL.md` owns the tags.
8. **A UUID payee that prints identifiers needs its own entry.** The mapping's key is the payee string, so 5 of the 43 entries are keyed by a UUID.
9. **An identifier the mapping expects and the source lacks is written `?`.** The gap stays visible in the payee line instead of shortening the group; one header in `ledger/**` uses it.
10. **A number that identifies the account is not an identifier.** Wallet, card, and bank numbers never enter a payee line or an `id_mappings.yml` key, whatever else `../ingest-statement/SKILL.md` excludes them from; a receipt number and a card number can look alike, and the mapping's regex hints are not licence to record the second.
11. **The table stays sorted and deduplicated, and a new id mapping is the owner's to confirm.** Its 46 aliases ascend by alias, so a new one is inserted at its sorted place rather than appended or grouped under its source; rule 4 forbids an identity alias, rule 2 governs a new one, and an `id_mappings.yml` entry is written only once the owner confirms its order and shape.
12. **The payee is written exactly as declared.** No branch, region, or terminal code is appended to it, and a name the declaration already carries is not stripped of it.

## Procedure

1. Take the name as printed, with the row's amount, items, venue, and any identifier.
2. Decide which authority answers: `private.yaml` for a confidential name, `payee_mappings.yml` for an alias, a declaration in the preludes for a name already canonical.
3. Resolve a multi-target alias from the row, and stop where the row does not decide.
4. Set the identifiers in the order `id_mappings.yml` gives, `?` for a missing one.
5. Check the payee is declared; anything the table or the preludes lack is rule 2's to settle.
6. Hand the resolved payee line to `../ingest/SKILL.md`, and run the check loop through `../fix-journals/SKILL.md`.

## Worked example

The printed name is a confidential merchant, so the payee is its UUID and the identifier its mapping orders first leads the line.

```hledger
2025-03-04 (00000000) <uuid>  ; activity: eating, eating: lunch, time: 12:30:56, timezone: UTC+08:00
    expenses:food and drinks:dining           35.00 HKD
    assets:digital:Octopus cards:<uuid>      -35.00 HKD
```

## Stop and ask

- A printed name that no alias, no `private.yaml` pair, and no prelude declaration covers.
- An alias listing several targets that the row's amount, items, and venue do not separate.
- An identifier whose order or shape no `id_mappings.yml` entry gives.
- A name that could be personal, and so belongs behind a UUID, against one that could be a trading name.
- A mapping whose resolution would need `private.yaml` decrypted without the owner's say-so.
