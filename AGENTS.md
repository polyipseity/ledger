<!-- markdownlint-disable MD013 MD036 -->

# Personal Ledger Project - Instructions

**IMPORTANT: This documentation must not contain confidential information.** All examples should use non-confidential placeholders (UUIDs, generic names, example amounts) instead of real account numbers, personal names, locations, or actual financial data. Confidential mappings are stored in the encrypted `private.yaml.gpg` file only.

## Project Overview

Personal accounting system using **hledger** (plain text accounting) to track financial transactions organized by year/month.

## Documentation Structure

Core instructions (`.github/instructions/`):

- **architecture** - File hierarchy, include patterns
- **transaction-format** - hledger syntax, tags, patterns
- **account-hierarchy** - All account types (50+ accounts)
- **developer-workflows** - Scripts, Python patterns, testing
- **common-workflows** - Practical task guides
- **editing-guidelines** - Best practices for journal editing
- **security** - Encryption, UUID privacy
- **alternatives-journal** - Illiquid vs liquid asset tracking
- **dependencies** - Required software (hledger, Python, GPG)
- **git-commits** - Commit conventions

Agent Skills (`.github/skills/`):

- **add-transactions** - Transcribe transactions from raw data
- **add-octopus-transactions** - Add missing Octopus card transactions
- **match-octopus-statement-transactions** - Match statement rows to journal transactions
- **monthly-migration** - Monthly close using hledger --migrate
- **edit-journals** - Edit journals with best practices
- **validate-journals** - Validate and format before commit

## Key Concepts

**Status markers**: `!` = pending (awaiting confirmation), `*` = cleared (verified), no marker = normal

**Journal types**: `self.journal` (liquid assets), `self.alternatives.journal` (illiquid/crypto)

**Essential commands**:

- `python -m check` / `python -m format` - Validate/format journals
- `pnpm run hledger:check` / `pnpm run hledger:format` - Alternative via pnpm
- `hledger close --migrate` - Monthly migration
- `python -m encrypt` / `python -m decrypt` - Confidential data

## Quick Start

Skills: [add-transactions](.github/skills/add-transactions/), [add-octopus-transactions](.github/skills/add-octopus-transactions/), [monthly-migration](.github/skills/monthly-migration/), [edit-journals](.github/skills/edit-journals/), [validate-journals](.github/skills/validate-journals/)

Security: [security.instructions.md](.github/instructions/security.instructions.md) | Pre-commit: [common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md)

## VS Code Setup

**Chat configuration**: Enable `chat.useAgentsMdFile` in settings. Leave `chat.useNestedAgentsMdFiles` disabled (single root AGENTS.md). Use "Chat: Configure Instructions" to verify active files.

**Markdown formatting**: Use `.editorconfig` (UTF-8, 2-space indent) and `.markdownlint.jsonc`. Format via VS Code extension or CLI (`pnpm run markdownlint:fix`). Always format before commit.

**Agent commits**: Agents and automation (including bots and assistants) MUST follow the repository's Git commit conventions described in `.github/instructions/git-commits.instructions.md`. Before making commits, agents must run the repository formatting and validation steps and use Conventional Commits for commit headers.

When an agent has a motivation or rationale for a non-ledger change, include that rationale in the commit body. Do NOT include bodies for `ledger(...)` transaction commits — those must remain a single-line header to stay machine-parseable.
