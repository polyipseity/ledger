# Food Transactions Theme

This file contains rules, clarifications, and examples specific to food and restaurant transactions. Use this file whenever a transaction involves food, drink, dining, or restaurant-related expenses.

## When to Use

- Any transaction involving food, drink, or dining (including restaurants, cafes, canteens, takeout, etc.)
- Transactions with food/drink itemization, modifiers, or translations

## Key Rules

- Always use canonical payee names (see payee_mappings.yml). All mapping values in `payee_mappings.yml` are YAML sequences (lists). If a list contains multiple canonical candidates, disambiguate using contextual cues (store/branch id, receipt tokens, item categories, locality); prompt for clarification if context is insufficient.
- Normalize food/drink items and modifiers (see below for rules)
- Use `food_or_drink:` tag in posting comments for each item
- Within a `food_or_drink:` tag, do not escape quotation marks; write `"` directly and **avoid comma characters** (replace them with semicolons) to prevent accidental splitting into multiple tags.
- **Food tag language consistency:** Preserve the language of the original receipt item names; do not translate English names into Chinese (or vice versa) unless the mapping file explicitly requires it. When the same item is listed in multiple languages on the receipt (for example, `Hot Chocolate (熱朱古力)` or `熱朱古力 (Hot Chocolate)`), prefer the English name in the journal. If no English appears, keep the first language shown on the receipt. Validated examples: Saizeriya 2026-04-15 preserves Italian-style dish names exactly as printed (意式野菜焗蛋, A香蒜辣汁野菌西蘭花); American Diner 2026-04-17 preserves Chinese dish codes with names (G.鮮蘑菇炒蛋). Do not apply translation mappings without explicit user approval in the transaction.
- Use English translations from food_translations.yml only after user approval
- Split items and modifiers as per the rules below
- Do not invent new tags; only use those declared in the prelude

### Itemization, Modifiers, Item Numbers, and Tagging

- **Always fully itemize all food and drink items.** Never use placeholders like "(see receipt)". Every item and its amount must be listed explicitly, with a separate `food_or_drink:` tag for each.
- Preserve printed receipt itemization. If a receipt shows individual menu lines and amounts, record each printed line as its own posting rather than collapsing the transaction into a single subtotal comment. Maintain service charge as a separate `expenses:food and drinks:fees` posting, and keep the final payment posting separate from the item postings.
- **For Taste and similar supermarkets or bakeries, always include the item number or code from the receipt as part of the `food_or_drink:` tag, if available.** For example, `food_or_drink: 091421 LA BOULANGERIE BREAD`.
- Separate distinct food/drink items into separate `food_or_drink:` tags, even if listed together on the receipt (e.g. "麵包, 咖啡" → `food_or_drink: 麵包, food_or_drink: 咖啡`).
  - Drop a leading "配" prefix when present; it means "with" and not part of the item name (e.g. `麥皮 配蛋治` → two tags `麥皮, 蛋治`).
  - If a menu line embeds `配` as a connector between two named items (e.g., `...米線配汽水`), split into two items: the main dish and the companion item. Record the companion as its own posting when priced separately, or as a `0.00` posting when explicitly shown as bundled/free.
  - If a receipt line shows multiple full-priced menu items, they are **not** modifiers; do **not** join them with `+`.
  - If the receipt uses `+` between what appears to be full menu items (especially in Chinese item names), treat those as separate items and reformat using commas instead of `+`.
  - A common Cafe 100% pattern shows a bundled set with several named components under one total amount; record each named component as a separate tag and use commas between them, reserving `+` only for true modifiers (ice level, sweetness, milk, etc.). See examples.md for a worked example.
