---
name: add-transactions
description: Transcribe transactions from source documents into the hledger ledger. Handles raw data (receipts, invoices, bank statements, OCR text) with proper status markers, tagging, and account registration.
---

# Add Transactions Skill (2026-01-26 Consolidated Edition)

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

## Required Reference Files (Must Always Be Read and Remembered)

Always read and remember:

1. `private.yaml`
2. `preludes/index.journal` and all `preludes/**/*.journal`
3. All mapping/translation files above
4. All theme/aspect markdown files above
