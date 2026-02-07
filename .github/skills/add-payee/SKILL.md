---
name: add-payee
summary: Add a new payee (merchant, person, organization, or UUID) to the correct preludes journal file, maintaining strict lexicographical order.
---


# Skill: Add Payee

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. **Never** use `Any` or `Unknown` in type annotations — prefer explicit types, Protocols, or TypedDicts. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

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

      **Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical guidance — prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

         Example:

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
