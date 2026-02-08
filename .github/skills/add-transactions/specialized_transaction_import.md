# Specialized Transaction Import & Automation

This document describes the general workflow and best practices for automating the import, deduplication, and updating of highly-structured or machine-readable transactions from external sources (such as emails, app notifications, or data exports) into the hledger journal. It provides a framework for handling any specialized transaction type, with a detailed example for Octopus eDDA top-up transactions.

## General Workflow for Specialized Transaction Import

1. **Source Identification**
    - Identify the external source (e.g., email, app, CSV export) and the transaction type to be automated.
    - Ensure the source provides sufficient metadata for deduplication and correct journal entry.

2. **Data Extraction**
    - Parse the source to extract all relevant transaction fields:
        - Reference/transaction IDs
        - Date and time
        - Amount and currency
        - Account identifiers (e.g., card, wallet, bank)
        - Any additional metadata required for correct posting and tagging
    - Normalize extracted data to match hledger conventions and project standards.

3. **Deduplication & Update**
    - Search the relevant monthly journal (using the full ledger file path with `ledger/` prefix) for a transaction matching the extracted unique identifiers (e.g., reference ID, date, amount).
    - If a matching transaction exists:
        - Update its metadata (payee line, tags, IDs) to conform to the standard format for this transaction type.
        - If the transaction is already correct, no update is needed.
    - If no matching transaction exists:
        - Insert a new transaction at the correct chronological position, using the standard format and all extracted metadata.

4. **Formatting and Validation**
    - **Note:** Insert transactions in strict chronological order; see `.github/instructions/transaction-format.instructions.md` for canonical rules.
    - Use the correct account names and UUIDs as per project conventions.
    - Format all tags and columns according to the repository’s transaction-format and editing-guidelines.
    - Always validate and format the journal file after changes.

5. **Anti-Patterns**
    - Do not add duplicate transactions for the same unique identifier.
    - **Note:** Do not insert transactions out of chronological order; see `.github/instructions/transaction-format.instructions.md` for details.
    - Do not omit required metadata or tags.
    - Do not use incorrect or generic account names.
    - Do not modify unrelated transactions.

## Example: Octopus eDDA Top-Up Transactions

**Examples:** See `./examples.md` for the Octopus eDDA import worked examples (Pass 1: update existing; Pass 2: add new transaction).

**Summary workflow:** extract transaction data, search/deduplicate (update if matching), or insert a new transaction at the correct chronological position, then run `pnpm run format` and `pnpm run check` to validate. Prefer updates over duplicates; follow privacy and mapping rules in `payee_mappings.yml`, `id_mappings.yml`, and `private.yaml`.

### Related Skills & References

- [edit-journals](../edit-journals/SKILL.md) — General journal editing best practices
- [validate-journals](../validate-journals/SKILL.md) — Validation and formatting
- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md)
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md)
