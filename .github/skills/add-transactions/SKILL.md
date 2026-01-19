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

### Pattern: Unclear Purpose

**Scenario**: Amount and date clear, but category ambiguous (maintenance vs. repair vs. cleaning?).

**Ask**: What activity type? Recurring or one-time?

**Resolution**: Search ledger for similar merchants/amounts (past 3 months). If pattern exists → use same category/tags. If not → ask user and save pattern.

### Pattern: Unclear Payment Method

**Scenario**: Category known, but which source account (cash, card, transfer)?

**Ask**: Payment method? Which account used before?

**Resolution**: Cross-reference bank statements for that date. Check recent transactions for same payee. If unclear → ask user and save pattern.

## Validation and Commit

After adding transactions:

```powershell
# 1. Validate all journals
python -m check

# 2. Format all journals
python -m format

# 3. Review changes
git status
git diff

# 4. Commit
git commit -S -m "Add transactions from [source]"
```

## Related Documentation

- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md) - Detailed hledger format specifications
- [Account Hierarchy & Meanings](../../instructions/account-hierarchy.instructions.md) - All available accounts and their purposes
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices and anti-patterns
- [Security Practices](../../instructions/security.instructions.md) - Handling confidential data with private.yaml
