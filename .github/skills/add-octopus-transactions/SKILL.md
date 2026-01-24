---
name: add-octopus-transactions
description: Add missing Octopus card transactions from app transaction history. Identifies missing transport transactions, adds duration metadata for existing transactions when ending times are available, and records card reloads from Octopus wallet to Octopus card.
---

# Add Octopus Transactions Skill

This skill guides you through transcribing missing transactions from Octopus card transaction history (from the Octopus mobile app) into the personal accounting ledger.

## When to Use This Skill

- User provides Octopus card transaction history (screenshots, exported data, or transaction listings)
- Need to add missing transport transactions (MTR, bus, minibus, etc.)
- Need to add missing retail/dining transactions paid via Octopus
- Need to add missing Octopus card reloads from Octopus wallet
- Need to update existing transactions with duration metadata when ending times are available

## Privacy and Confidentiality

**CRITICAL**: Never expose the actual Octopus card number in any documentation, examples, or conversations. Always use placeholders like `<octopus-card-uuid>` or generic examples like `1608ef20-afcd-4cd0-9631-2c7b15437521` (which is already in the ledger).

## Understanding Octopus Accounts and Data

### Octopus Wallet vs Octopus Card

**Two distinct accounts** - do not confuse:

1. **Octopus Wallet** (`assets:digital:Octopus:<uuid>`): Digital balance in the Octopus mobile app, used for online payments and card reloads
2. **Octopus Card** (`assets:digital:Octopus cards:<uuid>`): Physical/virtual card balance, used for transit and in-person payments

**Reload flow**: Bank → Octopus Wallet → Octopus Card

### Octopus Transaction Data Format

Typical Octopus app transaction data includes:

- **Date/Time**: Format `YYYY-MM-DD HH:MM` (e.g., `2026-01-19 19:33`)
- **Merchant/Payee**: Name in Chinese or English (e.g., `港鐵`, `美心食品有限公司`, `百佳`)
- **Amount**: Positive (reload/credit) or negative (expense/debit) in HKD
- **Transaction type icons**:
  - 🚌 Transit (MTR/港鐵, buses, minibuses, ferries)
  - 🍴 Food & Dining
  - 🛍️ Retail/Shopping
  - ➕ Reload/Top-up (八達通轉賬)

### Expense Account Mapping

**Transport accounts**:

- `expenses:transport:trains` - MTR/港鐵 (Mass Transit Railway)
- `expenses:transport:buses` - Buses (KMB, Long Win Bus, etc.)
- `expenses:transport:minibuses` - Public light buses (紅色小巴/綠色小巴)
- `expenses:transport:ferries` - Ferries (Star Ferry, etc.)
- `expenses:transport:taxis` - Taxis (rare, usually cash)

**Other common accounts**:

- `expenses:food and drinks:dining` - Restaurant/canteen meals
- `expenses:food and drinks:snacks` - Snacks, bakery items
- `expenses:food and drinks:drinks` - Beverages only
- `expenses:shopping:groceries` - Supermarket purchases (ParknShop, Wellcome, etc.)
- `expenses:shopping:general` - Other retail purchases

## Step-by-Step Workflow

### Step 1: Load Journal Context

Before processing Octopus transactions, read the current month's journal to understand:

- Existing transactions (to avoid duplicates)
- Recent Octopus card balance
- Transaction patterns and formatting conventions

```powershell
# Read current month's journal
cat ledger/2026/2026-01/self.journal
```

### Step 2: Apply Two-Step Payee Mappings

Octopus transaction merchant names often differ from actual payee names used in the journal. Apply a two-step mapping process:

**Step 2a: Octopus Name → Actual Payee Name**

Check `.github/skills/add-octopus-transactions/payee_mappings.yml` for the first mapping layer.

**CRITICAL**: When transcribing Octopus merchant names, copy the exact text from the app screenshot or user input. Preserve character precision (traditional vs simplified Chinese, punctuation, spacing). Do not correct or normalize Octopus names—transcribe them exactly as shown.

Example structure:

```yaml
# One-to-one mapping (list with single payee, can extend to multiple later)
"百佳":
  - "Taste"
"美心 / 星巴克":
  - "城大食坊 (City Express)"
"餐飲 / 會所":
  - "A-1 Bakery"

# One-to-many mapping (same Octopus name can map to multiple payees)
"Union Cash Register Co. Ltd.":
  - "ParknShop"      # Use context: grocery amounts, food items
  - "Wellcome"       # Use context: different location or time pattern
  - "7-Eleven"       # Use context: small amounts, snacks
```

