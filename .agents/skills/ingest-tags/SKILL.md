---
name: ingest-tags
description: Rules for the metadata tags on an hledger entry — which comment keys its activity requires, the order formatting leaves them in, and the prelude line that makes a key legal.
---

# ingest-tags

This aspect decides the metadata a transaction carries: the comment keys its activity requires, the order they survive formatting in, and whether a key or a value may be used at all. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; `../../instructions/transaction-format.instructions.md` owns the key vocabulary and the surrounding syntax; `../../instructions/editing-guidelines.instructions.md` owns placement and declaration order; `../fix-journals/SKILL.md` owns the check loop. Meal timing is `../ingest-food/SKILL.md`'s and the reward postings of a fare are `../ingest-transport/SKILL.md`'s.

## When to use

Every transaction written into `ledger/**`, whatever the source — a receipt, a statement row, an app history, an email, a conversion. Settle the keys before handing the block to `../ingest/SKILL.md`: an undeclared or missing key reports itself only afterwards, as a failed `bun run check:journal`.

## Rules

1. **A key lives in a comment, on the line it describes.** The header's comment opens two spaces after the payee with `;`, a posting's two spaces after its amount, and several keys on one line are separated by a comma followed by a space. A part with no colon is a bare note: it holds no key and needs no declaration.
2. **Write the keys already sorted.** The formatter sorts each unbroken run of neighbouring keys alphabetically and leaves a bare note where it stood, so `activity` opens a run and `timezone` closes it, and a note — a scan name, an identifier lifted from the source — goes first: `activity: eating, duration: PT20M, time: 12:30, timezone: UTC+08:00`.
3. **`timezone:` records the zone the source printed its moment in.** A home-zone source carries `UTC+08:00`, as 6,814 entries do, and a document from a trip keeps its own hour instead of the home zone's: 43 entries in `ledger/2024/2024-06`, `ledger/2025/2025-07`, and `ledger/2025/2025-09` carry `UTC+09:00`. A printed time is never shifted into another zone.
4. **`activity:` names the event, never the account.** Take a term the ledger already writes — `consumption`, `eating`, `education`, `transport`, `transfer`, `service`, `tutoring`, `repayment` — rather than coining one for the row.
5. **`time:` is the event's own clock.** `HH:MM` where the source prints minutes and `HH:MM:SS` where it prints seconds; a source that gives only a date omits `time:` rather than claiming midnight.
6. **A boundary block trades `activity:` for `clopen:`.** The generated opening and closing blocks carry `clopen:` with an empty value and are never hand-written, so their keys are not yours to set.
7. **Extras follow the activity, not a checklist.** `eating:` names the meal rather than the cuisine; `duration:` appears only where the source bounds both ends of the span; `rate:` only where the transaction converts one commodity into another; `posted:` only where the source's own timestamp differs from the date the entry takes.
8. **The receipt vocabulary stays on postings.** `food_or_drink:`, `item:`, `discount:`, `voucher:`, and `valid:` describe one posting and never reach a header, whereas a header's keys describe the event itself (`activity:`, `time:`, `timezone:`, `via:`, `transfer:`, `clopen:`).
9. **A comma ends the part.** A value that needs one is written with `;` instead, and a `"` inside a value is written directly rather than escaped, because the formatter splits the comment on commas before it sorts the parts.
10. **Every key name is declared before it is used.** The closed list is the `tag` lines of `preludes/index.journal` together with those of the prelude of the stream the entry belongs to — `preludes/self.journal` for the main stream, `preludes/self.alternatives.journal` for the alternatives stream, which alone declares `collect`, `compute`, and `recycle`; `bun run check:journal` fails a name outside it through `hledger check tags`. A needed name that is undeclared stops the entry until the owner adds the `tag` line.
11. **No prelude enumerates values, so borrow them.** Nothing declares the legal `activity:` or `eating:` values; the vocabulary is what `ledger/**` already writes, which makes searching for an existing term part of choosing one.

## Procedure

1. Read the source and name the event, then the activity it belongs to.
2. Add the keys that activity carries, and the moment in the zone the source prints.
3. Move every item, discount, and voucher detail onto the posting it belongs to.
4. Check each key name against the `tag` lines, and each value against a term `ledger/**` already writes.
5. Order the keys as rule 2 leaves them, then write the block.
6. Hand the block to `../ingest/SKILL.md`; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 Example Bookstore  ; activity: consumption, time: 15:20, timezone: UTC+08:00
    expenses:education:books                  80.00 HKD  ; item: textbook
    assets:digital:Octopus cards:<uuid>      -80.00 HKD
```

## Stop and ask

- The activity needs a key name that no prelude declares; the `tag` line is the owner's to add.
- Two activities fit the source equally well, as when a charge could be `service` or `fees` and the keys differ between them.
- The source prints two moments and it is unclear which the event happened at.
- A value would have to be coined because nothing in `ledger/**` covers it.
