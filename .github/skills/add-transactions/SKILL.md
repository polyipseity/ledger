---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill — Summary

Purpose: Import and normalize transactions from receipts, statements, and structured sources into monthly journals.

Core guidance:

- Use full ledger paths (e.g., `ledger/2024/2024-01/self.journal`) and insert transactions in strict chronological order; see `.github/instructions/transaction-format.instructions.md`.
- Use the Todo List Tool for multi-step tasks and follow `AGENTS.md` workflow rules; see `.github/instructions/agent-quickstart.instructions.md` for a concise command checklist.
- Use canonical scripts for formatting/validation (`pnpm run format` then `pnpm run check`); see `.github/instructions/developer-workflows.instructions.md`.
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

Refer to each theme file for detailed rules; for canonical worked examples and edge cases see `./examples.md`. For quick definitions and key terms, see `.github/instructions/agent-glossary.instructions.md`.

Canonical rule locations (quick map):

- Payee mapping & ID rules: `payee_id_mapping_rules.md` and `id_mappings.yml`
- Food/drinks tagging and translations: `food_transactions.md` and `food_translations.yml`
- Posting & tag validation: `posting_tag_rules.md`
- Lending/borrowing and status markers: `lending_borrowing_transactions.md`
- Specialized imports and Octopus heuristics: `specialized_transaction_import.md` and `examples.md`

If a lesson in `lessons.md` needs integration, add it to the relevant file above and replace the lesson entry with a one-line pointer.

Refer to each theme file for detailed rules, examples, and test expectations. For quick definitions and key terms, see `.github/instructions/agent-glossary.instructions.md`.

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

**Note:** See `.github/instructions/developer-workflows.instructions.md` for canonical script usage and working-directory rules.

Example:

```powershell
python -m format   # set cwd to scripts/
python -m check    # set cwd to scripts/
```

## Lessons & Continuous Improvements

See `./lessons.md` for consolidated, actionable lessons and `./examples.md` for canonical worked examples and edge cases. If a `lessons.md` entry needs integration into this SKILL, `examples.md`, or a theme file, follow the integration-first process described in `./lessons.md` and run `pnpm run format` and `pnpm run test` afterwards.

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
**Note:** For chronological ordering rules, see `.github/instructions/transaction-format.instructions.md`.
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
