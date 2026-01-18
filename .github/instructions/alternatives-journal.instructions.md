---
name: Alternatives Journal Tracking
description: Understanding the distinction between main and alternatives journals for separate tracking of liquid versus illiquid assets.
applyTo: "ledger/**/self.alternatives.journal"
---

# Alternatives Journal Tracking

Understanding the distinction between main and alternatives journals for separate tracking of assets.

## Purpose and Scope

The [self.alternatives.journal](../../ledger/self.alternatives.journal) file tracks alternative scenarios and items that **cannot be easily converted into liquid financial assets**. This separation provides a clear distinction between:

- **Main journal** (`self.journal`): Readily accessible liquid assets with clear financial values
- **Alternatives journal** (`self.alternatives.journal`): Illiquid or experimental holdings without established market liquidity

### Why Separate Tracking?

Mixing liquid and illiquid assets in a single ledger obscures financial reality:

- **Liquid assets** (bank accounts, cash, credit card points) can be reliably converted to real currency
- **Illiquid assets** (cryptocurrency, non-transferable investments, experimental holdings) cannot be easily monetized
- **Separate tracking** provides clearer accounting of what's actually accessible vs. what's speculative

## Key Distinctions

### Main Journal (`self.journal`)

Contains liquid assets and items with clear financial value:

- **Bank accounts**: Immediate withdrawal capability
- **Cash**: Directly spendable
- **Digital payment accounts**: Octopus cards, Stripe (easily converted to banks)
- **Credit cards**: Immediate purchasing power (balance owed)
- **Rewards points**: Credit card points, store loyalty programs that function as restricted currency with known conversion rates
- **Loans**: Money lent with clear repayment expectations
- **Physical objects**: Depreciated items with salvage value

**Common characteristic**: All assets have reliable market values or redemption rates.

### Alternatives Journal (`self.alternatives.journal`)

Contains illiquid or experimental holdings:

- **Cryptocurrency**: Bitcoin, Ethereum, altcoins (volatile, no guaranteed redemption)
- **Non-transferable investments**: Locked-in stocks, bonds, restricted investments
- **Experimental holdings**: Research tracking, hypothetical scenarios, "what-if" tracking
- **Loyalty points**: Membership points with no clear redemption mechanism or value
- **Non-fungible assets**: Digital collectibles, one-of-a-kind items
- **Illiquid securities**: Shares in private companies, crowdfunding investments

**Common characteristic**: None have readily established market prices or conversion mechanisms.

## Separate Hierarchy

### Parallel Include Structure

Each journal type has its own include hierarchy:

```
ledger/
  index.journal
  self.journal                    # Main journal
  self.alternatives.journal       # Alternatives journal
  2025/
    self.journal                  # Main yearly include
    self.alternatives.journal     # Alternative yearly include
    2025-01/
      self.journal                # Monthly main
      self.alternatives.journal   # Monthly alternatives (if used)
```

### Prelude Definitions

**Main journal preludes** (`preludes/self.journal`):

- Standard account hierarchy (assets, liabilities, equity, expenses, revenues)
- Currencies: HKD, USD, CNY, EUR, KRW
- Reward points: _PT/B,_PT/C, _PT/D,_PT/E, _PT/F
- Standard payees and tags

**Alternatives journal preludes** (`preludes/self.alternatives.journal`):

- Alternative scenario accounts
- Commodity definitions for illiquid items
- Examples: GREEN$ (green currency), _BEC,_FLW, _GLB,_MET, _OPL,_PAP, _PLA,_REB, _SEA

## Examples of Tracking Scenarios

### Example 1: Credit Card Points vs Research Cryptocurrency

**Main journal - Track credit card rewards:**

```hledger
2025-01-20 Credit Card Reward
    assets:special:rewards:credit cards:<uuid>     100 _PT/D
    revenues:rewards
```

These points have redemption mechanisms (convert to statement credit, travel, gift cards).

**Alternatives journal - Track experimental crypto:**

```hledger
2025-01-20 Crypto Purchase
    assets:digital:<exchange-uuid>:Bitcoin         0.001 BTC
    assets:banks:<bank-uuid>                    -5000.00 HKD
```

Cryptocurrency value is volatile and tracking it separately clarifies it's speculative.

### Example 2: Regular Savings vs Locked Investment

**Main journal - Bank savings (liquid):**

```hledger
2025-01-01 opening balances
    assets:banks:<bank-uuid>:savings           10000.00 HKD = 10000.00 HKD
```

Access money anytime.

**Alternatives journal - Locked investment (illiquid):**

```hledger
2025-01-01 opening balances
    assets:digital:<investment-uuid>:Stock A        100 shares = 100 shares
```

Cannot withdraw until maturity or lock-in period ends.

## Tracking Both Journals

### Linking Journals

The connection between main and alternatives journals:

```hledger
# In main journal
equity:external:self.alternatives     -200 000. _PT/B

# In alternatives journal
equity:external:self.alternatives      200 000. _PT/B
```

Use `equity:external:self.alternatives` to maintain referential integrity when funds flow between journals.

### Monthly Migration

When migrating months, run `hledger close --migrate` for **both** journals:

```powershell
hledger close -f ledger/2025/2025-12/self.journal --migrate
hledger close -f ledger/2025/2025-12/self.alternatives.journal --migrate
```

This ensures opening/closing balances are properly set for both tracking streams.

### Reporting

When generating reports, you may want to:

1. Report main journal separately for financial planning
2. Report alternatives journal separately for curiosity/experimentation tracking
3. Or combine both for complete net worth (noting which portions are liquid vs illiquid)

## When to Use Alternatives Tracking

**Use alternatives journal when:**

- Tracking non-liquid holdings for reference/curiosity
- Experimenting with "what-if" scenarios
- Monitoring cryptocurrency or volatile assets
- Recording non-transferable investments
- Testing new account structures or tracking ideas

**Use main journal for:**

- Daily transactions and spending
- Regular income and expenses
- Bank accounts and accessible funds
- Standard financial planning

## Key Design Insight

The alternatives journal allows you to keep detailed records of all holdings—liquid and illiquid—without polluting the main accounting ledger with speculative or experimental assets. This separation maintains clear distinction between reliable accounting (main journal) and exploratory tracking (alternatives journal).
