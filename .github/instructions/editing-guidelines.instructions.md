---
name: Editing Guidelines
description: Best practices and anti-patterns for editing and maintaining the personal ledger journals, including formatting, validation, and commit procedures.
applyTo: "**/*.journal"
---

# Editing Guidelines

Best practices and anti-patterns for editing and maintaining the personal ledger.

This documentation has been organized into a reusable Agent Skill that Copilot can load automatically when relevant to your editing tasks.

**See the dedicated skill:** [edit-journals](../skills/edit-journals/) - Complete guidance on journal editing with best practices and anti-patterns

## Summary

The edit-journals skill covers:

### Best Practices
- Always include preludes
- Maintain balance assertions
- Tag appropriately
- Format after editing
- Validate before commit
- Maintain opening/closing pattern
- Sort properties in comments
- Document complex transactions

### Anti-Patterns to Avoid
- Do not edit year-level journals manually
- Do not commit without validation
- Do not use inconsistent formatting
- Do not create transactions without timezone tags
- Do not modify prelude definitions lightly
- Do not leave unencrypted confidential files
- Do not remove existing accounts or payees
- Do not use spaces in account names

## Quick Reference

Recommended workflow for any journal edits:

```powershell
# 1. Make edits to journal files
# [Edit ledger/2025/2025-01/self.journal or other files]

# 2. Format all journals
python -m format

# 3. Validate all journals
python -m check

# 4. If edited confidential data
python -m encrypt

# 5. Review changes
git status
git diff

# 6. Commit
git add .
git commit -S -m "Description of changes"
```

## Related Skills and Documentation

- [edit-journals](../skills/edit-journals/) skill - Complete journal editing guidance
- [add-transactions](../skills/add-transactions/) skill - Adding transactions from raw data
- [validate-journals](../skills/validate-journals/) skill - Validation and formatting
- [Transaction Format Conventions](./transaction-format.instructions.md) - Transaction structure details
- [Account Hierarchy & Meanings](./account-hierarchy.instructions.md) - All available accounts
