---
name: Transaction Format Conventions
description: Learn hledger transaction format, structure, tags, patterns, and formatting conventions for the ledger system.
applyTo: "**/*.journal"
---

# Transaction Format Conventions

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

This transaction:
- Records lunch purchase on Jan 19 at 12:30:15
- Splits expense between two food items with detailed descriptions
- Deducts from Octopus card digital account
- All times in UTC+08:00 (Hong Kong time)
