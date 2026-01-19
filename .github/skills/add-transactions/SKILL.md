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

Example: Instead of "What is this?", ask: "Was this lunch or general dining?"

---

## Step-by-Step Procedure

### 1. Find a Template Transaction

Search recent ledger entries for similar transactions (same payee, category, or account) to use as a formatting template. Recent transactions reflect current conventions.

```powershell
grep -r "food and drinks" ledger/2025/2025-01/ | head -5
```

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

**Ask**: Payment method? Which account used before?

**Resolution**: Cross-reference bank statements for that date. Check recent transactions for same payee. If unclear → ask user and save pattern.

### Pattern: Payee / IDs / Item code normalization

When a receipt shows multiple identifiers, shorthand IDs, or truncated payee names, normalize as follows before inserting into the ledger:

- Prefer the merchant name (payee) as it appears on the receipt, simplified to a canonical short form used in existing journal entries (e.g., `Taste` rather than `Taste Festival Walk`).
- Preserve long numeric IDs from the receipt that uniquely identify the transaction (for audit/tracing). If multiple IDs appear, keep the main long ID and insert additional long IDs in the order they appear; omit short, non-unique terminal codes when redundant.
- For food_or_drink item descriptions, prefer the full code + name from the receipt when available (e.g., `014192 OWN RUN SIU MEI BBQ 叉燒飯`) rather than a shortened or OCR-corrupted form.

Quick rules (short):

- When a merchant is on-campus (e.g., AC2), use the location in the canonical name: `AC2 Canteen, CityUHK`.
- When a receipt shows multiple IDs, include them in parentheses in the transaction header in the order found (or as specified by `id_mappings.yml`), e.g. `(5B182E26011513304506CB, 0200001008, 12882)`.
- When listing multiple items in a single posting, repeat the tag name for each item due to hledger parsing limitations, e.g. `; food_or_drink: item 1, food_or_drink: item 2`.

When the user provides a clarification like "payee should be X, food_or_drink Y, add ID Z between existing IDs", apply the above normalization to the transaction and save the pattern to this skill's "Common Clarification Patterns" so future clarifications follow the same transformation.

### Pattern: Duration calculation

When a receipt includes both a start time (transaction time) and an explicit end time, compute an ISO-8601 duration (end_time - start_time) and add a `duration: PTxHxMxS` tag to the transaction metadata (example: `duration: PT43M55S`). Only compute durations when both times are unambiguous and in the same timezone (UTC+08:00).

Rule of thumb: if two times on a receipt differ by more than one minute, treat the older time as the start and the newer time as the end.

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
git commit -S -m "Add transactions from [source]"
```

Notes:
- Prefer the `scripts/*.py` entry points (e.g. `python scripts/format.py`) instead of `-m` module style; the latter may not work in some environments.
- Only run the format/check step on-demand or just before committing to avoid noisy CI-style runs during incremental edits.

## Related Documentation

- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md) - Detailed hledger format specifications
- [Account Hierarchy & Meanings](../../instructions/account-hierarchy.instructions.md) - All available accounts and their purposes
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices and anti-patterns
- [Security Practices](../../instructions/security.instructions.md) - Handling confidential data with private.yaml
