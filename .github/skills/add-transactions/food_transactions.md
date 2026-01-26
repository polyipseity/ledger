# Food Transactions Theme

This file contains rules, clarifications, and examples specific to food and restaurant transactions. Use this file whenever a transaction involves food, drink, dining, or restaurant-related expenses.

## When to Use

- Any transaction involving food, drink, or dining (including restaurants, cafes, canteens, takeout, etc.)
- Transactions with food/drink itemization, modifiers, or translations

## Key Rules

- Always use canonical payee names (see payee_mappings.yml)
- Normalize food/drink items and modifiers (see below for rules)
- Use `food_or_drink:` tag in posting comments for each item
- Use English translations from food_translations.yml only after user approval
- Split items and modifiers as per the rules below
- Do not invent new tags; only use those declared in the prelude

### Itemization, Modifiers, and Tagging

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

### Translation

- Store confirmed translation mappings in `food_translations.yml`, keyed by payee with an optional `default` fallback.
- When a mapping exists and the user has approved it, replace the transaction's `food_or_drink` value with the English translation only.
- If no mapping is found, do NOT translate automatically. Prompt the user with options: leave as-is, provide a mapping, or search journals for candidates.
- Only write mappings into `food_translations.yml` after explicit user approval.

### Examples

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

### Clarification Patterns (Food/Drink)

- Shared meal: Ask if split equally, covering all, or expecting reimbursement. Use `assets:loans` and pending status if reimbursement expected.
- Multi-category receipt: Ask if items are purchased together or separately. Record each item as a separate posting if receipt lists per-item prices.
- Payee/IDs/item code normalization: Prefer canonical payee names, clarify ambiguous names, and use UUIDs for confidentiality if mapped.
- Duration calculation: If both start and end times are present, compute ISO-8601 duration and add as `duration:` tag.

See SKILL.md for general procedures and cross-theme rules.

## More Examples

(Include detailed examples from SKILL.md and user feedback here)

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [food_translations.yml](./food_translations.yml)
- [SKILL.md](./SKILL.md)
