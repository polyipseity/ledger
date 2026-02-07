---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill (2026-02-01 Generalized Edition)

## Journal File Path Format

**Reminder:** All monthly journal files must be named and referenced as `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`). Do not omit the `ledger/` prefix when referring to journal files.

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Prefer `typing.Self` for methods that return the instance type (for example: `def clone(self) -> typing.Self:`); if supporting Python versions older than 3.11, use `typing_extensions.Self`. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. Avoid using `Any` or `Unknown` in type annotations; prefer explicit types, Protocols, or TypedDicts. Exception: `Any` or `Unknown` may be used only when there is a very strong, documented justification (for example, interfacing with untyped third-party libraries or representing truly dynamic/opaque data structures). When used, include an inline comment explaining the justification and a `# TODO` to refine the type later. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

> **⚠️ This skill is extremely difficult to master.**
>
> Adding transactions in this system involves many complex, context-dependent procedures and rules that vary by transaction type, payee, and data source. Mastery requires deep familiarity with all conventions, mappings, and edge cases. **Always follow the documented procedures and update the theme/aspect files as you learn.**
>
> **Whenever the user provides feedback or corrections, update the relevant theme/aspect file first, then the main file if needed.**
>
> **Continuous improvement is required:** treat every feedback as an opportunity to refine both your process and the skill documentation.

## Table of Contents & Theme Files

This skill is organized into theme/aspect-specific files. It also provides a general framework for automating the import, deduplication, and updating of highly-structured or machine-readable transactions from external sources (such as emails, app notifications, or data exports) into the hledger journal. Always consult all relevant files, as a single transaction may involve multiple aspects:

### Theme/Aspect Rule Files

- [Food Transactions](./food_transactions.md) — For all food, drink, and dining-related entries
- [Lending & Borrowing Transactions](./lending_borrowing_transactions.md) — For loans, repayments, and shared expenses
- [Currency Conversion Transactions](./currency_conversion_transactions.md) — For any transaction involving currency exchange
- [Platform Transaction & Payout Rules](./platform_payout_transactions.md) — For digital payment platforms (Stripe, PayPal, Square, Alipay, etc.), including both incoming transactions and payouts to bank accounts
- [Payee and ID Mapping Rules](./payee_id_mapping_rules.md) — For mapping payees and transaction identifiers
- [Posting and Tag Validation Rules](./posting_tag_rules.md) — For correct account, tag, and posting usage
- [Transport Reward Transactions](./transport_rewards.md) — For transit reward accrual patterns (Kowloon Motor Bus / Long Win Bus)
- [Entity Registration Rules](./entity_registration_rules.md) — For registering new payees, friends, or entities
- [Image and Attachment Handling Rules](./image_attachment_rules.md) — For handling receipt images or attachments
- [Specialized Transaction Import & Automation](./specialized_transaction_import.md) — For automating import of structured transactions (e.g., Octopus eDDA)
Refer to these files for detailed rules, clarifications, and examples. Do not duplicate their content here. The platform transaction & payout rules file generalizes patterns for Stripe and similar platforms, and should be consulted for any digital payment platform transaction or payout.

## Mapping and Translation Files

- [payee_mappings.yml](./payee_mappings.yml) — For mapping payee aliases, translations, and alternate names to canonical payee names. All mapping values MUST be YAML sequences (lists). Use one-element lists for unambiguous one-to-one mappings; use multi-element lists only when a single alias may legitimately refer to multiple canonical payees. When a list contains multiple candidates, disambiguate using context (store/branch ID, receipt tokens, item categories, locality); if context is insufficient, prompt for clarification and update the mapping with a more-specific key. This is **not** for UUID mapping or ID mapping. Always use this file to normalize payee names in transactions.
- [id_mappings.yml](./id_mappings.yml) — For formatting and mapping transaction/receipt IDs (e.g., which identifiers to include in the payee line, and their order/format). This is **not** for payee name normalization or UUID mapping.
- [food_translations.yml](./food_translations.yml) — For translating food/drink item names only.
- [private.yaml] — For mapping payee names or people to UUIDs for privacy and entity registration. This is **not** for payee name normalization or ID mapping.

**Clarification:**

- Use `payee_mappings.yml` to map any payee alias, translation, or alternate name to the canonical payee name for all transaction entries. Never use untranslated or unnormalized payee names if a mapping exists.
- Use `private.yaml` only for UUID/entity mapping (e.g., friends, people, or confidential payees), not for payee name normalization or ID mapping.
- Use `id_mappings.yml` only for specifying which transaction/receipt IDs to include in the payee line, and their order/format, not for payee name normalization or UUID mapping.

Each file contains its own documentation and must be referenced for correct transaction entry. Update only with explicit user approval.

## Validation Reminder

**Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical guidance — prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

Example:

```powershell
python -m format   # set cwd to scripts/
python -m check    # set cwd to scripts/
```

## Lessons Learned & Continuous Improvement

### 2026-02-01 (AI skill update, generalized)