**One-to-Many Mapping**: When an Octopus transaction name maps to multiple possible payees (list has >1 item), use context to determine which one:

- Transaction amount (grocery vs snack amounts)
- Transaction category (food vs retail)
- Time of day (breakfast vs dinner)
- Location patterns (search recent journal entries for similar transactions)
- Items purchased (if known)

**Behavior**: If no mapping exists for an Octopus merchant name, **ALWAYS ask the user** to provide the actual payee name. **DO NOT infer or guess** - even if the mapping seems obvious, ask the user explicitly. Then add the mapping to `add-octopus-transactions/payee_mappings.yml`.

**Step 2b: Payee Translation/Canonicalization (Optional)**

After applying the Octopus → Actual mapping, check if the actual payee name needs further translation or canonicalization using `.github/skills/add-transactions/payee_mappings.yml`:

```yaml
# Example: Translate Chinese payee to English canonical form
"美心": "Maxim's"
"百佳": "ParknShop"
"薩莉亞": "Saizeriya"
```

**Example flow**:

1. Octopus transaction shows: `美心 / 星巴克`
2. Apply Step 2a: `美心 / 星巴克` → `美心` (using add-octopus-transactions/payee_mappings.yml)
3. Apply Step 2b: `美心` → `Maxim's` (using add-transactions/payee_mappings.yml)
4. Result: Transaction payee is `Maxim's`

**UUID mappings**: After both mapping steps, check `private.yaml` (decrypted) for confidential merchant/person UUIDs. If a UUID exists for the final payee name, use the UUID in the transaction.

### Step 3: Identify Missing vs Existing Transactions

**Matching criteria** (in order of priority):

1. **Exact match**: Same date, time, merchant, and amount → Skip (already recorded)
2. **Time difference**: Same date, merchant, amount, but Octopus time is later → Update with duration (see Step 4)
3. **Missing transaction**: No match found → Add new transaction (proceed to Step 5)

**Transport transaction patterns**:

- MTR: Usually `-4.4 HKD`, `-4.9 HKD`, `-3.2 HKD` (varies by distance)
- Buses: Usually `-5.9 HKD`, `-6.4 HKD` (varies by route)
- Minibuses: Usually `-8.0 HKD` to `-10.0 HKD`

**Search strategy**:

```powershell
# Search for transactions on a specific date
grep "2026-01-19" ledger/2026/2026-01/self.journal

# Search for MTR transactions with specific amount
grep -A2 "Mass Transit Railway.*2026-01-19" ledger/2026/2026-01/self.journal | grep "4.40"

# Search for transactions with Octopus card account
grep "1608ef20-afcd-4cd0-9631-2c7b15437521" ledger/2026/2026-01/self.journal
```

### Step 4: Add Duration Metadata (When Applicable)

**Scenario**: An existing journal transaction matches an Octopus transaction (same date, merchant, amount), but:

- Journal transaction has a start time (`time:` tag)
- Octopus transaction timestamp is later (several minutes later)
- Journal transaction does **NOT** already have a `duration:` tag

**Interpretation**: The Octopus timestamp is the **ending time** of the activity (e.g., exiting MTR station, finishing meal).

**Action**: Calculate duration (end_time - start_time) and add `duration:` tag in ISO 8601 format to the existing transaction. **Do NOT create a new transaction**.

**When NOT to add duration**:

- If journal transaction already has `duration:` tag → Leave it unchanged
- If Octopus time difference is <2 minutes → Skip (likely rounding/precision difference)
- If amounts or merchants differ → Treat as separate transactions

**Duration format**: `PT<hours>H<minutes>M<seconds>S` (omit zero components)

- `PT35M55S` = 35 minutes 55 seconds
- `PT1H9M42S` = 1 hour 9 minutes 42 seconds
- `PT30M23S` = 30 minutes 23 seconds

**Quick checklist to avoid missing duration updates**:

- After adding/reviewing a date, scan for pairs with same merchant and amount where the Octopus time is later than the journal time
- If the journal entry has no `duration:` yet and the time gap is reasonable (>2 minutes), compute and add the `duration:`
- Do not add a second transaction for the same event; duration belongs on the original entry

**Example**:

Existing journal (no duration):

```hledger
2026-01-17 (41208456, 18) Cafe 100%  ; activity: eating, eating: breakfast, time: 10:56:05, timezone: UTC+08:00
    expenses:food and drinks:dining                                         43.00 HKD
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -43.00 HKD
```

Octopus shows: `Cafe 100%`, `-43.0 HKD`, `2026-01-17 11:32`

Duration calculation: 10:56:05 → 11:32:00 = 35 minutes 55 seconds

