# Currency Conversion Transactions Theme

This file contains rules, clarifications, and examples specific to currency conversion and foreign exchange transactions. Use this file whenever a transaction involves exchanging one currency for another.

## When to Use

- Any transaction involving currency exchange or conversion
- Transactions with multiple currencies in postings

## Key Rules

- Record exchange rate in a comment on the transaction
- Use appropriate equity:conversions accounts for each currency
- Always use canonical payee names or UUIDs as per SKILL.md
- Insert transactions in strict chronological order

### Currency Conversion Procedure

- When a transaction involves exchanging one currency for another, record the exchange rate in a comment on the transaction.
- Use the appropriate `equity:conversions` accounts for each currency.
- Insert the transaction in strict chronological order.

#### Example

```hledger
2026-01-10 Currency Exchange  ; activity: transfer, time: 14:30:00, timezone: UTC+08:00
 equity:conversions:HKD-USD:HKD                   -1 000.00 HKD  ; 1000 HKD → 130 USD, rate: 0.1300
 assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:HKD savings    1 000.00 HKD
 equity:conversions:HKD-USD:USD                     130.00 USD
 assets:banks:eb3a5344-9cdb-471f-a489-ea8981329cd6:USD           -130.00 USD
```

See SKILL.md for general procedures and cross-theme rules.

## Examples

(Include detailed examples from SKILL.md and user feedback here)

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [id_mappings.yml](./id_mappings.yml)
- [SKILL.md](./SKILL.md)
