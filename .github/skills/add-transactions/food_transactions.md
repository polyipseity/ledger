# Food Transactions Theme

This file contains rules, clarifications, and examples specific to food and restaurant transactions. Use this file whenever a transaction involves food, drink, dining, or restaurant-related expenses.

## When to Use

- Any transaction involving food, drink, or dining (including restaurants, cafes, canteens, takeout, etc.)
- Transactions with food/drink itemization, modifiers, or translations

## Key Rules

- Always use canonical payee names (see payee_mappings.yml). All mapping values in `payee_mappings.yml` are YAML sequences (lists). If a list contains multiple canonical candidates, disambiguate using contextual cues (store/branch id, receipt tokens, item categories, locality); prompt for clarification if context is insufficient.
- Normalize food/drink items and modifiers (see below for rules)
- Use `food_or_drink:` tag in posting comments for each item
- Use English translations from food_translations.yml only after user approval
- Split items and modifiers as per the rules below
- Do not invent new tags; only use those declared in the prelude

### Itemization, Modifiers, Item Numbers, and Tagging

- **Always fully itemize all food and drink items.** Never use placeholders like "(see receipt)". Every item and its amount must be listed explicitly, with a separate `food_or_drink:` tag for each.
- **For Taste and similar supermarkets or bakeries, always include the item number or code from the receipt as part of the `food_or_drink:` tag, if available.** For example, `food_or_drink: 091421 LA BOULANGERIE BREAD`.
- Separate distinct food/drink items into separate `food_or_drink:` tags, even if listed together on the receipt (e.g. "麵包, 咖啡" → `food_or_drink: 麵包, food_or_drink: 咖啡`).
- Use `+` syntax only for modifiers (e.g. "hot coffee + more milk" → `food_or_drink: hot coffee + more milk`).
- Remove parenthetical descriptors that are not part of the item name (e.g. "(辣)麥炸雞" → "麥炸雞").
- Remove conjunction prefixes that are not part of the item name (e.g. "配朱古力" → "朱古力").
- The middle dot character `・` separates distinct food items and should result in separate `food_or_drink:` entries.
- Receipt sub-items (marked with `--`, `+`, or similar prefixes) are typically separate items or substitutions, not modifiers.
- Complimentary/zero-cost items (e.g., "set hot coffee $0.0") should be treated as items with modifiers, not as separate line items. Include them using the `+` syntax to show customization.
- Items that cost $0 and describe the transaction type (e.g., "dine-in", "take-away") should be omitted entirely.

### Modifiers vs Items

- Modifiers are preparation adjustments applied to a base item (e.g., "more milk", "less ice"). Use `+` syntax: `food_or_drink: hot coffee + more milk`.
- Items are distinct food components, even if listed as sub-items on the receipt (e.g., "sweet corn", "garlic butter on toast"). List separately: `food_or_drink: item1, food_or_drink: item2`.
- If a sequence of `food_or_drink:` tags is present and the first is a base item (e.g., a drink) and the following are modifiers (e.g., ice level, sweetness, size), combine them into a single tag using the `+` syntax. For example, `food_or_drink: 冰蜜檸檬綠茶, food_or_drink: 去冰, food_or_drink: 7分甜` should become `food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜`.

#### Example: Drink with Modifiers

Original: 冰蜜檸檬綠茶, 去冰, 7分甜

Result: food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜

### Translation

- Store confirmed translation mappings in `food_translations.yml`, keyed by payee with an optional `default` fallback.
- When a mapping exists and the user has approved it, replace the transaction's `food_or_drink` value with the English translation only.
- If no mapping is found, do NOT translate automatically. Prompt the user with options: leave as-is, provide a mapping, or search journals for candidates.
- Only write mappings into `food_translations.yml` after explicit user approval.

### Examples

#### Example: Taste Item Number

Original: 091421 LA BOULANGERIE BREAD

Result: food_or_drink: 091421 LA BOULANGERIE BREAD

#### Example: Full Itemization (No "see receipt")

Original: (see receipt)

Result:
    expenses:food and drinks:dining  48.00 HKD  ; food_or_drink: 白切雞飯
    expenses:food and drinks:dining  48.00 HKD  ; food_or_drink: 豉油雞飯
    ... (repeat for each item)

#### Example: Modifiers and Zero-Cost Items

```text
Original:
 義大利粉番茄肉醬套餐
 - 七味蛋
 Set Hot Coffee (complimentary)
  - Extra milk
 Dine-in $0
```

Result: food_or_drink: Spaghetti Bolognese with Fried Egg in Assorted Chilli Pepper, food_or_drink: set hot coffee + extra milk

#### Example: Distinct Items

Original: 鮮奶炒滑蛋・吉列魚柳
Sub-items: -- 粒粒粟米; 轉 蒜香牛油多士

Result: food_or_drink: scrambled egg, food_or_drink: sweet corn, food_or_drink: cutlet fish fillet, food_or_drink: garlic butter on toast

#### Example: True Modifiers

Original: 熱咖啡
Modification: 多奶

Result: food_or_drink: hot coffee + more milk

### Unknown or Unreadable Items

- If an item on the receipt is missing, illegible, or OCR failed to reliably capture it, record a placeholder tag `food_or_drink: (unknown)`. Use this only when the transaction clearly represents a food/drink purchase but the specific item(s) cannot be determined from the source.
- When multiple items are clearly present but one or more are unreadable, add one `(unknown)` tag per unreadable item when quantity is obvious; otherwise add a single `(unknown)` tag for the posting and note to confirm later if necessary.
- Prefer to confirm with the user or the receipt source before guessing item names. Do not invent item names for unclear text.

### Clarification Patterns (Food/Drink)

- Shared meal: Ask if split equally, covering all, or expecting reimbursement. Use `assets:loans` and pending status if reimbursement expected.
- Multi-category receipt: Ask if items are purchased together or separately. When the receipt shows per-item prices, record each item as its own posting line with the item's amount and a `food_or_drink:` comment tag. Ensure the item postings sum exactly to the transaction total and place the payment posting (e.g., the `assets:digital:Octopus cards:...` line) as the final posting for the full negative total. Maintain the order of postings to match the receipt.
- Payee/IDs/item code normalization: Prefer canonical payee names, clarify ambiguous names, and use UUIDs for confidentiality if mapped. **Always check `private.yaml` for a UUID mapping and use the UUID as the payee if present.**
- Timezone: All transactions that include a time must also include an explicit `timezone:` (e.g., `timezone: UTC+08:00`). This helps compute durations reliably and keeps entries consistent across journals.
- Duration calculation: If both start and end times are present (for example, an order/printed time and a settlement/transaction time displayed on the receipt), compute an ISO-8601 duration and add it as a `duration:` tag on the transaction header (e.g., `duration: PT34M19S`). Use the receipt's timestamps and the explicit `timezone:` when computing durations.
- Modifier detection: If a sequence of `food_or_drink:` tags contains a base item followed by modifiers (for example: `奶茶`, then `多奶`), combine them using `+` into a single tag: `food_or_drink: 奶茶 + 多奶`. Do not leave modifiers as standalone tags.

See SKILL.md for general procedures and cross-theme rules.

## More Examples

(Include detailed examples from SKILL.md and user feedback here)

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [food_translations.yml](./food_translations.yml)
- [SKILL.md](./SKILL.md)
