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
    - Ensure the transaction is inserted in strict chronological order (by date and time).
    - Use the correct account names and UUIDs as per project conventions.
    - Format all tags and columns according to the repository’s transaction-format and editing-guidelines.
    - Always validate and format the journal file after changes.

5. **Anti-Patterns**
    - Do not add duplicate transactions for the same unique identifier.
    - Do not insert transactions out of chronological order.
    - Do not omit required metadata or tags.
    - Do not use incorrect or generic account names.
    - Do not modify unrelated transactions.

## Example: Octopus eDDA Top-Up Transactions

### Purpose

Automate the import and updating of Octopus eDDA (Electronic Direct Debit Authorisation) top-up transactions from email notifications into the hledger journal.

### Input

- A list of email attachments or screenshots, each containing exactly one Octopus eDDA transaction notification.

### Example Workflow

1. **Extract Transaction Data**
    - Parse each email attachment to extract:
        - Reference ID (e.g., C1K62243986)
        - Date and time of transaction
        - Amount and currency
        - Octopus wallet/card identifiers (if present)
        - Bank account information (if present)
        - Any additional transaction IDs (e.g., FRN..., OCTOPUS...)
    - Normalize all extracted data to match hledger conventions.
2. **Check for Existing Transaction**
    - Search the relevant monthly journal for a transaction matching the extracted reference ID, date, and amount.
    - If a matching transaction exists, update its metadata to conform to the standard format:
        - Payee line: (Reference ID, FRN..., OCTOPUS...) self  ; activity: transfer, time: HH:MM, timezone: UTC+08:00, via: eDDA
        - Ensure all relevant IDs and tags are present and correct.
    - If no matching transaction exists, insert a new transaction at the correct chronological position, using the standard format and all extracted metadata.
3. **Formatting and Validation**
    - Ensure the transaction is inserted in strict chronological order (by date and time).
    - Use the correct account names and UUIDs for Octopus and bank accounts.
    - Format all tags and columns according to the repository’s transaction-format and editing-guidelines.
    - Always validate and format the journal file after changes.

### Output

- The monthly journal is updated with the new or corrected Octopus eDDA transaction(s), fully formatted and validated.
- **Status markers (`!` for pending, `*` for cleared) must NOT be used for repayment transactions:** Only use status markers for the original pending lending/borrowing transaction (see SKILL.md and lending_borrowing_transactions.md). Repayment transactions must NOT have a status marker. If you see a status marker in any automated import, specialized, or repayment transaction, it is an error and must be corrected.

### Related Skills & References

- [edit-journals](../edit-journals/SKILL.md) — General journal editing best practices
- [validate-journals](../validate-journals/SKILL.md) — Validation and formatting
- [Transaction Format Conventions](../../instructions/transaction-format.instructions.md)
- [Editing Guidelines](../../instructions/editing-guidelines.instructions.md)
