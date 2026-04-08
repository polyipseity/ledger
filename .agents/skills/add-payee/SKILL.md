---
name: add-payee
description: Add a new payee (merchant, person, organization, or UUID) to the correct preludes journal file, maintaining strict lexicographical order.
---


# Skill: Add Payee

**Note:** See `AGENTS.md` and `.agents/instructions/agent-quickstart.instructions.md` for agent workflow rules and a concise checklist; use the Todo List Tool for multi-step tasks.

**Note:** See `.agents/instructions/developer-workflows.instructions.md` for canonical coding, testing, and formatting rules (type annotations, docstrings, `__all__`, test conventions). See `AGENTS.md` for agent workflow rules.

**Payee directives must always be added to a `preludes/` journal file, never to monthly or yearly journals. If you encounter a strict payee error (e.g., 'payee ... has not been declared'), resolve it by adding the payee to the appropriate `preludes/` file as described below.**

This skill describes how to add a new payee to the ledger system.

## When to Use

- When a new merchant, person, organization, or UUID payee is encountered in a transaction or needs to be registered for future use.

**Example & guidance:** See `./examples.md` for a short example of adding a payee to `preludes/self.journal`. Validate with `bun run format` and `bun run check` after adding.

## Steps

1. **Determine the correct preludes file**
   - All payee directives must be placed in a `preludes/` journal file, never in a monthly or yearly journal.
   - Most payees go in `preludes/self.journal`.
   - If the payee is specific to an alternative or other scenario, use the appropriate `preludes/*.journal` file.

2. **Locate the payee section**
   - Find the block of lines starting with `payee` in the chosen preludes file.

3. **Insert the new payee**
   - Add a line: `payee <payee-name-or-UUID>`
   - Place the new payee in strict lexicographical (ASCII/Unicode) order within the payee section.
   - When adding, check the entire payee section for correct placement and move any out-of-order entries if found.

4. **Validation**

      **Note:** Use the canonical formatting and validation workflow: see `.agents/instructions/developer-workflows.instructions.md` and `.agents/instructions/common-workflows.instructions.md` for steps and examples (prefer `bun run format` and `bun run check`).

## Anti-Patterns

- **Never add payees to monthly or yearly journals.** Always use a `preludes/` file.
- Inserting payees out of order, or failing to correct existing order mistakes

## Lessons Learned

For consolidated lessons across all skills, see `.agents/instructions/continuous-learning.instructions.md`.

Key pattern: Payees must **always** be kept in strict lexicographical (ASCII/Unicode) order. When adding or editing, scan the entire payee section and proactively correct any out-of-order entries. This prevents merge conflicts and ensures consistency.

## Related Documentation

- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md)
- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md)
- [Architecture & File Organization](../../instructions/architecture.instructions.md)
- [Continuous Learning & Common Pitfalls](../../instructions/continuous-learning.instructions.md) - Lessons learned
