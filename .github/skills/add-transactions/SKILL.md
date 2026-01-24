---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill

This skill guides you through transcribing financial transactions from raw data into the personal accounting ledger following hledger conventions.

## When to Use This Skill

Transcribing transactions from receipts, bank statements, invoices, or OCR-extracted data

## When Clarification Is Needed

For unclear data: 1) **Search ledger** for similar transactions to infer missing details. 2) **Ask specific questions** with context (not vague prompts). 3) **Save generalizations** to "Common Clarification Patterns" (without confidential data) if pattern cannot be inferred and is not already documented.

Quick clarifications to apply when the user specifies rules:

- Keep zero-value "complimentary" postings but remove the text "(complimentary)" from the food_or_drink tag value.
- If payment method is unclear, ask the user which account paid (cash / Octopus / bank / credit card / paid-by-friend, etc.). When someone else paid, record the settlement as a liability posting to the appropriate account (e.g., `liabilities:loans:friends:<uuid>` or `liabilities:loans:colleagues:<uuid>`) and mark the transaction as pending with `!`.

Additional automatic rules:

- **Tag validation**: Only use tags declared in the active prelude(s). Do not invent new tag names. If a standard metadata field (e.g., `activity`, `eating`, `reward`) is not in the prelude, omit it from the transaction. This ensures consistency and prevents undefined metadata pollution.
- **Payee/counterparty resolution**: Decrypt `private.yaml` and look up the counterparty (friend, colleague, merchant). If a UUID mapping exists for the counterparty, use the UUID as the payee name in the transaction header and all related postings. This centralizes confidentiality and ensures consistent referencing across the ledger.
- **Time precision**: When a receipt or document lacks an explicit time, ask the user to provide one (HH:MM or HH:MM:SS in the transaction timezone). Do not assume or interpolate times. Only record `time:` in the comment metadata after user clarification.
- **Liability assertions**: When recording a repayment that settles a liability (any `liabilities:*` account), append an assertion `= 0.00 <CURRENCY>` to the liability posting. This makes the debt clearance explicit and helps catch inconsistencies. Related pending transactions (`!`) with the same counterparty should be marked as cleared (`*`) once repayment is confirmed.
- **Pending transaction state transitions**: When a repayment transaction is added and settles one or more pending (`!`) transactions, update those pending transactions to cleared (`*`) status to reflect the completed settlement.

---

## Step-by-Step Procedure

### 1. Find a Template Transaction

Search recent ledger entries for similar transactions (same payee, category, or account) to use as a formatting template. Recent transactions reflect current conventions.

```powershell
grep -r "food and drinks" ledger/2025/2025-01/ | head -5
```

### 1.5. Apply Payee, Food, and ID Mappings

Before inserting a transaction, check for existing mappings and apply them:

1. **Payee & UUID mapping**: Check `private.yaml` (decrypted) for the payee name or similar counterparty entries. If a match or near-match exists with medium confidence, ask the user to confirm before applying. Otherwise, check `payee_mappings.yml` for the canonical English name. After identifying a UUID, search the prelude(s) to determine the correct account hierarchy (e.g., `equity:friends:`, `equity:kins:families:`, `liabilities:loans:colleagues:`) before inserting the transaction. Apply confirmed mappings or use the UUID if one exists in `private.yaml`.
2. **Food translations**: Check `food_translations.yml` for approved translations. Apply if found.
3. **Receipt IDs**: Extract identifiers from the receipt and place them in parentheses before the payee name in the transaction header. Use the form `(ID1, ID2, ...)` or `(ID, count)` when an item count is specified by the user (e.g., `(800815, 3) Cafe 100%`).

Follow the ID extraction and ordering rules documented in the "Pattern: ID extraction and ordering" section below or in `id_mappings.yml` for payee-specific patterns.

**If no mapping exists**, do not translate automatically—use the original text and consider proposing a mapping for user approval.

### 2. Apply Status Markers