- Use `+` syntax only for modifiers (e.g. "hot coffee + more milk" → `food_or_drink: hot coffee + more milk`).
- Remove parenthetical descriptors that are not part of the item name (e.g. "(辣)麥炸雞" → "麥炸雞").
- Remove conjunction prefixes that are not part of the item name (e.g. "配朱古力" → "朱古力").
- The prefix character "配" is especially common; always strip it from the item name when it means "with" rather than being part of the dish (e.g. "配蛋治" → "蛋治").
- Remove ordering/meal markers such as "堂食", "外賣", "自取", and the set indicator "餐" when they are not part of the food/drink name but instead describe service type or a set meal context. This includes removing these markers when shown in parentheses (e.g., "壽司$8 (堂食)" should become just "壽司$8").
- Remove leading or trailing descriptors that are not part of the dish name, such as time-of-day markers like `(早)`, `(午)`, `(晚)`, transaction markers like `轉`, or accidental leading `+` characters. These are metadata, not menu items.
- The middle dot character `・` separates distinct food items and should result in separate `food_or_drink:` entries.
- Receipt sub-items (marked with `--`, `+`, or similar prefixes) are typically separate items or substitutions, not modifiers.
- Complimentary/zero-cost items (e.g., "set hot coffee $0.0") should still be recorded explicitly with modifiers using `+` syntax.
  - Preferred posting pattern: use a dedicated `expenses:food and drinks:drinks  0.00 HKD` line for the zero-priced drink when the receipt shows it as a separate drink line.
  - If the receipt does not show a complimentary item, do not add one.
  - **Important:** only record a zero‑priced drink if it is explicitly listed on that receipt; do not assume every Cafe 100% breakfast includes coffee. Verify each transaction individually.
- When a receipt prints a separate voucher, e-coupon, or cash-card discount line, record it as a distinct negative expense posting with a `food_or_drink:` comment and keep the payment posting separate. This preserves the receipt structure and makes the discount auditable.
- Items that cost $0 and describe the transaction type (e.g., "dine-in", "take-away") should be omitted entirely.
- **Zero-priced itemization consistency:** When a receipt itemizes multiple zero-priced components (e.g., toppings, modifiers, garnishes, complimentary sides bundled with a base meal), record each component as a separate posting line with its own `food_or_drink:` tag. This preserves receipt structure fidelity and enables accurate audit trails. Example: TamJai SamGor breakfast combo on 2026-04-16 itemizes as 1 × 33.00 HKD base meal posting followed by 3 × 0.00 HKD postings for each named modifier (黑糖, 紅豆, 芋圓), each with its own `food_or_drink:` tag. The total still balances (33.00), but each component is explicitly logged.- For TamJai SamGor breakfast combo receipts where the printed sub-items appear grouped beneath a single paid base meal line, preserve that grouping with a single 0.00 HKD posting line containing multiple `food_or_drink:` tags separated by commas. Use `+` syntax only when the grouped text clearly represents modifiers of a base drink (for example, `熱咖啡 + 多奶 + 走攪棍`).

### Modifiers vs Items

- Modifiers are preparation adjustments applied to a base item (e.g., "more milk", "less ice"). Use `+` syntax: `food_or_drink: hot coffee + more milk`.
- Items are distinct food components, even if listed as sub-items on the receipt (e.g., "sweet corn", "garlic butter on toast"). List separately: `food_or_drink: item1, food_or_drink: item2`.
- In Chinese receipts, modifiers tend to be short phrases about preparation (e.g., 去冰, 少糖, 無糖, 多奶, 加奶, 轉配). If the text after a `+` looks like a standalone dish name (often including nouns like 麵/飯/湯/粉/餃/肉/菜/etc.), treat it as a separate item and split with commas instead.
- If a sequence of `food_or_drink:` tags is present and the first is a base item (e.g., a drink) and the following are modifiers (e.g., ice level, sweetness, size), combine them into a single tag using the `+` syntax. For example, `food_or_drink: 冰蜜檸檬綠茶, food_or_drink: 去冰, food_or_drink: 7分甜` should become `food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜`.
- Use common sense when determining modifier relationships: if a modifier clearly applies to a specific item (e.g., `多奶` clearly modifies a coffee or tea), attach it to that item rather than leaving it as a standalone `food_or_drink:` tag. If it is ambiguous, choose the most plausible base item and keep the tags readable, but flag it for review if needed.

