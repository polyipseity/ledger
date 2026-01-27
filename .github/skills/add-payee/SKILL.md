---
name: add-payee
summary: Add a new payee (merchant, person, organization, or UUID) to the correct preludes journal file, maintaining strict lexicographical order.
---

# Skill: Add Payee

This skill describes how to add a new payee to the ledger system.

## When to Use

- When a new merchant, person, organization, or UUID payee is encountered in a transaction or needs to be registered for future use.

## Steps

1. **Determine the correct preludes file**
   - Most payees go in `preludes/self.journal`.
   - If the payee is specific to an alternative or other scenario, use the appropriate `preludes/*.journal` file.

2. **Locate the payee section**
   - Find the block of lines starting with `payee` in the chosen preludes file.

3. **Insert the new payee**
   - Add a line: `payee <payee-name-or-UUID>`
   - Place the new payee in strict lexicographical (ASCII/Unicode) order within the payee section.
   - When adding, check the entire payee section for correct placement and move any out-of-order entries if found.

4. **Validation**
   - Run the formatting and validation scripts to ensure the file remains valid and well-ordered.

## Anti-Patterns

- Adding payees to monthly or yearly journals (never do this)
- Inserting payees out of order, or failing to correct existing order mistakes

## Related Documentation

- [Editing Guidelines](../../.github/instructions/editing-guidelines.instructions.md)
- [Transaction Format Conventions](../../.github/instructions/transaction-format.instructions.md)
- [Architecture & File Organization](../../.github/instructions/architecture.instructions.md)