- `!` = pending (awaiting confirmation, repayment, or follow-up)
- `*` = cleared (verified, all parties settled)
- no marker = normal transaction

**Update status:** Change `!` to `*` when a pending transaction completes:

```hledger
2025-01-15 ! Friend Lunch                    # Pending
    assets:loans:friends:<uuid>      50.00 HKD
    assets:cash                     -50.00 HKD

2025-01-20 * Friend Lunch                    # Update to cleared when repaid
    assets:loans:friends:<uuid>      50.00 HKD = 0.00 HKD
    assets:banks:<bank-uuid>        -50.00 HKD
```

### 3. Register New Entities

Before adding a transaction with a new merchant or counterparty:

Keep payee declarations in `preludes/*.journal` alphabetized; insert any new payee in order.

**Add payee to [preludes/self.journal](../../../preludes/self.journal):**

```hledger
payee Example Restaurant
payee <new-person-uuid>
```

**Add account if needed:**

```hledger
account assets:banks:<new-bank-uuid>:Currency
account liabilities:loans:friends:<new-friend-uuid>
```

**For confidential details**, add UUID mapping to `private.yaml`:

```yaml
<new-person-uuid>: "John Doe"
<new-bank-uuid>: "Bank XYZ Account 123-456"
```

Then encrypt: `python -m encrypt`

### 4. Handle Currency Conversions

Record exchange rate in comment:

```hledger
2026-01-10 Currency Exchange  ; activity: transfer, time: 14:30:00, timezone: UTC+08:00
    equity:conversions:HKD-USD:HKD                   -1 000.00 HKD  ; 1000 HKD → 130 USD, rate: 0.1300
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings    1 000.00 HKD
    equity:conversions:HKD-USD:USD                     130.00 USD
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:USD           -130.00 USD
```

### 5. Apply Tags

Add rich metadata for analysis:

```hledger
2025-01-19 Example Restaurant  ; activity: eating, eating: lunch, time: 12:30:15, timezone: UTC+08:00
    expenses:food and drinks:dining        50.00 HKD  ; food_or_drink: pasta, food_or_drink: coffee
    assets:digital:Octopus cards:<uuid>   -50.00 HKD
```

**Tag categories:** activity (eating, transport, shopping, transfer, etc.) | eating (breakfast, lunch, dinner) | time (HH:MM:SS) | timezone (UTC+08:00) | location | item | food_or_drink | reward

### 6. Insert Transaction in Chronological Order

**Transactions must be sorted by date and time.** Insert new transactions in the correct position within the monthly journal file, maintaining chronological order.

Within each transaction, order postings with credits first, then debits.

## Common Clarification Patterns

These are scenarios that commonly require clarification when processing raw transaction data. Review this section before asking the user—your clarification may already be documented here.

### Pattern: Shared Meal

**Scenario**: How to split or categorize a multi-person meal?

**Ask**: Split equally or covering all? Expected reimbursement?

**Resolution**: Reimbursement expected → use `assets:loans` (pending status `!`). Fully covered → single transaction. Already split → record only your portion.

### Pattern: Multi-Category Receipt

**Scenario**: Single receipt with items in different expense categories.

**Ask**: Purchased together or separately? Line items or combined total?

**Resolution**: Items separate → one transaction with multiple postings. Bundled → primary category with detailed tags. Check recent receipts from same merchant for patterns.

Note: If the receipt shows a price next to each line item (i.e., individual amounts per item), record each item as a separate posting with its own amount and a repeated `food_or_drink` tag. Only group items into a single posting when the receipt lists a single grouped price (e.g., a meal set) rather than per-item prices.

Example (receipt lists per-item prices):

