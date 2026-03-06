# Currency Conversion Transactions Theme

This file contains rules, clarifications, and examples specific to currency conversion and foreign exchange transactions. Use this file whenever a transaction involves exchanging one currency for another.

## When to Use

- Any transaction involving currency exchange or conversion
- Transactions with multiple currencies in postings

## Key Rules

- Record exchange rate in a comment on the transaction
- Use appropriate equity:conversions accounts for each currency
- Always use canonical payee names or UUIDs as per SKILL.md
**Note:** See `.github/instructions/transaction-format.instructions.md` for chronological ordering rules.
- Only use status markers for the original pending lending/borrowing transaction (see SKILL.md and lending_borrowing_transactions.md). Repayment transactions must NOT have a status marker. If you see a status marker in any currency conversion or repayment transaction, it is an error and must be corrected.

### Currency Conversion Procedure

- When a transaction involves exchanging one currency for another, record the exchange rate in a comment on the transaction.
- Use the appropriate `equity:conversions` accounts for each currency.

See SKILL.md for general procedures and cross-theme rules.

**Examples:** See `./examples.md` for a canonical currency conversion worked example and edge cases.

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [id_mappings.yml](./id_mappings.yml)
- [SKILL.md](./SKILL.md)
