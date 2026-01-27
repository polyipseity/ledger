---
name: Editing Guidelines
description: Best practices for editing and maintaining personal ledger journals.
applyTo: "**/*.journal"
---

# Editing Guidelines

See [edit-journals](../skills/edit-journals/) skill for complete guidance.

## Best Practices

- Include preludes in monthly journals
- Maintain balance assertions
- Tag all transactions appropriately
- Format and validate before committing
- Maintain opening/closing patterns
- **Strictly maintain chronological order:** All transactions in every journal file must be strictly ordered by date, and by time within each date. Out-of-order entries are not permitted. Always insert new transactions in the correct chronological position.
- Register all payees in the appropriate `preludes/*.journal` file using `payee` lines. Never declare payees in monthly or yearly journals. Always insert new payees in strict lexicographical (ASCII/Unicode) order within the payee section. When adding a payee, check the entire payee section to ensure correct placement and move any out-of-order entries if found.

## Anti-Patterns to Avoid

- Manually editing year-level journals (use monthly journals only)
- Committing without validation (`python -m check`)
- Missing timezone tags (always use UTC+08:00)
- Spaces in account names (use colons)
- Unencrypted confidential files (encrypt before commit)
- **Out-of-order transactions:** Never insert or leave transactions out of chronological order (by date, then by time). This is a critical error and must be corrected immediately.
- Declaring payees anywhere except a `preludes/*.journal` file (never add `payee` lines to monthly or yearly journals). Adding payees out of lexicographical order, or failing to correct existing order mistakes.

## Related Documentation

- [edit-journals](../skills/edit-journals/) - Complete journal editing guidance
- [add-transactions](../skills/add-transactions/) - Adding transactions from raw data
- [validate-journals](../skills/validate-journals/) - Validation and formatting
- [Transaction Format Conventions](./transaction-format.instructions.md) - Transaction structure
- [Account Hierarchy](./account-hierarchy.instructions.md) - All available accounts