Updated with duration:

```hledger
2026-01-17 (41208456, 18) Cafe 100%  ; activity: eating, duration: PT35M55S, eating: breakfast, time: 10:56:05, timezone: UTC+08:00
    expenses:food and drinks:dining                                         43.00 HKD
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -43.00 HKD
```

### Step 5: Add Missing Transactions

#### Transport Transactions

**Format for MTR/港鐵**:

```hledger
2026-01-19 Mass Transit Railway  ; activity: transport, time: 19:33, timezone: UTC+08:00
    expenses:transport:trains                                                4.40 HKD
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521       -4.40 HKD
```

#### Reload Transactions

Each reload involves **TWO transactions** with the **SAME timestamp**:

1. **Step 1: Bank → Octopus Wallet** (eDDA authorization)
2. **Step 2: Octopus Wallet → Octopus Card** (visible in Octopus app)

**Important**: When the Octopus transaction history shows `八達通轉賬` or `Octopus Transfer` with a positive amount (e.g., `+200.0`), this represents **Step 2** only (Wallet → Card). Step 1 (Bank → Wallet) must be verified separately from bank email notifications, and both transactions should have the same timestamp.

**Complete reload transaction example**:

```hledger
; Step 1: Bank to Octopus Wallet (from bank email notification)
2026-01-14 (C1E56743229, FRN202601144PAYD0103092279035, OCTOPUS038084565301286497) self  ; activity: transfer, time: 09:16, timezone: UTC+08:00, via: eDDA
    assets:digital:Octopus:abb12fe5-9fea-4bc4-b062-5a393eea2be2        200.00 HKD
    assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings     -200.00 HKD

; Step 2: Octopus Wallet to Octopus Card (from Octopus transaction history)
2026-01-14 self  ; activity: transfer, time: 09:16, timezone: UTC+08:00
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      200.00 HKD
    assets:digital:Octopus:abb12fe5-9fea-4bc4-b062-5a393eea2be2           -200.00 HKD
```

**Extracting transaction IDs from bank email notifications**:

When the user provides Hang Seng Bank email notifications for Octopus reloads (subject: "你的直接付款授權已被成功執行/Your Direct Debit Authorisation has been processed successfully"), extract ALL three transaction identifiers:

1. **Email reference** (from subject line): Extract the code in square brackets after "Ref:"
   - Example: Subject contains `Ref:[C1E56743229]` → Extract `C1E56743229`

2. **FRN reference** (from email body): Look for the "備註" / "Ref:" field in the email body
   - Example: Email body shows `Ref: FRN202601144PAYD0103092279035` → Extract full FRN string

3. **Debtor Reference**: Always `OCTOPUS038084565301286497` (constant eDDA identifier for this Octopus account)

4. **Transaction timestamp**: Extract from "交易日期 / Transfer date:" field
   - Example: `2026-01-14 09:16`

5. **Amount**: Extract from the green HKD amount at top of email
   - Example: `HKD 200.00`

**Workflow when bank email is available**:

1. Extract all fields from email (see above)
2. Add Step 1 (Bank → Wallet) transaction with complete transaction IDs
3. Add Step 2 (Wallet → Card) transaction with matching timestamp
4. Both transactions use the SAME time from the email

**Workflow when bank email is NOT available**:

When only Octopus transaction history shows a reload:

1. Add Step 2 (Wallet → Card) transaction immediately:

```hledger
; Step 2: Octopus Wallet to Octopus Card (from Octopus transaction history)
2026-01-15 self  ; activity: transfer, time: 18:14, timezone: UTC+08:00
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      200.00 HKD
    assets:digital:Octopus:abb12fe5-9fea-4bc4-b062-5a393eea2be2           -200.00 HKD
```

1. Ask user to provide bank email notification for complete transaction IDs
2. If bank email is later provided, add Step 1 transaction with complete IDs

#### Dining/Retail Transactions

**Format**:

```hledger
2026-01-19 Maxim's  ; activity: eating, eating: lunch, time: 13:50, timezone: UTC+08:00
    expenses:food and drinks:dining                                         49.00 HKD  ; food_or_drink: (unknown)
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -49.00 HKD
```

**Note**: When the specific items purchased are not available in the Octopus transaction data, use `food_or_drink: (unknown)` or similar placeholder. Ask the user if they remember the items or have a receipt.

### Step 6: Transaction Ordering and Insertion

**Insert transactions in strict chronological order** within the monthly journal file, sorted by date and then by time (HH:MM:SS). When multiple transactions occur on the same date, insert them in time order.

**Chronology safety checks**:

- After adding entries for a given date, run a quick scan and ensure the time sequence is strictly ascending within that date
- Prefer inserting new blocks without copying surrounding lines; copying nearby lines during edits can accidentally duplicate existing transactions
- If a later-time entry appears above an earlier-time entry, move the block down until the sequence reads top-to-bottom by time
- Never create or keep duplicates: if the same merchant/time pair appears twice, remove the extra block

**Post-edit verification helpers**:

```powershell
# Verify ordering for a specific date
grep "2026-01-15" ledger/2026/2026-01/self.journal

# Search for unintended duplicates
grep -n "Game Zone.*2026-01-15" ledger/2026/2026-01/self.journal
```

**Within each transaction**, order postings with **debits first (increases), then credits (decreases)**:

```hledger
; Correct order: expense (debit) first, then asset decrease (credit)
2026-01-19 Mass Transit Railway  ; activity: transport, time: 19:33, timezone: UTC+08:00
    expenses:transport:trains                                                4.40 HKD
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521       -4.40 HKD
```

### Step 7: Register New Payees

Before adding transactions with new merchants, register the payee in the prelude:

**Add to [preludes/self.journal](../../../preludes/self.journal)** (keep alphabetized):

```hledger
payee Mass Transit Railway
payee ParknShop
payee Saizeriya
```

For confidential payees with UUIDs, register the UUID and add the mapping to `private.yaml`:

```hledger
payee <merchant-uuid>
```

```yaml
# In private.yaml (before encrypting)
<merchant-uuid>: "Confidential Merchant Name"
```

Then encrypt: `python -m encrypt`

## Common Scenarios and Patterns

### Octopus showing different merchant name than actual payee

**Scenario**: Octopus transaction shows merchant name (e.g., "Union Cash Register Co. Ltd.", "餐飲 / 會所") but the actual payee in your journal is different (e.g., "Cafe 100%", "A-1 Bakery").

**Common cause**: Octopus app displays generic or payment processor names rather than actual merchant names. Check the mapping in `add-octopus-transactions/payee_mappings.yml` to resolve to the correct payee.

**Action**:

1. Check if mapping exists → Use mapped name
2. If no mapping → Ask user for actual payee and add to `payee_mappings.yml`
3. Do not infer or guess the mapping

**Example**:

- Octopus: "Union Cash Register Co. Ltd." → Maps to "Cafe 100%"
- Octopus: "美心 / 星巴克" → Maps to "城大食坊 (City Express)"

### Merchant name variations

**Scenario**: Octopus shows `美心食品有限公司` but you need to determine the actual payee name for the journal.

**Resolution (Two-step mapping process)**:

1. **First mapping**: Check `add-octopus-transactions/payee_mappings.yml` for Octopus name → Actual payee
   - **If no mapping exists**: ALWAYS ask the user "What is the actual payee name for Octopus transaction '美心食品有限公司'?"
   - **DO NOT infer or guess** - even if you think you know the answer, ask explicitly
   - Add the user's response to `add-octopus-transactions/payee_mappings.yml`

   - **If multiple mappings exist** (one-to-many): Use context to disambiguate
     - Check recent journal entries for similar transactions at this merchant
     - Consider transaction amount, category, time, and location
     - Example: "Union Cash Register Co. Ltd." could be ParknShop (groceries, 30-50 HKD), Wellcome (groceries, different location), or 7-Eleven (snacks, 10-20 HKD)
     - If context is insufficient, ask the user: "This Octopus transaction 'Union Cash Register Co. Ltd.' -35.0 HKD could be ParknShop, Wellcome, or 7-Eleven. Which merchant was it?"

2. **Second mapping** (optional): Check `add-transactions/payee_mappings.yml` for translation/canonicalization
   - Example: `美心` → `Maxim's`
   - If no mapping exists here, you may use the Chinese name or ask for translation

3. **UUID check**: After both mappings, check `private.yaml` for UUID (if confidential)

4. Use the final payee name consistently across all transactions

**Important**: Never skip the first mapping step. Never infer mappings. If the Octopus transaction name is not in `add-octopus-transactions/payee_mappings.yml`, always ask the user and add it.

### Unknown food items

**Scenario**: Octopus transaction shows a dining transaction with an amount, but no item details.

**Ask**: Do you remember what you ordered? Do you have a receipt?

**Resolution**: If user provides details, add specific `food_or_drink:` tags. Otherwise, use `food_or_drink: (unknown)` placeholder.

### Reload source ambiguity

**Scenario**: Octopus transaction shows a reload (`八達通轉賬 +200.0 HKD`) but you don't have bank transaction details.