```hledger
2026-01-15 AC2 Canteen, CityUHK  ; activity: eating, eating: lunch, time: 13:30:45
    expenses:food and drinks:dining        15.00 HKD  ; food_or_drink: 小碗菜
    expenses:food and drinks:dining        18.00 HKD  ; food_or_drink: 小碗菜
    expenses:food and drinks:dining        10.00 HKD  ; food_or_drink: 小碗菜
    expenses:food and drinks:dining         6.00 HKD  ; food_or_drink: 白飯
    assets:digital:Octopus cards:<uuid>   -49.00 HKD
```

### Pattern: Unclear Purpose

**Scenario**: Amount and date clear, but category ambiguous (maintenance vs. repair vs. cleaning?).

**Ask**: What activity type? Recurring or one-time?

**Resolution**: Search ledger for similar merchants/amounts (past 3 months). If pattern exists → use same category/tags. If not → ask user and save pattern.

### Pattern: Unclear Payment Method

**Scenario**: Category known, but which source account (cash, card, transfer)?

**Ask**: Which account paid? (cash / Octopus / bank / credit card / family member / etc.)

**Resolution**: Cross-reference bank statements for that date. Check recent transactions for same payee to identify account pattern. If unclear → **ask the user directly** which account should be recorded, then apply the clarification.

Common payment accounts:

- `assets:cash` – physical cash payment
- `assets:digital:Octopus cards:<uuid>` – Octopus card (Hong Kong transit/payment card)
- `assets:digital:Octopus:<uuid>` – Octopus app/digital wallet balance
- `assets:banks:<bank-uuid>:<currency>` – bank account transfer
- `liabilities:credit cards:<uuid>` – credit card
- `equity:kins:families:<uuid>` – paid by family member (settle later)
- `equity:friends:<uuid>` – paid by friend (settle later)

Example (user clarified: paid by family member):

```hledger
2026-01-16 (55601108, 0110, 43) ad982faf-117f-4ddc-bc68-3606fb71ff52  ; activity: eating, eating: dinner, time: 19:59:05, timezone: UTC+08:00
    expenses:food and drinks:dining              68.00 HKD  ; food_or_drink: 煎白菜鮮肉餃（12隻）
    expenses:food and drinks:dining              60.00 HKD  ; food_or_drink: 金湯肥牛鍋
    expenses:food and drinks:dining              55.00 HKD  ; food_or_drink: 豆腐蔬菜鍋
    equity:kins:families:3833b42e-dad3-425c-b254-904be68993e4  -183.00 HKD
```

### Pattern: Payee / IDs / Item code normalization

When a receipt shows multiple identifiers, shorthand IDs, or truncated payee names, normalize as follows before inserting into the ledger:

- Prefer the merchant name (payee) as it appears on the receipt, simplified to a canonical short form used in existing journal entries (e.g., `Taste` rather than `Taste Festival Walk`).
- When payee identity is unclear (e.g., ambiguous location name, restaurant code instead of name), **ask the user to clarify** the actual merchant/payee name rather than using a generic descriptor.
- **UUIDs and confidentiality**: If a payee has a UUID mapping in `private.yaml` for privacy, use the UUID as the payee name in the transaction. UUID usage is orthogonal to payee clarity—it's a privacy/confidentiality mechanism, not a signal of unclear payee. Always clarify the payee name with the user first, then apply UUID mapping if one exists.
- Preserve long numeric IDs from the receipt that uniquely identify the transaction (for audit/tracing). If multiple IDs appear, keep the main long ID and insert additional long IDs in the order they appear; omit short, non-unique terminal codes when redundant.
- **When a receipt shows item/table/section counts or qualifiers** (e.g., "table 43", "row 3"), append these as the final element in the ID tuple after all receipt IDs. Example: `(receipt-id, checkout-id, 43)` or `(transaction-id, table-number, 3)`.
- For food_or_drink item descriptions, prefer the full code + name from the receipt when available (e.g., `014192 OWN RUN SIU MEI BBQ 叉燒飯`) rather than a shortened or OCR-corrupted form.

Quick rules (short):