- **Payee Mapping, UUID Mapping, and ID Mapping (Critical Distinction):**
  - **Payee mapping**: Always check `payee_mappings.yml` for payee aliases, translations, or alternate names. Mapping entries are always YAML sequences (lists). If a mapping list contains a single canonical name, use that name. If the list contains multiple candidates, attempt to disambiguate using contextual cues (store/branch ID, receipt tokens, item categories, locality, etc.). If context is insufficient to choose among the candidates, prompt for clarification and then update `payee_mappings.yml` with a more-specific key (for example, include branch/terminal codes). **Never use the untranslated or unnormalized payee name if a mapping exists.**
  - **UUID mapping**: Use `private.yaml` only for mapping payees or people to UUIDs for privacy or entity registration. This is for internal entity tracking, not for payee name normalization or ID mapping.
  - **ID mapping**: Use `id_mappings.yml` only to determine which transaction/receipt IDs to include in the payee line, and their order/format. This is not for payee name normalization or UUID mapping.
  - For receipt/transaction identifiers: Prepend only the identifiers specified by the payee's rule in `id_mappings.yml` (e.g., for KFC, only use (receipt_id, store_id)). If the payee is not in the mapping, update the mapping simultaneously when adding the entry.
  - When updating or adding a payee, UUID, or ID mapping, always update the relevant mapping file after the documentation comment, not before.
- **Food/Drink Tagging:**
  - Always split each food or drink item into a separate `food_or_drink:` tag. Do not combine multiple items into a single tag. **Never translate the food_or_drink value unless required by a specific mapping or convention.** Maintain the order of items as they appear on the receipt.
  - **Never place any itemization, discount, or similar tags (such as `food_or_drink:`, `discount:`, or item codes) in the transaction header.** These must always be placed in posting comments only, never in the header line. This applies to all item, discount, and similar tags, regardless of transaction type or payee. See `posting_tag_rules.md` for details.
  - For food/drink items, omit parenthetical descriptors or prefixes (e.g., omit (早) or 轉 if not part of the item name). For sub-items or substitutions, treat as separate items unless clearly a modifier.
  - When a receipt shows per-item prices, record each item as its own posting line with the item's amount and a `food_or_drink:` comment tag. Ensure the item postings sum exactly to the transaction total and include the payment posting (e.g., `assets:digital:Octopus cards:...`) as the final, negative total posting. Maintain the order of postings to match the receipt.
  - For drinks or items with modifiers (e.g., less ice, more milk), use the `+` syntax to combine the base item and modifiers (e.g., `food_or_drink: hot coffee + more milk`). **If a modifier appears on its own line after a beverage (for example: `food_or_drink: 奶茶` followed by `food_or_drink: 多奶`), combine them into `food_or_drink: 奶茶 + 多奶` and remove the standalone modifier tag.**
  - If a modifier is missing, check the receipt and add it to the tag as needed.
  - Timezone and duration: When a receipt contains both an order/print time and a separate settlement/transaction time, compute the ISO-8601 duration as the difference and add `duration:` to the transaction header (e.g., `duration: PT34M19S`). **Always include an explicit `timezone:` when specifying `time:` so duration computations are unambiguous.**
  - Payee mapping: Before using an untranslated payee name, check `private.yaml` for a UUID mapping and use the UUID as the payee if present; otherwise consult `payee_mappings.yml` for canonical names. Because mapping values are always lists, if the list contains multiple canonical candidates, disambiguate using contextual information; once the canonical payee is chosen, check `private.yaml` and use its UUID if present (the mapping file remains clear-text).
- **Account and Tag Selection:**
  - Use the most specific and correct account (e.g., `dining`, `snacks`, etc.) as per the context and conventions. Do not default to a generic or similar account if a more precise one is available.
  - Use the correct `eating:` tag (`lunch`, `afternoon tea`, etc.) based on the actual meal or context from the receipt.
  - Align columns and tags for readability. Follow the tag order and formatting conventions strictly as per the project’s transaction-format instructions.
- **Identifiers and Traceability:**
  - Always include only the identifiers specified by the payee's rule in `id_mappings.yml` in the payee line for traceability.
- **Generalized Learnings:**
  - Always cross-reference `private.yaml`, `payee_mappings.yml`, and `id_mappings.yml` before assigning payees or formatting identifiers.
  - Never assume a payee UUID—always verify or create the mapping as needed.
  - Split all food/drink items into individual tags and maintain their order, omitting non-item descriptors and using modifiers as appropriate.
  - Use the most contextually accurate account and tags.
  - Maintain strict formatting and tag order for consistency and readability.

### Status markers

Use status markers only for lending/borrowing transactions. See `lending_borrowing_transactions.md` and `.github/instructions/transaction-format.instructions.md` for canonical rules and examples.

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
- **Chronological:** Insert new transactions in strict chronological order (date, then time). See `.github/instructions/transaction-format.instructions.md` for canonical rules.
- When editing, always check for and correct structural errors (e.g., duplicate includes, misplaced transactions) before finishing.
- **Verify insertion location:** Do not rely blindly on tools to insert at the correct place—always check and correct placement manually if needed.

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
