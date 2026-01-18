---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill

This skill guides you through transcribing financial transactions from raw data into the personal accounting ledger following hledger conventions.

## When to Use This Skill

- Transcribing transactions from receipt images, scans, or PDFs
- Entering data from bank statements or credit card statements
- Processing OCR-extracted text from documents
- Adding transactions from invoices or order confirmations
- Entering raw transaction data from digital sources

## Step-by-Step Procedure

### 1. Find a Template Transaction

Search the ledger for the most recent similar transaction to use as a formatting template:

```powershell
# Search recent transactions for similar activity
grep -r "food and drinks" ledger/2025/2025-01/ | head -5
```

**Why recent?** Transaction conventions evolve over time. Recent entries provide the most current formatting patterns and tag usage.

Look for transactions with:

- Same payee (if repeat merchant)
- Same category (if same type of spending)
- Same account (if using same payment method)

### 2. Understand Transaction Status Markers

Transactions use status markers to track lifecycle:

- `!` (exclamation mark) = **pending/unclear** - Transaction awaiting confirmation or requires follow-up action
- `*` (asterisk) = **cleared** - Transaction completed and verified, all parties settled
- No marker = **normal** - Standard completed transaction

### 3. Apply Status Markers Correctly

**Use `!` (pending) when:**

- Lending money to a friend, awaiting repayment
- Borrowing money with repayment pending
- Transaction requires verification (e.g., amount not yet confirmed)
- Awaiting reciprocal transaction (e.g., cost-sharing not yet finalized)

**Use `*` (cleared) when:**

- Purchase completed, item received, payment settled
- Loan repayment received
- Bank statement confirms transaction
- Both parties agree on the transaction

**Use no marker for:**

- Regular, straightforward transactions
- Transactions with no pending actions
- Already-verified expenses

**Updating status:**
When a pending transaction completes, find the original transaction and change `!` to `*`:

```hledger
# Original (pending)
2025-01-15 ! Friend Lunch
    assets:loans:friends:<uuid>      50.00 HKD
    assets:cash                     -50.00 HKD

# Later (when repaid, update to cleared)
2025-01-20 * Friend Lunch            # Changed ! to *
    assets:loans:friends:<uuid>      50.00 HKD = 0.00 HKD
    assets:banks:<bank-uuid>        -50.00 HKD
```

### 4. Register New Entities

Before adding a transaction with a new merchant or counterparty:

**Add payee to [preludes/self.journal](../../preludes/self.journal):**

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

### 5. Handle Currency Conversions

For multi-currency transactions, record the exchange rate:

```hledger
2025-01-19 Currency Exchange  ; rate: 1 USD = 7.8 HKD
    assets:banks:<bank-uuid>:HKD              -78.00 HKD = 5000.00 HKD
    equity:conversions:HKD-USD:HKD            78.00 HKD = 78.00 HKD
    equity:conversions:HKD-USD:USD           -10.00 USD = -10.00 USD
    assets:banks:<bank-uuid>:USD               10.00 USD = 150.00 USD
```

Include rate in comment for reference. Reference recent conversion transactions for exact formatting patterns.

### 6. Apply Comprehensive Tagging

Rich metadata enables powerful future analysis. Add detailed tags:

```hledger
2025-01-19 Example Restaurant  ; activity: eating, eating: lunch, time: 12:30:15, timezone: UTC+08:00, location: Downtown
    expenses:food and drinks:dining        50.00 HKD  ; food_or_drink: pasta, food_or_drink: coffee
    assets:digital:Octopus cards:<uuid>   -50.00 HKD
```

**Common tag categories:**

- **activity**: eating, transport, tutoring, fees, shopping, transfer, repayment
- **eating**: breakfast, lunch, dinner, afternoon tea, snacks
- **time**: HH:MM or HH:MM:SS format
- **timezone**: Always UTC+08:00
- **duration**: ISO 8601 format (PT1H30M)
- **item**: Specific product or item name
- **food_or_drink**: Detailed descriptions of food/beverage items
- **location**: Geographic location or venue name
- **reward**: Reward/prize identification

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

- [Transaction Format Conventions](../ledger/transaction-format.md) - Detailed hledger format specifications
- [Account Hierarchy & Meanings](../ledger/account-hierarchy.md) - All available accounts and their purposes
- [Editing Guidelines](../ledger/editing-guidelines.md) - Best practices and anti-patterns
- [Security Practices](../ledger/security.md) - Handling confidential data with private.yaml