- When a merchant is on-campus (e.g., AC2), use the location in the canonical name: `AC2 Canteen, CityUHK`.
- When payee name is unclear, ask the user; then apply UUID if confidential mapping exists.
- When a receipt shows multiple IDs plus a count or qualifier (e.g., table number), include all in parentheses in the order: `(id1, id2, ..., count)`. Example: `(55601108, 0110, 43)`.
- When listing multiple items in a single posting, repeat the tag name for each item due to hledger parsing limitations, e.g. `; food_or_drink: item 1, food_or_drink: item 2`.

When the user provides a clarification like "payee should be X, food_or_drink Y, add ID Z between existing IDs", apply the above normalization to the transaction and save the pattern to this skill's "Common Clarification Patterns" so future clarifications follow the same transformation.

### Pattern: Duration calculation

When a receipt includes both a start time (transaction time) and an explicit end time, compute an ISO-8601 duration (end_time - start_time) and add a `duration: PTxHxMxS` tag to the transaction metadata (example: `duration: PT43M55S`). Only compute durations when both times are unambiguous and in the same timezone (UTC+08:00).

Rule of thumb: if two times on a receipt differ by more than one minute, treat the older time as the start and the newer time as the end.

### Pattern: Food item modifiers and separators

When transcribing food/drink items:

**Item separators**: The middle dot character `・` separates distinct food items and should result in separate `food_or_drink:` entries. Receipt sub-items (marked with `--`, `+`, or similar prefixes) are typically separate items or substitutions, not modifiers.

**Modifiers vs Items**:

- **Modifiers** are preparation adjustments applied to a base item (e.g., "more milk", "less ice", "no sugar", "fewer"). Use `+` syntax: `food_or_drink: hot coffee + more milk`
- **Items** are distinct food components, even if listed as sub-items on the receipt (e.g., "sweet corn", "garlic butter on toast", "French fries"). List separately: `food_or_drink: item1, food_or_drink: item2`

**Complimentary/zero-cost items**: Free or zero-dollar items (e.g., "set hot coffee $0.0") should be treated as **items with modifiers**, not as separate line items. Include them in the transaction using the `+` syntax to show customization.

**Non-items to ignore**: Items that cost $0 and describe the transaction type (e.g., "dine-in", "take-away") should be omitted entirely—they provide no value information and describe the consumption method, not what was consumed.

**Rule of thumb**:

- If it's a noun phrase describing a dish component or drink offering (even if $0), treat it as an **item**.
- If it describes how to prepare/customize an item, treat it as a **modifier**.
- If it describes the transaction type (e.g., location of consumption) and costs $0, **ignore it**.

Example receipt transcription (includes modifiers and zero-cost items):

```text
Original: 
  義大利粉番茄肉醬套餐
  - 七味蛋
  Set Hot Coffee (complimentary)
    - Extra milk
  Dine-in $0

Result: food_or_drink: Spaghetti Bolognese with Fried Egg in Assorted Chilli Pepper, food_or_drink: set hot coffee + extra milk
```

Example with distinct items:

```text
Original: 鮮奶炒滑蛋・吉列魚柳
Sub-items: -- 粒粒粟米; 轉 蒜香牛油多士

Result: food_or_drink: scrambled egg, food_or_drink: sweet corn, food_or_drink: cutlet fish fillet, food_or_drink: garlic butter on toast
```

Example with true modifiers:

```text
Original: 熱咖啡
Modification: 多奶

Result: food_or_drink: hot coffee + more milk
```

### Pattern: English translation lookup for food_or_drink

Store confirmed translation mappings in `./.github/skills/add-transactions/food_translations.yml`, keyed by payee with an optional `default` fallback. Example:

```yaml
Payee Name:
    "蒜香法包": "garlic baguette"
default:
    "蒜香法包": "garlic baguette"
```

Behavior:

- When a mapping exists and the user has approved it, replace the transaction's `food_or_drink` value with the English translation only (do not keep the original non-English text).
- If no mapping is found, do NOT translate automatically. Prompt the user with options:
    1) Leave the original non-English text as-is in the transaction.
    2) Provide a translation mapping manually (which will be stored after approval).
    3) Search the journals for candidate mappings and present them for approval.