**Ask**: Can you provide the bank email notification for this reload? (Subject: "你的直接付款授權已被成功執行")

**Resolution**:

- If email provided → Extract all transaction IDs (see Step 5 reload section) and create BOTH Step 1 (Bank→Wallet) and Step 2 (Wallet→Card) transactions
- If email not available → Add only Step 2 (Wallet→Card) transaction, ask user for bank email to complete Step 1 later

**Key data in bank email**:

- Email reference (subject): `C1E56743229`
- FRN reference (body): `FRN202601144PAYD0103092279035`
- Debtor reference: `OCTOPUS038084565301286497` (constant)
- Timestamp: `2026-01-14 09:16`
- Amount: `HKD 200.00`

### Transport transaction timing

**Scenario**: Octopus shows MTR transaction at `2026-01-19 19:33` but journal has an MTR transaction at `19:28` with a different amount.

**Analysis**: These are likely **two separate transactions** (entry and exit at different stations, or different journeys). The Octopus timestamp represents when the card was tapped.

**Resolution**: Add both transactions separately. Do not combine or update duration unless there is a clear match (same amount, same context).

### Multiple transactions at same merchant on same day

**Scenario**: Multiple transactions at the same merchant within a short time period.

**Resolution**:

- Use time differences to distinguish transactions
- If times are very close (within 1-2 minutes), they may be the same transaction → verify with amounts and context

### Unusual amounts

**Examples**:

- MTR with amount other than typical fares (e.g., `-1.4 HKD`) → likely a short journey or discounted fare, record as-is
- Round amounts in retail (e.g., `-40.0 HKD`, `-35.0 HKD`) → likely grocery or retail purchases

### Transactions paid by Octopus Wallet vs Card

**Scenario**: Some merchants accept Octopus app QR code payments (Wallet) vs physical card tap (Card).

**Resolution**:

- Octopus transaction history should indicate the payment source
- If paid via Octopus Wallet (app balance), use `assets:digital:Octopus:<uuid>` instead of `assets:digital:Octopus cards:<uuid>`

## Validation and Commit

Before committing, validate and format the journal:

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

## Complete Example

**User provides**: Screenshots of Octopus card transaction history showing:

- `2026-01-19 19:33` | 港鐵 | `-4.4 HKD`
- `2026-01-19 13:50` | 美心 / 星巴克 | `-38.9 HKD`
- `2026-01-15 18:14` | 八達通轉賬 | `+200.0 HKD`

**Agent workflow**:

1. Read current month's journal: `cat ledger/2026/2026-01/self.journal`
2. Check for existing transactions:
   - Search for `2026-01-19` with MTR and `-4.4 HKD` → Found at `00:18`, not at `19:33` → **Missing transaction**
   - Search for `2026-01-19` with `美心` or `Maxim` and `-38.9 HKD` → Found at `13:50:22` → **Existing transaction** (time matches)
   - Search for `2026-01-15` with `200.00 HKD` and `Octopus` → Found at `18:14` → **Existing reload** (already recorded)
3. Apply two-step payee mappings:
   - **Step 1**: `港鐵` → `Mass Transit Railway` (from `add-octopus-transactions/payee_mappings.yml`)
   - **Step 2**: Check `add-transactions/payee_mappings.yml` → No further translation needed
   - **Step 1**: `美心 / 星巴克` → `美心` (from `add-octopus-transactions/payee_mappings.yml`)
   - **Step 2**: `美心` → `Maxim's` (from `add-transactions/payee_mappings.yml`)
4. Add missing transaction:

   ```hledger
   2026-01-19 Mass Transit Railway  ; activity: transport, time: 19:33, timezone: UTC+08:00
       expenses:transport:trains                                                4.40 HKD
       assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521       -4.40 HKD
   ```

5. Validate and commit:

   ```powershell
   python scripts/format.py ; python scripts/check.py
   # For transaction commits follow `.github/instructions/git-commits.instructions.md` and use the ledger header (no body).
   git commit -S -m "ledger(self.journal): add 1 transaction(s)"
   ```

**Result**: One new transaction added, existing transactions verified, no duplicates created.

## Related Documentation

- [Add Transactions Skill](../add-transactions/SKILL.md) - General transaction transcription guidance
- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md) - Detailed hledger format specifications
- [Account Hierarchy & Meanings](../../instructions/account-hierarchy.instructions.md) - All available accounts and their purposes
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md) - Best practices and anti-patterns
- [Match Octopus Statement Transactions](../match-octopus-statement-transactions/SKILL.md) - Match Octopus Wallet statement rows to journal transactions and update datetimes (seconds-only edits silent by default).
