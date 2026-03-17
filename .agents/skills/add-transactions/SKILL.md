---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill — Summary

Purpose: Import and normalize transactions from receipts, statements, and structured sources into monthly journals.

Core guidance:

- Use full ledger paths (e.g., `ledger/2024/2024-01/self.journal`) and insert transactions in strict chronological order; see `.agents/instructions/transaction-format.instructions.md`.
- Use the Todo List Tool for multi-step tasks and follow `AGENTS.md` workflow rules; see `.agents/instructions/agent-quickstart.instructions.md` for a concise command checklist.
- Use canonical scripts for formatting/validation (`bun run format` then `bun run check`); see `.agents/instructions/developer-workflows.instructions.md`.
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

## Lessons & Continuous Improvements

See `./lessons.md` for the active queue and integration pointers. This file should contain only short, unresolved notes. After integrating a lesson into a canonical file (`SKILL.md`, a theme file, or `examples.md`), replace that lesson with a one-line pointer and remove detailed duplicated text.

Consolidated cross-theme reminders:

- Use the most specific account and contextually correct tags (`activity:`, `eating:`, etc.), and keep tag order/format aligned with `.agents/instructions/transaction-format.instructions.md`.
- Always resolve payee + identifiers via `private.yaml` (UUIDs), `payee_mappings.yml` (name normalization), and `id_mappings.yml` (identifier order/regex).
- For food entries: modifiers must be inline in `food_or_drink:` values, routine discounts should be reflected in item prices (not separate negative discount postings), and ordering-method descriptors are metadata (not posting lines).
- If start/end timestamps are both present, add `duration:` and update existing entries rather than creating duplicates for end-time rows.
- Never use Octopus eDDA debtor-reference tokens for matching or mapping; match with FRN/transfer ids + timestamp + amount.
- Keep journals strictly chronological and fix structural issues (misplaced transactions, duplicate includes) before finishing.
- Keep outputs non-confidential: no leaked personal ids, Octopus numbers, employee names, or attachment filenames.

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

Always read and remember:

1. `private.yaml`
2. `preludes/index.journal` and all `preludes/**/*.journal`
3. All mapping/translation files above
4. All theme/aspect markdown files above
