---
name: ingest-food
description: Rules for transcribing a food or drink receipt into hledger — printed itemization, modifiers, fees, vouchers, meal durations, and shared bills.
---

# ingest-food

This aspect decides what a food or drink source contributes line by line: which printed items become postings, how modifiers and discounts attach to them, and what timing metadata the entry carries. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; journal syntax and posting shape are `../../instructions/transaction-format.instructions.md`'s, and placement is `../../instructions/editing-guidelines.instructions.md`'s.

## When to use

A restaurant, cafe, canteen, takeaway, bakery, supermarket, or app order whose source prints drink or dish lines, modifiers, a service charge, or a voucher, with the postings landing in `expenses:food and drinks:*`. A source that prints only a total has nothing to itemize here: carry the total to `../ingest/SKILL.md` unchanged and say so in the report.

## Rules

1. **The print is the itemization.** Each printed item line becomes its own posting and its own `food_or_drink:` tag, in printed order; never collapse printed lines into a subtotal, and never stand a placeholder in for items.
2. **Zero-priced means zero-priced on paper.** A bundled component gets a `0.00` posting only when the receipt prints it, and a zero-priced drink prints as `expenses:food and drinks:drinks`. A drink the receipt does not print is not added, and a `$0` line that only names the service (`堂食`, `外賣`, `自取`) is dropped.
3. **Fees stay separate.** A service charge, delivery fee, or tip is its own `expenses:food and drinks:fees` posting carrying its printed description, never folded into an item.
4. **Modifiers attach; items do not.** Preparation adjustments join their base item inside one tag through the `+` separator (`奶茶 + 多奶`), and a modifier never stands alone. Two full-priced dishes never join with `+`; separate tags on one line are separated by commas.
5. **Strip metadata, keep the name.** Drop ordering and service markers (`配`, `堂食`, `外賣`, `自取`, the set marker `餐`, `(早)`/`(午)`/`(晚)`, a stray leading `+`); every remaining printed character is the item name, item code included (`091421 LA BOULANGERIE BREAD`).
6. **Split what the print separates.** A `・` between names, a receipt sub-item prefix (`--`, `+`), and a `配` connector that joins two named dishes each yield separate items rather than one joined name.
7. **Quote and comma hygiene.** Write a `"` inside a tag value directly, never escaped; replace a comma inside one value with `;`; write a quantity as `×` plus a digit (`火腿 ×2`).
8. **No reading, no name.** An item you cannot read becomes `food_or_drink: (unknown)`, one per printed item, and no invented name ever replaces printed text.
9. **A voucher is a negative expense.** A printed coupon, cash-card, or points-redemption line gets its own negative `expenses:food and drinks:dining` posting whose tag carries the printed label verbatim, with the payment posting left to cover the remainder.
10. **Order time to settlement time.** `time:` is the printed order or print time, and `duration:` spans order to settlement when both are printed, at second precision (`PT36M52S`). Omit `duration:` below `PT2M`: a meal's dwell time is not a duration.
11. **Split the bill at the table.** Each non-paying participant gets one `equity:friends:<uuid>` posting for their share and a matching negative expense posting; a friend who paid leaves `liabilities:loans:friends:<uuid>` for what you owe, settled through `../ingest-lending/SKILL.md`.
12. **The printed language wins.** Keep each name in the language it was printed in, with `../ingest/food_translations.yml` supplying an approved replacement. Nothing else is translated.

## Procedure

1. Read the source in full and list every printed line with its amount, plus every printed time, identifier, and the tender that paid.
2. Resolve the payee through `../ingest/payee_mappings.yml` and order the printed identifiers by `../ingest/id_mappings.yml`.
3. Turn the printed lines into postings in printed order, applying rules 1–8.
4. Add the fee postings, then the printed voucher line, then any split.
5. Close the block with the payment posting for what was actually paid.
6. Derive `time:` and `duration:` from the printed timestamps.
7. Hand the block to `../ingest/SKILL.md` for the action decision; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 (000-000000, 1A) Example Noodle House  ; activity: eating, duration: PT25M10S, eating: lunch, time: 12:30:00, timezone: UTC+08:00
    expenses:food and drinks:dining                     40.00 HKD  ; food_or_drink: 招牌湯麵
    expenses:food and drinks:dining                      0.00 HKD  ; food_or_drink: 熱奶茶 + 多奶
    expenses:food and drinks:fees                        4.00 HKD  ; food_or_drink: 10% service charge
    expenses:food and drinks:dining                    -20.00 HKD  ; food_or_drink: [電子現金券] $20 午餐券
    equity:friends:<uuid>                              -12.00 HKD
    assets:digital:Octopus cards:<uuid>                -12.00 HKD
```

## Stop and ask

- An item name or a price you cannot read, or a total that does not equal the printed lines.
- A shared bill whose payer or split is unstated, or whose shares do not divide evenly.
- A voucher or discount line that matches no printed amount.
- Two printed timestamps when it is unclear which one the meal started at, since `duration:` depends on it.
- A name with no approved `../ingest/food_translations.yml` mapping once the owner wants English.
