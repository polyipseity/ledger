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

## Anti-Patterns to Avoid

- Manually editing year-level journals (use monthly journals only)
- Committing without validation (`python -m check`)
- Missing timezone tags (always use UTC+08:00)
- Spaces in account names (use colons)
- Unencrypted confidential files (encrypt before commit)

## Related Documentation

- [edit-journals](../skills/edit-journals/) - Complete journal editing guidance
- [add-transactions](../skills/add-transactions/) - Adding transactions from raw data
- [validate-journals](../skills/validate-journals/) - Validation and formatting
- [Transaction Format Conventions](./transaction-format.instructions.md) - Transaction structure
- [Account Hierarchy](./account-hierarchy.instructions.md) - All available accounts
