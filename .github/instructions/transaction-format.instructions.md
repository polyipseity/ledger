---
name: Transaction Format Conventions
description: Learn hledger transaction format, structure, tags, patterns, and formatting conventions for the ledger system.
applyTo: "**/*.journal"
---


# Transaction Format Conventions

**Note:** See `AGENTS.md` for agent workflow rules and use the Todo List Tool for multi-step tasks.

## Payee and ID Mapping

When transcribing a transaction:

1. **Always check `private.yaml` for payee mappings.**
2. **If the merchant name or a similar entry is found in `private.yaml`, use the corresponding UUID as the payee.**
3. **If not found, use the merchant name as the payee.**
4. **For receipt/transaction identifiers:**
    - Prepend all available identifiers (order number, receipt number, etc.) in parentheses at the start of the payee line.
    - If an `id_mappings.yml` exists, follow its mapping for identifier formatting and order. If the payee is not in the mapping, update the mapping simultaneously when adding the entry.

All payees (merchants, people, organizations, UUIDs) must be registered in the appropriate `preludes/*.journal` file using a line of the form:

```hledger
payee <payee-name-or-UUID>
```

Never declare or repeat payee lines in monthly or yearly journals. Always insert new payees in strict lexicographical (ASCII/Unicode) order within the payee section of the relevant preludes file. When adding a payee, check the entire payee section to ensure correct placement and move any out-of-order entries if found. This ensures a single source of truth for payee names and UUIDs and keeps payee lists organized.

## Standard Transaction Structure

```hledger
YYYY-MM-DD [!|*] payee  ; activity: value, tag: value, timezone: UTC+08:00
    account:subaccount[:subsubaccount]  [-]amount CURRENCY [= balance CURRENCY]
    account:subaccount  [; tag: value, tag: value]
```

### Components Explained

- **Date**: ISO 8601 format (YYYY-MM-DD)
- **Status marker**: Optional single character after date:
  - `!` (exclamation) = pending/unclear
  - `*` (asterisk) = cleared/verified
  - None = normal transaction
- **Payee**: Name of merchant, person, or organization
- **Comment tags**: Key-value pairs in format `tag: value`, semicolon-separated
- **Posting lines**: Account and amount pairs, indented with spaces
- **Balance assertion**: Optional `= balance CURRENCY` to verify account state after transaction

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## Chronological Order Requirement

**All transactions in every journal file must be strictly ordered by date, and by time within each date. Out-of-order entries are not permitted. Always insert new transactions in the correct chronological position. When adding or editing transactions, always check for and enforce correct time order within each date. If multiple transactions share the same date, they must be sorted by their time (using the `time:` tag or, if missing, by logical/expected sequence). Never leave or introduce out-of-order transactions.**

## Key Patterns

### Opening and Closing Balances

- **First transaction of month**: `opening balances` payee, lists all accounts with opening values and `= balance CURRENCY`
- **Last transaction of month**: `closing balances` payee, zeroes out all accounts with `= 0.00 CURRENCY`
- **Purpose**: Marks month boundaries and validates account balances

### Balance Assertions

```hledger
2025-01-19 Purchase
    assets:cash                           -50.00 HKD = 1000.00 HKD
    expenses:food:dining                   50.00 HKD
```

Use `= balance CURRENCY` on postings to assert the running balance after that posting. Helps catch data entry errors early.

### Common Tags

**Metadata tags** used throughout transactions:

- **activity**: Type of activity (eating, transport, tutoring, fees, transfer, repayment, etc.)
- **time**: Time of transaction in HH:MM or HH:MM:SS format
- **timezone**: Always `UTC+08:00` (Hong Kong standard)
- **duration**: ISO 8601 duration (e.g., `PT1H30M`)
- **item**: Specific item or product name
- **food_or_drink**: Detailed food/beverage descriptions
- **eating**: Meal type (breakfast, lunch, dinner, afternoon tea, snacks)
- **posted**: Posted date for transactions recorded later
- **rate**: Currency conversion rate (e.g., `1 USD = 7.8 HKD`)
- **location**: Geographic location or venue
- **reward**: Reward/prize identification

### Formatting Rules

**Amounts and Decimal Precision:**

- Decimal precision: 2 decimal places (e.g., `123.45 HKD`)
- Large numbers: Use space separators for thousands (e.g., `16 966.42 HKD`)
- Points/loyalty currencies: May use no decimals (e.g., `100 _PT/B`)

**Account Naming:**

- Account UUIDs: Many accounts include UUID identifiers (e.g., `assets:banks:<bank-uuid>`)
- Nested accounts: Use colons (`:`) to separate hierarchy levels
- No spaces in account names

**Timezone Convention:**

- Consistently use `UTC+08:00` (Hong Kong time) in all timezone tags
- Always include timezone in metadata for transaction timestamps

**Posting Order:**

- List credit postings before debit postings within a transaction.

## Special Accounts and Patterns

### Accumulated Depreciation

```hledger
2025-01-31 depreciation
    assets:accumulated depreciation      -50.00 HKD
    expenses:depreciation                 50.00 HKD
```

Contra-asset account tracking depreciation of owned objects.

### Currency Conversions

```hledger
2025-01-19 Currency Exchange
    assets:banks:<bank-uuid>             7.80 USD
    equity:conversions:HKD-USD:USD        -7.80 USD = 0.00 USD
    equity:conversions:HKD-USD:HKD      -60.84 HKD = -60.84 HKD
    assets:banks:<bank-uuid>:HKD         60.84 HKD
```

Track currency conversion transactions to maintain rate information.

### Balance Tracking Accounts

- **equity:conversions**: Currency/point conversion tracking with rate metadata
- **equity:unaccounted**: Tracks unaccounted differences during reconciliation
- **equity:external:self.alternatives**: Links to alternative investment tracking

## Example Transaction

```hledger
2025-01-19 Generic Cafe  ; activity: eating, eating: lunch, time: 12:30:15, timezone: UTC+08:00
    expenses:food and drinks:dining       50.00 HKD  ; food_or_drink: sandwich, food_or_drink: coffee
    assets:digital:Octopus cards:<uuid>  -50.00 HKD
```

## Food/Drink Tagging and Posting Conventions

- **Always split each food or drink item into a separate `food_or_drink:` tag.**
- **Do not combine multiple items into a single tag.**
- **Do not add translations unless required by convention.**
- **Maintain the order of items as they appear on the receipt.**
- **If an item description is missing or unreadable, use `food_or_drink: (unknown)` as a placeholder and prefer to confirm with the user before guessing.**

## Account and Tag Selection

- **Use the most specific and correct account** (e.g., `dining`, `snacks`, etc.) as per the context and conventions. Do not default to a generic or similar account if a more precise one is available.
- **Use the correct `eating:` tag** (`lunch`, `afternoon tea`, etc.) based on the actual meal or context from the receipt.
- **Align columns and tags for readability.**
- **Follow the tag order and formatting conventions strictly as per the project’s transaction-format instructions.**

## Identifiers and Traceability

- **Always include all available receipt, order, or transaction identifiers in the payee line for traceability, following the mapping rules above.**

## Generalized Learnings for Future Tasks

- Always cross-reference `private.yaml` and `id_mappings.yml` before assigning payees or formatting identifiers.
- Never assume a payee UUID—always verify or create the mapping as needed.
- Split all food/drink items into individual tags and maintain their order.
- Use the most contextually accurate account and tags.
- Maintain strict formatting and tag order for consistency and readability.
