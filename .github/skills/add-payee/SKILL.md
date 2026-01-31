---
name: add-payee
summary: Add a new payee (merchant, person, organization, or UUID) to the correct preludes journal file, maintaining strict lexicographical order.
---


# Skill: Add Payee

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When registering new payees, use the todo list tool to break down the process into actionable steps.**

Mark each step as in-progress and completed, and update the todo list after each change to ensure all payee registration steps are completed and nothing is missed.

**Payee directives must always be added to a `preludes/` journal file, never to monthly or yearly journals. If you encounter a strict payee error (e.g., 'payee ... has not been declared'), resolve it by adding the payee to the appropriate `preludes/` file as described below.**

This skill describes how to add a new payee to the ledger system.

## When to Use

- When a new merchant, person, organization, or UUID payee is encountered in a transaction or needs to be registered for future use.

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

      - Run the formatting and validation scripts to ensure the file remains valid and well-ordered.
      - **Script commands: Always run from the `scripts/` directory**
         - For all Python scripts (e.g., `python -m check`, `python -m format`, `python -m depreciate`, `python -m shift`, `python -m replace`, `python -m encrypt`, `python -m decrypt`), **always set the working directory to `scripts/` using the tool's `cwd` parameter**. This applies to both direct Python invocations and all script wrappers (e.g., `./check`, `check.bat`, etc.).
         - **Never run scripts from the root directory or any other location.** Running from the wrong directory will cause include and file discovery errors.
         - Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.
         - **Critical:** If you run any script or wrapper from the wrong directory, you will encounter include errors, missing file errors, or incorrect results. Always double-check the working directory before running any script command.
         - Example:

            ```powershell
            python -m format   # set cwd to scripts/
            python -m check    # set cwd to scripts/
            ```

## Anti-Patterns

- **Never add payees to monthly or yearly journals.** Always use a `preludes/` file.
- Inserting payees out of order, or failing to correct existing order mistakes

## Related Documentation

- [Editing Guidelines](../../.github/instructions/editing-guidelines.instructions.md)
- [Transaction Format Conventions](../../.github/instructions/transaction-format.instructions.md)
- [Architecture & File Organization](../../.github/instructions/architecture.instructions.md)