Only write mappings into `food_translations.yml` after explicit user approval.

### Pattern: Payee mappings (translations and canonical names)

Use a single mappings file `./.github/skills/add-transactions/payee_mappings.yml` for both translations and canonical name normalization. Each entry maps a source/alias to a canonical form and may include metadata (e.g., location normalization).

Example:

```yaml
"百份百": "Cafe 100%"
"AC2 Canteen": "AC2 Canteen, CityUHK"
default: {}
```

Behavior:

- When a mapping exists and is approved, replace the payee with the canonical name only (do not keep the original text).
- If no mapping is found, do NOT translate or rename automatically. Offer options: keep as-is, supply a mapping to add, or search journals for candidates to propose.
- Persist mappings only with explicit user approval.

Automatic suggestions:

- When processing a receipt, suggest existing food/payee translations and ID mappings found in `food_translations.yml`, `payee_mappings.yml`, and `id_mappings.yml`.
- Present suggested mappings and ID extraction in a short summary for user approval; if approved, apply them to the transaction and (optionally) persist the mapping for future auto-application.
- Do not persist suggestions without explicit approval; always show the proposed changes first.

### Pattern: ID extraction and ordering

Store payee-specific ID extraction rules in `./.github/skills/add-transactions/id_mappings.yml`. Each payee maps to an ordered list of identifier names (and optional simple regex hints) that define the exact order IDs should appear in the transaction parentheses.

Example `id_mappings.yml` structure:

```yaml
"Cafe 100%":
    order: [transaction_id, table_number]
    regex:
        transaction_id: "\\d{6,}"
        table_number: "\\d+"
default:
    order: []
```

Behavior:

- When a mapping exists and is approved, the parser should extract identifiers from the receipt in the mapped order and insert them in the transaction header parentheses (omitting missing values or using `?` as placeholder when only partially available).
- If multiple candidate IDs match the same regex, prefer the longest numeric token (likely the transaction number) and keep others in the documented order.
- If no mapping exists, fall back to the generic rule: place the longest numeric ID first, then any shorter numeric IDs in the sequence they appear on the receipt.
- Only write or update `id_mappings.yml` after explicit user approval.

Automatic suggestions for IDs:

- When a payee has an `id_mappings.yml` entry, propose the extracted identifiers and their ordered placement; allow the user to accept, edit, or reject before inserting into the transaction header.
- If no mapping exists but a clear pattern of IDs is detected, propose a one-line candidate mapping for user approval to persist.

## Validation and Commit

Run validation and formatting together only when you explicitly request it or immediately before committing changes. On Windows PowerShell you can run both in one command so the work is faster and atomic:

```powershell
# Format then check (single command)
python scripts/format.py ; python scripts/check.py

# Review changes
git status
git diff

# Commit when ready
# For transaction commits follow `.github/instructions/git-commits.instructions.md` and use the ledger header (no body).
git commit -S -m "ledger(self.journal): add N transaction(s)"
```

Notes:

- Prefer the `scripts/*.py` entry points (e.g. `python scripts/format.py`) instead of `-m` module style; the latter may not work in some environments.
- Scripts expect the working directory to be the repository root (not the `scripts/` folder).
- Only run the format/check step on-demand or just before committing to avoid noisy CI-style runs during incremental edits.

## Related Documentation

- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md) - Detailed hledger format specifications
- [Account Hierarchy & Meanings](../../instructions/account-hierarchy.instructions.md) - All available accounts and their purposes
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices and anti-patterns
- [Security Practices](../../instructions/security.instructions.md) - Handling confidential data with private.yaml
- [Match Octopus Statement Transactions](../match-octopus-statement-transactions/SKILL.md) - Match Octopus Wallet statement rows to journal transactions and update datetimes (seconds-only edits silent by default).