#### Example: Drink with Modifiers

Original: 冰蜜檸檬綠茶, 去冰, 7分甜

Result: food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜

### Translation

- Store confirmed translation mappings in `food_translations.yml`, keyed by payee with an optional `default` fallback.
- When a mapping exists and the user has approved it, replace the transaction's `food_or_drink` value with the English translation only.
- If no mapping is found, do NOT translate automatically. Prompt the user with options: leave as-is, provide a mapping, or search journals for candidates.
- Only write mappings into `food_translations.yml` after explicit user approval.

**Examples:** See `./examples.md` for canonical worked examples (drink modifiers, taste item numbers, itemization, modifiers, and unknown item handling).

### Unknown or Unreadable Items

- If an item on the receipt is missing, illegible, or OCR failed to reliably capture it, record a placeholder tag `food_or_drink: (unknown)`. Use this only when the transaction clearly represents a food/drink purchase but the specific item(s) cannot be determined from the source.
- When multiple items are clearly present but one or more are unreadable, add one `(unknown)` tag per unreadable item when quantity is obvious; otherwise add a single `(unknown)` tag for the posting and note to confirm later if necessary.
- Prefer to confirm with the user or the receipt source before guessing item names. Do not invent item names for unclear text.

### Clarification Patterns (Food/Drink)

- Shared meal: Ask if split equally, covering all, or expecting reimbursement. Use `assets:loans` and pending status if reimbursement expected.
- Multi-category receipt: Ask if items are purchased together or separately. When the receipt shows per-item prices, record each item as its own posting line with the item's amount and a `food_or_drink:` comment tag. Ensure the item postings sum exactly to the transaction total and place the payment posting (e.g., the `assets:digital:Octopus cards:...` line) as the final posting for the full negative total. Maintain the order of postings to match the receipt.
- Payee/IDs/item code normalization: Prefer canonical payee names, clarify ambiguous names, and use UUIDs for confidentiality if mapped. **Always check `private.yaml` for a UUID mapping and use the UUID as the payee if present.**
- If the receipt header includes multiple IDs (for example `000-964096, 36` at Saizeriya or `374369, K459` at American Diner), preserve both identifiers in the journal header in the order defined by `id_mappings.yml`.
- Timezone: All transactions that include a time must also include an explicit `timezone:` (e.g., `timezone: UTC+08:00`). This helps compute durations reliably and keeps entries consistent across journals.
- **Duration calculation precision:** If both start and end times are present (for example, an order/printed time and a settlement/transaction time displayed on the receipt), compute an ISO-8601 duration and add it as a `duration:` tag on the transaction header (e.g., `duration: PT34M19S`). Use the receipt's timestamps and the explicit `timezone:` when computing durations. Duration represents the time elapsed from order placement to payment settlement, not total "dwell time" in the venue. Examples from 2026-04-15–2026-04-18 batch:
  - 2026-04-16 TamJai SamGor: Order time 10:27:01, checkout ~11:03:53 = `duration: PT36M52S` (36 minutes 52 seconds)
  - 2026-04-18 Saizeriya: Order time 12:27:18, checkout ~12:57:56 = `duration: PT30M38S` (30 minutes 38 seconds)
  - These durations validate that calculated values are precise to the second and consistent with receipt timestamps.
  - If the receipt shows a later “end/settlement” time separate from the printed/ordered time, use that later time as the end point when calculating duration.
- Modifier detection: If a sequence of `food_or_drink:` tags contains a base item followed by modifiers (for example: `奶茶`, then `多奶`), combine them using `+` into a single tag: `food_or_drink: 奶茶 + 多奶`. Do not leave modifiers as standalone tags.

See SKILL.md for general procedures and cross-theme rules.

## More Examples

(Include detailed examples from SKILL.md and user feedback here)

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [food_translations.yml](./food_translations.yml)
- [SKILL.md](./SKILL.md)
