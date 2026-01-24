<!-- markdownlint-disable MD013 -->

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
- **[git-commits.instructions.md](.github/instructions/git-commits.instructions.md)** - Repository commit/message conventions for agents and humans

Agent Skills for specialized workflows:

- **[.github/skills/add-transactions/](.github/skills/add-transactions/)** - Transcribe transactions from raw data with proper status markers and tagging
- **[.github/skills/add-octopus-transactions/](.github/skills/add-octopus-transactions/)** - Add missing Octopus card transactions from app history, identify missing transport transactions, add duration metadata, and record card reloads
- **[.github/skills/match-octopus-statement-transactions/](.github/skills/match-octopus-statement-transactions/)** - Match Octopus Wallet statement rows to journal transactions and update transaction datetimes (seconds-only updates are silent by default; non-typical changes reported).
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

- `python -m check` / `python -m format` - Validate and format journals
- Use repo-managed tooling via pnpm instead of global installs where possible:
  - `pnpm install` — install JS dev deps and run Python postinstall
  - `pnpm run hledger:check` — runs `scripts.check` (hledger validation)
  - `pnpm run hledger:format` — runs `scripts.format` (formats journals)
  - `pnpm run hledger:format:check` — check-only formatting
  - `pnpm run markdownlint` — markdown linting
  - `pnpm run markdownlint:fix` — auto-fix markdown lint issues (optional)
  - `pnpm run commitlint` — run commit message linting locally (Husky runs commitlint on commit-msg)
- `hledger close --migrate` - Generate monthly balances
- `python -m encrypt` / `python -m decrypt` - Manage confidential data

## Quick Start

- **Adding transactions**: [add-transactions](./skills/add-transactions/) skill
- **Adding Octopus transactions**: [add-octopus-transactions](./skills/add-octopus-transactions/) skill
- **Monthly migration**: [monthly-migration](./skills/monthly-migration/) skill
- **Editing journals**: [edit-journals](./skills/edit-journals/) skill
- **Validating**: [validate-journals](./skills/validate-journals/) skill
- **Security**: See [security.instructions.md](.github/instructions/security.instructions.md)
- **Pre-commit**: See [common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md). Agents should run `pnpm install` and `pnpm run prepare` to enable Husky hooks locally.

## VS Code setup

To ensure AGENTS.md and instruction files are applied in chat:

- Enable support for AGENTS.md: set `chat.useAgentsMdFile` to true in VS Code settings
- We use a single root AGENTS.md (no per-folder AGENTS.md files). Leave `chat.useNestedAgentsMdFiles` disabled.
- Ensure instruction files are discoverable: keep `.instructions.md` files under `.github/instructions/`
- For conditional instructions, use YAML frontmatter `applyTo` in `.instructions.md` (for example: `applyTo: "**/*.journal"`)

Formatting setup (Markdown):

- `.editorconfig` sets UTF-8, final newlines, trailing whitespace trim, and 2-space indents for Markdown (80 char line length)
- `.markdownlint.jsonc` uses markdownlint defaults
- Use markdownlint (VS Code extension). For CLI: prefer using pnpm and the repository script. Run:

```powershell
pnpm install
pnpm run markdownlint
pnpm run markdownlint:fix   # optional: auto-fix issues
```

Or use `./scripts/format-md.sh` / `./scripts/format-md.bat`.

- Always format Markdown files before committing (include in pre-commit workflow)

Tip: Use “Chat: Configure Instructions” from the Command Palette to view which instruction files are active and verify they’re included in chat context.
