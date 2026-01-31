---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill (2026-01-26 Consolidated Edition)

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**When transcribing, mapping, or editing transactions, use the todo list tool to break down the process into actionable steps.**

Mark each step as in-progress and completed, and update the todo list after each change to ensure all transaction entry and mapping steps are completed and nothing is missed.

> **⚠️ This skill is extremely difficult to master.**
>
> Adding transactions in this system involves many complex, context-dependent procedures and rules that vary by transaction type, payee, and data source. Mastery requires deep familiarity with all conventions, mappings, and edge cases. **Always follow the documented procedures and update the theme/aspect files as you learn.**
>
> **Whenever the user provides feedback or corrections, update the relevant theme/aspect file first, then the main file if needed.**
>
> **Continuous improvement is required:** treat every feedback as an opportunity to refine both your process and the skill documentation.

## Table of Contents & Theme Files

This skill is organized into theme/aspect-specific files. Always consult all relevant files, as a single transaction may involve multiple aspects:

### Theme/Aspect Rule Files

- [Food Transactions](./food_transactions.md)
- [Lending & Borrowing Transactions](./lending_borrowing_transactions.md)
- [Currency Conversion Transactions](./currency_conversion_transactions.md)
- [Payee and ID Mapping Rules](./payee_id_mapping_rules.md)
- [Posting and Tag Validation Rules](./posting_tag_rules.md)
- [Entity Registration Rules](./entity_registration_rules.md)
- [Image and Attachment Handling Rules](./image_attachment_rules.md)

Refer to these files for detailed rules, clarifications, and examples. Do not duplicate their content here.

## Mapping and Translation Files

- [payee_mappings.yml](./payee_mappings.yml)
- [id_mappings.yml](./id_mappings.yml)
- [food_translations.yml](./food_translations.yml)

Each file contains its own documentation and must be referenced for correct transaction entry. Update only with explicit user approval.

## Validation Reminder

**Script commands: Always run from the `scripts/` directory**

- For all Python scripts (e.g., `python -m check`, `python -m format`, `python -m depreciate`, `python -m shift`, `python -m replace`, `python -m encrypt`, `python -m decrypt`), **always set the working directory to `scripts/` using the tool's `cwd` parameter**. This applies to both direct Python invocations and all script wrappers (e.g., `./check`, `check.bat`, etc.).
- **Never run scripts from the root directory or any other location.** Running from the wrong directory will cause include and file discovery errors.
- Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.

**Critical:** If you run any script or wrapper from the wrong directory, you will encounter include errors, missing file errors, or incorrect results. Always double-check the working directory before running any script command.

Example:

```powershell
python -m format   # set cwd to scripts/
python -m check    # set cwd to scripts/
```

## Lessons Learned & Continuous Improvement

### 2026-01-28 (AI skill update, revised)

- **Payee and ID Mapping:**
  - Always check `private.yaml` for payee mappings. If the merchant name or a similar entry is found, use the corresponding UUID as the payee. If not found, use the merchant name.
  - For receipt/transaction identifiers: Prepend all available identifiers (order number, receipt number, etc.) in parentheses at the start of the payee line. If an `id_mappings.yml` exists, follow its mapping for identifier formatting and order. If the payee is not in the mapping, update the mapping simultaneously when adding the entry.
- **Food/Drink Tagging:**
  - Always split each food or drink item into a separate `food_or_drink:` tag. Do not combine multiple items into a single tag. Do not add translations unless required by convention. Maintain the order of items as they appear on the receipt.
- **Account and Tag Selection:**
  - Use the most specific and correct account (e.g., `dining`, `snacks`, etc.) as per the context and conventions. Do not default to a generic or similar account if a more precise one is available.
  - Use the correct `eating:` tag (`lunch`, `afternoon tea`, etc.) based on the actual meal or context from the receipt.
  - Align columns and tags for readability. Follow the tag order and formatting conventions strictly as per the project’s transaction-format instructions.
- **Identifiers and Traceability:**
  - Always include all available receipt, order, or transaction identifiers in the payee line for traceability, following the mapping rules above.
- **Generalized Learnings:**
  - Always cross-reference `private.yaml` and `id_mappings.yml` before assigning payees or formatting identifiers.
  - Never assume a payee UUID—always verify or create the mapping as needed.
  - Split all food/drink items into individual tags and maintain their order.
  - Use the most contextually accurate account and tags.
  - Maintain strict formatting and tag order for consistency and readability.

Other previous learnings remain in effect:

- **OCR accuracy:** When transcribing from receipts or images, always stick to the recognized characters for item names and details. Only make corrections if the OCR result is obviously wrong. Do not over-correct or invent new names.
- **YAML doc comment placement:** When adding new mappings to YAML files (such as id_mappings.yml), always place new content after the documentation comment at the top of the file, not before.
- **YAML regex escaping:** When writing regex strings in YAML files (such as id_mappings.yml), always escape backslashes (e.g., use `\\d` instead of `\d`).
- **ID mapping location:** Never put payee-specific ID mapping rules in this SKILL.md file. All such rules must be placed only in id_mappings.yml, after the documentation comment.
- **Taste ID mapping:** For Taste, always use the 17-digit numeric ID and the 24-character transaction ID, in that order, if both are present. See [payee_id_mapping_rules.md](./payee_id_mapping_rules.md) for details and regex.
- **Hotpot/restaurant item multiplicity:** If a food or fee item is ordered more than once, record as `food_or_drink: <item> ×N` (with a space before `×`, no space after). Use the exact multiplicity as shown on the receipt.
- **Service charge and rounding translation:** When translating service fee and rounding, only keep the English translation (e.g., `10% service charge`, `rounding`), not the original Chinese. Do not duplicate both.
- **Tea/cover charge as fee:** If an item like "茶水$12/位" (tea per person) is present, record it as a fee, not as dining.
- **No extraneous comments:** Do not add unnecessary comments at the end of the transaction (e.g., receipt details, employee names, or explanations). Only include what is required by the format.
- **No employee names:** Never include employee or staff names from receipts in the journal.
- **Never leak Octopus numbers or personal IDs** in any transaction, mapping, or documentation. These must be treated as confidential and must not appear in journal entries, ID mappings, or skill documentation. Only use anonymized or mapped UUIDs where required.
- **Never leak attachment filenames or add an `attachment` tag** in any transaction. Do not reference image or file names in the journal.
- **Only one `include` line** for the prelude should appear at the top of each journal file. Remove any duplicates.
- **Always insert new transactions in strict chronological order**. Double-check placement to avoid out-of-order entries.
- When editing, always check for and correct structural errors (e.g., duplicate includes, misplaced transactions) before finishing.
- **Never trust the tool to insert at the correct location blindly.** Always check the file after any tool call that inserts or edits transactions to verify the actual insertion location. If the transaction is not in the intended place, move it manually to the correct chronological position.

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

Always read and remember:

1. `private.yaml`
2. `preludes/index.journal` and all `preludes/**/*.journal`
3. All mapping/translation files above
4. All theme/aspect markdown files above
