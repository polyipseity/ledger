# Personal Ledger Project - Instructions

**IMPORTANT: This documentation must not contain confidential information.** All examples should use non-confidential placeholders (UUIDs, generic names, example amounts) instead of real account numbers, personal names, locations, or actual financial data. Confidential mappings are stored in the encrypted `private.yaml.gpg` file only.

## Project Overview

This is a personal accounting/bookkeeping system using **hledger** (plain text accounting). The ledger files track financial transactions, assets, liabilities, expenses, and revenues organized by year and month.

## Documentation Structure

All documentation is organized into `.instructions.md` files in the `.github/instructions/` folder:

- **[architecture.instructions.md](.github/instructions/architecture.instructions.md)** - Project structure, file hierarchy, include patterns
- **[transaction-format.instructions.md](.github/instructions/transaction-format.instructions.md)** - hledger format, transaction structure, tags, and patterns
- **[account-hierarchy.instructions.md](.github/instructions/account-hierarchy.instructions.md)** - Complete documentation of all account types and their purposes
- **[developer-workflows.instructions.md](.github/instructions/developer-workflows.instructions.md)** - Scripts, Python patterns, code conventions, testing & validation
- **[common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md)** - Practical task guides and examples
- **[editing-guidelines.instructions.md](.github/instructions/editing-guidelines.instructions.md)** - Best practices for journal editing and formatting
- **[security.instructions.md](.github/instructions/security.instructions.md)** - private.yaml encryption/decryption, confidentiality requirements
- **[alternatives-journal.instructions.md](.github/instructions/alternatives-journal.instructions.md)** - Tracking illiquid assets vs liquid rewards
- **[dependencies.instructions.md](.github/instructions/dependencies.instructions.md)** - Required software and their roles

Agent Skills for specialized workflows:
- **[.github/skills/add-transactions/](.github/skills/add-transactions/)** - Transcribe transactions from raw data with proper status markers and tagging
- **[.github/skills/monthly-migration/](.github/skills/monthly-migration/)** - Perform monthly journal migration using hledger close --migrate
- **[.github/skills/edit-journals/](.github/skills/edit-journals/)** - Edit journals following best practices and conventions
- **[.github/skills/validate-journals/](.github/skills/validate-journals/)** - Validate and format journals before committing

## Key Concepts

### Transaction Status Markers
- `!` (exclamation mark) = pending/unclear - awaiting confirmation or requires follow-up action
- `*` (asterisk) = cleared - transaction complete and verified
- No marker = normal standard transaction

### Journal Types
- **self.journal**: Main ledger for liquid assets and financial transactions
- **self.alternatives.journal**: Alternative scenarios and illiquid holdings (crypto, non-transferable investments, etc.)

### Essential Commands
- `python -m check` - Validate all journals
- `python -m format` - Auto-format all journals
- `hledger close --migrate` - Generate monthly closing/opening balances
- `python -m encrypt` - Encrypt private data
- `python -m decrypt` - Decrypt private data for editing

## Quick Reference

**Adding transactions**: Follow the add-transactions skill for step-by-step guidance on entering transactions from raw data.

**Monthly migration**: Use the monthly-migration skill for the journal migration process.

**Editing journals**: Use the edit-journals skill for best practices and validation procedures.

**Validating changes**: Use the validate-journals skill for checking and formatting journals.

**Security**: Always follow security.instructions.md before working with confidential data. Never commit unencrypted `private.yaml` to version control - only `private.yaml.gpg` should be tracked.

## File Organization

```
ledger/
  index.journal              # Root includes self.journal and self.alternatives.journal
  self.journal              # Includes all yearly journals
  self.alternatives.journal # Includes all yearly alternatives journals
  2024/
    self.journal            # Yearly include file
    2024-01/
      self.journal          # Monthly transactions
    2024-02/
      self.journal
    ...
  2025/
    ...

preludes/
  self.journal              # Global account, commodity, payee, tag definitions
  self.alternatives.journal # Alternative scenario commodity definitions
```

## Pre-Commit Workflow

Before committing changes:

1. `python -m check` - Validate all journals
2. `python -m format` - Auto-format all journals
3. `python -m encrypt` - If you edited private.yaml
4. `git status` and `git diff` - Review changes
5. `git commit -S -m "Description of changes"` - Commit with signature

## VS Code setup

To ensure AGENTS.md and instruction files are applied in chat:

- Enable support for AGENTS.md: set `chat.useAgentsMdFile` to true in VS Code settings
- We use a single root AGENTS.md (no per-folder AGENTS.md files). Leave `chat.useNestedAgentsMdFiles` disabled.
- Ensure instruction files are discoverable: keep `.instructions.md` files under `.github/instructions/`
- For conditional instructions, use YAML frontmatter `applyTo` in `.instructions.md` (for example: `applyTo: "**/*.journal"`)

Tip: Use “Chat: Configure Instructions” from the Command Palette to view which instruction files are active and verify they’re included in chat context.
