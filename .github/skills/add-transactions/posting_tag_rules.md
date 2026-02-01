# Posting and Tag Validation Rules

This file contains all rules and best practices for posting structure, tag validation, and tag usage in transaction entry. Use this file whenever you need to validate tags, structure postings, or handle tag-related edge cases.

## Tag Validation and Usage

- Only use tags declared in the active prelude(s). Never invent or use undefined tags.
- If a standard metadata field (e.g., `activity`, `eating`, `reward`) is not in the prelude, omit it from the transaction.
- Before adding any tag, verify it's valid by grepping the preludes for lines that begin with `tag`.
- Use the existing, validated tag name when recording items. Do not invent tag names.
- If you must ask the user to add a new tag, present the candidate and request approval; do not persist it silently.
- When extracting line items from receipts, attach them using the validated tag (e.g., `food_or_drink:` if present in the preludes). Add repeated tag entries for multiple items.
- Always split distinct food/drink items into separate `food_or_drink:` tags.
- **Never place any itemization, discount, or similar tags (such as `food_or_drink:`, `discount:`, or item codes) in the transaction header.** These must always be placed in posting comments only, never in the header line. This applies to all item, discount, and similar tags, regardless of transaction type or payee.

## Posting Structure

- Do not add tags to the transaction header line; only use them in posting comments as per convention.
- For food/drink modifiers, always use a space before and after the plus sign (e.g., `food_or_drink: hot coffee + more milk`).
- Only valid tags in posting comments.

## Related Files

- [preludes/*.journal](../../../preludes/)
- [SKILL.md](./SKILL.md)
