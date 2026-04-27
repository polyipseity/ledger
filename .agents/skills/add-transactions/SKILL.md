---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration. For multiple entries, uses a separate subagent for each transaction to enable parallelization and focused scope.
---

# Add Transactions Skill — Summary

**Purpose:** Import and normalize transactions from receipts, statements, and structured sources into monthly journals. Supports both single-entry and multi-entry workflows, with multi-entry tasks delegated to independent subagents for focused, parallelizable processing.

## Workflow Selection

**Decision Logic:**

```text
if (number of entries to add/edit) == 1:
  → Use DIRECT WORKFLOW (main agent handles)
elif (number of entries to add/edit) >= 2:
  → Use MULTI-ENTRY WORKFLOW (delegate via subagents)
```

**Single Entry (Direct Handling):**

- User provides one transaction to add or edit
- Main agent handles directly using theme files and mappings
- No subagent invocation needed
- Main agent edits the journal file, validates, and reports

**Multiple Entries (Subagent-Per-Entry):**

- User provides 2+ transactions to add/edit
- Create a todo list with one item per entry
- Invoke a separate subagent for each transaction (can run in parallel)
- Collect results and perform final coordinated validation
- See [Multi-Entry Workflow (Using Subagents)](#multi-entry-workflow-using-subagents) below

**Why Two Workflows?**

- Single-entry requests are streamlined (no subagent overhead)
- Multi-entry requests benefit from parallelization and clear isolation
- Both workflows apply the same validation rules and follow the same theme files
- The split scales gracefully as batch size increases

## Core Guidance

- Use full ledger paths (e.g., `ledger/2024/2024-01/self.journal`) and insert transactions in strict chronological order; see `.agents/instructions/transaction-format.instructions.md`.
- **Multi-Entry Workflow:** Use the Todo List Tool to create one item per transaction. Mark each as `in-progress` when a subagent starts, and `completed` when it finishes. This provides visibility and ensures no entries are skipped. See [Multi-Entry Workflow (Using Subagents)](#multi-entry-workflow-using-subagents) for details.
- Use the Todo List Tool for all multi-step tasks and follow `AGENTS.md` workflow rules; see `.agents/instructions/agent-quickstart.instructions.md` for a concise command checklist.
- Use canonical scripts for formatting/validation (`bun run format` then `bun run check`); see `.agents/instructions/developer-workflows.instructions.md`. These are run by the main agent after all subagents complete (not by subagents individually).
- For food and restaurant receipts, preserve explicit printed itemization. Do not collapse a detailed receipt into a single subtotal posting when the receipt already shows individual item lines. Record each printed item or modifier with its own `food_or_drink:` comment, keep service charge as a separate `expenses:food and drinks:fees` posting, and keep the final payment posting separate.
- When adding tests for this skill, place them under a `tests_<hash>` subdirectory within the skill folder. The workspace `pyproject.toml` is already configured to discover any `.agents/skills/**/tests_*` directories, so new tests will run automatically during `bun run test`.
- Update the theme/aspect files below when introducing new patterns—these are authoritative for type-specific rules.

Theme/aspect files (authoritative):

- [Food Transactions](./food_transactions.md) — When to use: receipts with food/drink items, modifiers, or itemized bills.
- [Lending & Borrowing Transactions](./lending_borrowing_transactions.md) — When to use: loans, IOUs, shared payments, or transactions needing status markers.
- [Currency Conversion Transactions](./currency_conversion_transactions.md) — When to use: exchanges or transactions involving multiple currencies.
- [Platform Transaction & Payout Rules](./platform_payout_transactions.md) — When to use: platform payments, fees, or payout reconciliations (Stripe, PayPal, etc.).
- [Payee & ID Mapping Rules](./payee_id_mapping_rules.md) — When to use: resolving canonical payees, UUIDs, and transaction ID ordering.
- [Posting & Tag Validation Rules](./posting_tag_rules.md) — When to use: verifying posting/comment/tag structure and tag validity.
- [Transport Reward Transactions](./transport_rewards.md) — When to use: transit payments that accrue reward points or similar accrual patterns.
- [Entity Registration Rules](./entity_registration_rules.md) — When to use: registering new payees, accounts, or UUID mappings.
- [Image & Attachment Handling](./image_attachment_rules.md) — When to use: transcribing from receipt images or when attachments require validation.
- [Specialized Transaction Import & Automation](./specialized_transaction_import.md) — When to use: structured imports (CSV, email, API) and automation flows (Octopus eDDA, etc.).

Refer to each theme file for detailed rules; for canonical worked examples and edge cases see `./examples.md`. For quick definitions and key terms, see `.agents/instructions/agent-glossary.instructions.md`.

Canonical rule locations (quick map):

- Payee mapping & ID rules: `payee_id_mapping_rules.md` and `id_mappings.yml`
- Food/drinks tagging and translations: `food_transactions.md` and `food_translations.yml`
- Posting & tag validation: `posting_tag_rules.md`
- Lending/borrowing and status markers: `lending_borrowing_transactions.md`
- Specialized imports and Octopus heuristics: `specialized_transaction_import.md` and `examples.md`

If a lesson in `lessons.md` needs integration, add it to the relevant file above and replace the lesson entry with a one-line pointer.

## Multi-Entry Workflow (Using Subagents)

**When to use:** When the user requests adding or editing 2 or more transactions in a single request.

**Architecture:** Instead of the main agent handling all entries sequentially, each transaction is delegated to a separate independent subagent. This enables:

- Parallel processing of independent transactions
- Focused scope for each subagent (one transaction only)
- Clear error isolation (one entry's error doesn't block others)
- Better task tracking via todo list

**Main Agent Responsibilities:**

1. **Parse & Plan:** Receive the transaction batch and create a todo list with one item per entry (e.g., "Add transaction: 2024-01-15 Saizeriya HKD 250"). Mark each as `in-progress` before invoking the subagent.

2. **Orchestrate:** For each transaction, invoke a subagent ("General Purpose" or equivalent) with context including:
   - The exact transaction source data (receipt text, date, amounts, IDs, etc.)
   - The target ledger file path (full path, e.g., `ledger/2024/2024-01/self.journal`)
   - The current state of the target journal file (so subagent can validate against existing entries)
   - Transaction type classification (food, lending, currency, platform, etc.)
   - Instructions to format and validate the entry (but NOT to directly edit the file)
   - Links to theme files, mappings, and reference documentation
   - Explicit permission to read `private.yaml` and all mapping files

3. **Collect Results:** After all subagents complete (can run in parallel):
   - Mark each todo item as `completed`
   - Collect the formatted transaction entries (hledger output) from each subagent
   - Collect any validation issues or ambiguities reported
   - Ensure all entries are properly formatted and ready to merge

4. **Merge & Coordinate:**
   - Combine all formatted entries
   - Sort them into strict chronological order (merging with existing entries in the target journal)
   - Insert the merged entries into the target journal file
   - Verify no duplicate transaction IDs, dates, or amounts were created
   - Run `bun run format && bun run check` on the updated journal(s)

5. **Report:** Summarize results clearly (N entries added, M entries edited, any conflicts resolved, validation status).

**Subagent Invocation Template:**

```text
Invoke "General Purpose" subagent with:

- Task description: "Format and validate one transaction entry for ledger"
- Prompt includes:
  - Transaction source data (receipt text, structured format, etc.)
  - Target ledger file path (full path, e.g., ledger/2024/2024-01/self.journal)
  - Current target journal content (so subagent can check for duplicates/ordering)
  - Transaction type classification (food, lending, currency, platform, etc.)
  - Explicit instruction: "Use the add-transactions skill (read `.agents/skills/add-transactions/SKILL.md` first)
    to format this one transaction. Follow all theme files, mappings, and tag rules.
    You may read private.yaml and all mapping YAML files in the skill folder.
    Return ONLY the formatted hledger transaction block (no file editing).
    Validate that the entry is chronologically correct and doesn't duplicate existing items.
    Report any issues or ambiguities that need clarification."
  - References to relevant theme files for this transaction type
  - Links to payee_mappings.yml, id_mappings.yml, food_translations.yml as needed
```

**Key Constraints for Subagents:**

- Each subagent processes and formats only ONE transaction at a time
- Subagent MUST read the full skill file before proceeding
- Subagent MUST validate the entry locally using theme files and mappings
- Subagent MUST check chronological order against existing entries in the target journal
- **Subagent MUST NOT directly edit the journal file.** Instead, return the formatted entry as hledger text block for the main agent to merge
- Subagent MUST validate there are no duplicate transaction IDs, dates, and amounts within the same month
- Subagent MUST report back with: formatted entry, file path, validation status, any issues encountered
- Subagent can run in parallel with other subagents (no file-locking needed since they don't edit directly)

**Main Agent Final Validation Step (After All Subagents Complete):**

1. Merge all formatted entries into the target journal in strict chronological order
2. Run validation and formatting:

```powershell
cd scripts
python -m format     # Normalize formatting
python -m check      # Validate ledger
```

1. Manually verify:
   - All entries are in strict chronological order
   - No duplicate transaction IDs or identical dates/amounts
   - Payee names are from the canonical mapping
   - Tags follow the correct format (`activity:`, `eating:`, etc.)
   - Status markers are used only for lending/borrowing
   - All new entries are present in the final journal

**Example Multi-Entry Request Handling:**

User: "Add these 3 transactions to ledger/2024/2024-01/self.journal: (1) [receipt A], (2) [receipt B], (3) [existing txn ID 12345 needs date correction]"

Main agent:

1. Create todo list:
   - Add transaction from receipt A (2024-01-05 Saizeriya) — not-started
   - Add transaction from receipt B (2024-01-08 Octopus) — not-started
   - Edit transaction 12345 (fix date to 2024-01-10) — not-started

2. Invoke 3 subagents in parallel (can run concurrently):
   - Subagent 1 (in-progress): Format receipt A entry
   - Subagent 2 (in-progress): Format receipt B entry
   - Subagent 3 (in-progress): Format date correction for 12345

3. Each subagent:
   - Reads SKILL.md and relevant theme files
   - Formats the entry using appropriate theme rules
   - Checks the current journal for duplicates and ordering
   - **Returns the formatted hledger entry (does NOT edit the file directly)**
   - Reports validation status

4. Main agent collects all results and marks todos as completed:
   - Receipt A → "2024-01-05 \* (Saizeriya | …) HKD X.XX [formatted entry]"
   - Receipt B → "2024-01-08 \* (Octopus | …) HKD Y.YY [formatted entry]"
   - Edit 12345 → Updated entry with corrected date (2024-01-10)

5. Main agent merges all entries:
   - Loads current `ledger/2024/2024-01/self.journal`
   - Inserts/updates all entries in strict chronological order
   - File now contains: [existing entries] merged with [all new/edited entries], all sorted by date

6. Main agent final validation:
   - Run `bun run format && bun run check`
   - Verify chronological order, no duplicates, all payees normalized
   - Report: "3 entries processed: 2 added, 1 edited. Journal validated and formatted."

**Subagent Output Format (Machine-Parseable):**

Each subagent MUST return structured output in this format for the main agent to parse and merge:

```text
---TRANSACTION_START---
DATE: 2024-01-05
PAYEE: Saizeriya | [receipt ID or empty]
TYPE: food
TARGET_FILE: ledger/2024/2024-01/self.journal
ACTION: add  [or: edit_by_id, edit_by_date]
EDIT_REFERENCE: [if edit action, the transaction ID or date to target]
VALIDATION_STATUS: pass  [or: warn, fail]
VALIDATION_ISSUES: [empty, or list of warnings/issues if any]
---FORMATTED_ENTRY---
2024-01-05 * Saizeriya | receipt-123-abc
  assets:cards:octopus            -50.00 HKD
  expenses:food:restaurant         50.00 HKD
    ; eating: lunch ; activity: meal_with_friends ; duration: 1h
---ENTRY_END---
```

**Main Agent Parsing Logic:**

1. Parse each subagent output for `DATE`, `PAYEE`, `ACTION`, and the formatted entry
2. Collect all entries with `VALIDATION_STATUS: pass`
3. Warn on entries with `VALIDATION_STATUS: warn` (ambiguous payees, needing clarification)
4. Flag entries with `VALIDATION_STATUS: fail` (critical issues, need subagent retry or user input)
5. Sort all `pass` and `warn` entries chronologically by date
6. Insert into the target journal in order, replacing existing entries if `ACTION: edit*`
7. Run final validation and report results

**Subagent Responsibilities for Output:**

- Format the entry exactly as it should appear in the ledger file (with proper indentation and spacing)
- Set `VALIDATION_STATUS: pass` only if all rules are met (payee normalized, tags correct, deduplication checked)
- Set `VALIDATION_STATUS: warn` if there are minor issues that do not block entry (e.g., "Payee partially resolved, using close match")
- Set `VALIDATION_STATUS: fail` if entry cannot be created (e.g., "Mutually ambiguous payee, need clarification")
- List specific issues in `VALIDATION_ISSUES` for the main agent to review

## Transition Notes & Backward Compatibility

**For Existing Workflows:**

If you have existing requests or workflows that don't use subagents, they continue to work:

- Single-entry requests: Handled directly by the main agent (no change in behavior)
- Multi-entry requests NOT using subagents: Still work, but are less efficient (sequential processing instead of parallel)

**Migration to Subagent-Per-Entry (Recommended):**

For new multi-entry requests going forward:

1. User provides batch of 2+ transactions
2. Main agent immediately creates a todo list and invokes subagents
3. This is now the **preferred approach** for scalability and clarity

**Why This Matters:**

- The subagent-per-entry model scales to 10, 50, or 100 entries without degrading
- Clear separation of concerns (each subagent focuses on ONE transaction)
- Main agent orchestrates, validates, and merges results
- If one entry has issues, others are not blocked (can be retried independently)

---

**Important: Do not hesitate to ask the user for clarification if:**

- The transaction source data is ambiguous (multiple possible payees, unclear amount, etc.)
- The target ledger file is unclear or doesn't exist
- The transaction type classification is ambiguous (is this food? lending? currency exchange?)
- There are conflicting rules from multiple theme files

**Ambiguity Handling in Multi-Entry Workflow:**

If a subagent encounters ambiguity:

1. Set `VALIDATION_STATUS: warn` or `fail`
2. List the ambiguity clearly in `VALIDATION_ISSUES`
3. Return to the main agent, which will either:
   - Ask the user for clarification, or
   - Flag the entry for manual review, or
   - Move forward if it's a low-risk warning

**Do NOT guess or make assumptions.** The ledger is a precise financial record—ambiguous entries undermine trust and tracking.

## Mapping and Translation Files

- [payee_mappings.yml](./payee_mappings.yml) — For mapping payee aliases, translations, and alternate names to canonical payee names. All mapping values MUST be YAML sequences (lists). Use one-element lists for unambiguous one-to-one mappings; use multi-element lists only when a single alias may legitimately refer to multiple canonical payees. When a list contains multiple candidates, disambiguate using context (store/branch ID, receipt tokens, item categories, locality); if context is insufficient, prompt for clarification and update the mapping with a more-specific key. This is **not** for UUID mapping or ID mapping. Always use this file to normalize payee names in transactions.
- [id_mappings.yml](./id_mappings.yml) — For formatting and mapping transaction/receipt IDs (e.g., which identifiers to include in the payee line, and their order/format). This is **not** for payee name normalization or UUID mapping.
- [food_translations.yml](./food_translations.yml) — For translating food/drink item names only.
- [private.yaml](../../../private.yaml) — For mapping payee names or people to UUIDs for privacy and entity registration. This is **not** for payee name normalization or ID mapping.

**Clarification:**

- Use `payee_mappings.yml` to map any payee alias, translation, or alternate name to the canonical payee name for all transaction entries. Never use untranslated or unnormalized payee names if a mapping exists.
- Use `private.yaml` only for UUID/entity mapping (e.g., friends, people, or confidential payees), not for payee name normalization or ID mapping.
- Use `id_mappings.yml` only for specifying which transaction/receipt IDs to include in the payee line, and their order/format, not for payee name normalization or UUID mapping.

Each file contains its own documentation and must be referenced for correct transaction entry. Update only with explicit user approval.

## Validation Reminder

**Note:** See `.agents/instructions/developer-workflows.instructions.md` for canonical script usage and working-directory rules.

Example:

```powershell
python -m format   # set cwd to scripts/
python -m check    # set cwd to scripts/
```

## Lessons & Continuous Learning

See `./lessons.md` for the active queue of current learnings. **For consolidated insights across all skills (replaces scattered lessons.md), see `.agents/instructions/continuous-learning.instructions.md`** — a unified guide to lessons, anti-patterns, and best practices discovered through repeated use.

For guidelines on integrating new lessons:

1. Add new findings to `./lessons.md` with date and short description
2. Integrate into the relevant canonical file (SKILL.md, theme file, examples.md, or mapping YAML)
3. Replace detailed lesson with a one-line pointer in `./lessons.md`
4. Keep this file concise (single-screen)

Consolidated cross-theme reminders (key rules discovered through use):

- Use the most specific account and contextually correct tags (`activity:`, `eating:`, etc.), and keep tag order/format aligned with `.agents/instructions/transaction-format.instructions.md`.
- If a transaction uses `liabilities:credit cards:` for the payment posting, mark the purchase transaction pending with `!` to signal the outstanding liability to the issuer.
- Always resolve payee + identifiers via `private.yaml` (UUIDs), `payee_mappings.yml` (name normalization), and `id_mappings.yml` (identifier order/regex).
- For food entries: modifiers must be inline in `food_or_drink:` values, routine price reductions should be reflected in item amounts, and explicit receipt-printed voucher or cash-card discounts should be recorded as a separate negative expense posting with a `food_or_drink:` comment. Ordering-method descriptors are metadata (not posting lines).
- If start/end timestamps are both present, add `duration:` and update existing entries rather than creating duplicates for end-time rows.
- Never use Octopus eDDA debtor-reference tokens for matching or mapping; match with FRN/transfer ids + timestamp + amount.
- Keep journals strictly chronological and fix structural issues (misplaced transactions, duplicate includes) before finishing.
- Keep outputs non-confidential: no leaked personal ids, Octopus numbers, employee names, or attachment filenames.
- Do not rely on the runtime memory store for workflow rules. Instead, persist rule updates directly in skill or instruction files (`.agents/skills/*/SKILL.md`, `.agents/instructions/*.instructions.md`, `AGENTS.md`) so the repository is self-documenting and reviewers can audit behavior.

**Recent lessons (integrated into canonical files, see continuous-learning for details):**

- 2026-04-19 — TamJai SamGor voucher discount pattern: separate negative expense posting for receipt-printed voucher usage, plus final credit-card liability payment.
- 2026-04-08 — Saizeriya & American Diner receipt header ID conventions → `food_transactions.md`, `examples.md`, `id_mappings.yml`
- 2026-03-10 — Tag formatting & language consistency → `food_transactions.md`, `examples.md`
- 2026-02-24 — Complimentary items & modifier splitting → `food_transactions.md`, `examples.md`, `SKILL.md`

### Status markers

Use status markers only for lending/borrowing transactions. See `lending_borrowing_transactions.md` and `.agents/instructions/transaction-format.instructions.md` for canonical rules and examples.

#### Shared Expense and Repayment Pattern (Critical)

When a friend pays for a group meal or shared expense, always update the original transaction to:

- Itemize all expenses as usual.
- Add `equity:friends:<uuid>` lines for each friend's share (including yourself if you are not the payer).
- Add negative expense lines for the total of others' shares to offset the full amount.
- Add a `liabilities:loans:friends:<uuid>` line for the total amount paid by the friend for others, with a balance assertion (e.g., `= -654.00 HKD`).
- Annotate lines for clarity (e.g., `; paid by friend, other's share`).

When you repay the friend:

- Add a transaction debiting your asset account and crediting the liability, asserting the balance to zero (e.g., `= 0.00 HKD`).
- Include all relevant reference numbers and tags.

For new friends without UUIDs:

- Use a placeholder and update the prelude and transactions once the UUID is assigned.

This pattern ensures correct tracking of group expenses, liabilities, and repayments, and should be followed for all shared expense and group payment situations. See also the lending/borrowing theme file for more details.

## Required Reference Files (Must Always Be Read and Remembered)

**For Main Agent (All Workflows):**

- Always read and remember:
  1. `.agents/skills/add-transactions/SKILL.md` (this file)
  2. `private.yaml` (for UUID mappings)
  3. `preludes/index.journal` and all `preludes/**/*.journal` (account/payee definitions)
  4. All mapping/translation files: `payee_mappings.yml`, `id_mappings.yml`, `food_translations.yml`
  5. All theme/aspect markdown files: `food_transactions.md`, `lending_borrowing_transactions.md`, `currency_conversion_transactions.md`, etc.

**For Subagents (Multi-Entry Workflow Only):**

- Each subagent receives explicit instructions that include:
  1. The full path to this SKILL.md file (must be read first)
  2. The specific transaction source data to process
  3. The target ledger file path
  4. Permission/instructions to read `private.yaml`, all mapping YAMLs, and theme files
  5. Links to relevant theme files for that transaction type
  6. Clear directive: "Follow all rules in SKILL.md, theme files, and mappings before committing changes"

**Critical Subagent Requirement:**

- **Every subagent MUST read the full SKILL.md file before doing any work.** This ensures all subagents follow the same rules, regard theme files as authoritative, and apply consistent payee/tag/account logic.

**Main Agent Post-Subagent Responsibility:**

- After all subagents complete, the main agent must run final validation and formatting. **Do NOT assume subagents format or validate their own entries.** The main agent handles the coordinated `bun run format && bun run check` step.

---

## Quick Validation Checklist (Pre-Commit)

Use this checklist after all edits are merged:

- [ ] No duplicate transaction timestamps, IDs, or amounts within the same month
- [ ] All entries are in strict chronological order (by date, then by order in file)
- [ ] All payee names are normalized via `payee_mappings.yml`
- [ ] All tags follow correct format (`activity:`, `eating:`, `eating_method:`, etc.)
- [ ] All account names match the prelude definitions (no typos)
- [ ] Status markers (`!`, `*`) are used only for lending/borrowing transactions
- [ ] Ledger file includes prelude files at the top
- [ ] No confidential data leaked (personal IDs, Octopus card numbers, employee names, etc.)
- [ ] `bun run check` passes with no errors or unbalanced entries
- [ ] `bun run format` runs without changes (formatting is consistent)
