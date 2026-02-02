<!-- markdownlint-disable MD013 MD036 -->

# Personal Ledger Project - Instructions

**IMPORTANT: This documentation must not contain confidential information.** All examples should use non-confidential placeholders (UUIDs, generic names, example amounts) instead of real account numbers, personal names, locations, or actual financial data. Confidential mappings are stored in the encrypted `private.yaml.gpg` file only.

## 🚩 Agent Workflow Reminders

**1. When the user explicitly asks to use a skill, before thinking or taking any action, the agent must read the corresponding skill file in full.**

**2. Use the Todo List Tool for all multi-step or complex tasks.**
    - Plan actionable steps before starting
    - Mark each step as in-progress and completed as you go
    - Review and update the todo list after each action
    - Ensure no steps are missed or left ambiguous

These steps are critical for agent reliability and maintaining a clear record of progress.

## Project Overview

Personal accounting system using **hledger** (plain text accounting) to track financial transactions organized by year/month.

**Journal file path format:** All journal files are located under the `ledger/` directory, with the format `ledger/[year]/[year]-[month]/[name].journal` (e.g., `ledger/2024/2024-01/self.journal`).

## Documentation Structure

Core instructions (`.github/instructions/`):

- [architecture.instructions.md](.github/instructions/architecture.instructions.md) – Details the ledger file hierarchy, include patterns, and organizational structure for all journal files, ensuring consistency and discoverability across the system.
- [transaction-format.instructions.md](.github/instructions/transaction-format.instructions.md) – Comprehensive guide to hledger transaction syntax, required and optional tags, formatting conventions, and pattern usage for accurate and readable journal entries.
- [account-hierarchy.instructions.md](.github/instructions/account-hierarchy.instructions.md) – Complete documentation of all account types (over 50), including their purposes, relationships, and meanings within the asset, liability, equity, expense, and revenue categories.
- [developer-workflows.instructions.md](.github/instructions/developer-workflows.instructions.md) – Covers developer scripts, Python usage patterns, testing procedures, and automation best practices for maintaining and extending the ledger system.
- [common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md) – Step-by-step guides for frequently performed ledger operations, including transaction entry, monthly migration, and script usage, to streamline routine tasks.
- [editing-guidelines.instructions.md](.github/instructions/editing-guidelines.instructions.md) – Best practices for editing, formatting, and maintaining journal files, with anti-patterns to avoid and tips for structure, assertions, and includes.
- [security.instructions.md](.github/instructions/security.instructions.md) – Instructions for encryption, UUID privacy, and secure handling of confidential data, ensuring privacy and compliance throughout the ledger.
- [alternatives-journal.instructions.md](.github/instructions/alternatives-journal.instructions.md) – Explains the distinction between liquid and illiquid asset tracking, and how to manage alternative journals for crypto and non-cash assets.
- [dependencies.instructions.md](.github/instructions/dependencies.instructions.md) – Lists all required software and tools (hledger, Python, GPG), with installation and troubleshooting guidance for a reliable accounting environment.
- [git-commits.instructions.md](.github/instructions/git-commits.instructions.md) – Explicit conventional commit rules and agent commit conventions for all repository contributions, including ledger transaction commit requirements.

Agent Skills (`.github/skills/`):

- [add-transactions](.github/skills/add-transactions/SKILL.md) – Transcribe and enter transactions from raw data sources (including general automation of structured transaction imports, e.g. Octopus eDDA top-ups from email) with correct status, tags, accounts, and deduplication.
- [upsert-octopus-transactions](.github/skills/upsert-octopus-transactions/SKILL.md) – Add or update Octopus card transactions from app history, including transport and reloads, with proper mapping.
- [match-octopus-statement-transactions](.github/skills/match-octopus-statement-transactions/SKILL.md) – Match Octopus Wallet statement rows to journal transactions and update transaction datetimes for accuracy.
- [monthly-migration](.github/skills/monthly-migration/SKILL.md) – Perform monthly closing and migration using hledger --migrate, ensuring correct opening balances and assertions.
- [edit-journals](.github/skills/edit-journals/SKILL.md) – Edit hledger journal files following best practices for structure, includes, assertions, and formatting.
- [validate-journals](.github/skills/validate-journals/SKILL.md) – Validate and format hledger journals before commit using check/format scripts for consistency.

## Key Concepts

**Status markers**: `!` = pending (awaiting confirmation), `*` = cleared (verified), no marker = normal

**Journal types**: `self.journal` (liquid assets), `self.alternatives.journal` (illiquid/crypto)

**Journal file naming reminder:** Always use the full path `ledger/[year]/[year]-[month]/[name].journal` when referring to monthly journals, not just `[year]/[year]-[month]/[name].journal`.

**Script commands: Always run from the `scripts/` directory**

- For all Python scripts (e.g., `python -m check`, `python -m format`, `python -m depreciate`, `python -m shift`, `python -m replace`, `python -m encrypt`, `python -m decrypt`), **always set the working directory to `scripts/` using the tool's `cwd` parameter**. This applies to both direct Python invocations and all script wrappers (e.g., `./check`, `check.bat`, `./format`, `format.bat`).
- **Never run scripts from the root directory or any other location.** Running from the wrong directory will cause include and file discovery errors.
- Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.
- For `pnpm run hledger:check` and `pnpm run hledger:format`, run from the repository root as these are pnpm scripts.
- For `hledger close --migrate`, run from the repository root as well.

**Shortcut:** You may use the script wrappers from the `scripts/` directory directly (e.g., `./check`, `./format`, `check.bat`, `format.bat`), but you **must** still set the working directory to `scripts/` when using these wrappers.

**Critical:** If you run any script or wrapper from the wrong directory, you will encounter include errors, missing file errors, or incorrect results. Always double-check the working directory before running any script command.

**Module exports:** All Python modules in `scripts/` MUST define a module-level `__all__` tuple to explicitly control the module's public exports. If a module has no public exports, use an empty tuple `()`. This helps agents and imports be explicit about available symbols.

**Final Reminder:**

> **Agents must always check and set the working directory to `scripts/` for all script commands and wrappers.** This is the most common source of agent errors. Never assume the current directory is correct—always set it explicitly.

## Quick Start

Skills:

- [add-payee](.github/skills/add-payee/): Add or update payee information in the ledger, including payee aliases and mappings.
- [add-transactions](.github/skills/add-transactions/): Transcribe transactions from raw data (receipts, statements, OCR, and any structured machine-readable source such as Octopus eDDA top-up emails) into hledger journal format with correct status, tags, accounts, and deduplication. Includes a general framework for specialized transaction import and automation.
- [upsert-octopus-transactions](.github/skills/upsert-octopus-transactions/): Upsert (add or update) Octopus card transactions from app history, including transport and reloads, and update durations.
- [monthly-migration](.github/skills/monthly-migration/): Perform monthly closing and migration using hledger --migrate, ensuring correct opening balances and assertions.
- [edit-journals](.github/skills/edit-journals/): Edit hledger journal files following best practices for structure, includes, assertions, and formatting.
- [validate-journals](.github/skills/validate-journals/): Validate and format hledger journals before commit using check/format scripts.

Instructions:

- Security: [security.instructions.md](.github/instructions/security.instructions.md) — Guidance for handling confidential data, encryption, and UUID privacy.
- Pre-commit: [common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md) — Step-by-step pre-commit checklist and common ledger workflows.

## VS Code Setup

**Chat configuration**: Enable `chat.useAgentsMdFile` in settings. Leave `chat.useNestedAgentsMdFiles` disabled (single root AGENTS.md). Use "Chat: Configure Instructions" to verify active files.

**Markdown formatting**: Use `.editorconfig` (UTF-8, 2-space indent) and `.markdownlint.jsonc`. Format via VS Code extension or CLI (`pnpm run markdownlint:fix`). Always format before commit.

**Agent commits**: Agents and automation (including bots and assistants) MUST follow the repository's Git commit conventions described in `.github/instructions/git-commits.instructions.md`. **Commit body lines must be wrapped to 100 characters or fewer—this is strictly enforced by commitlint and will block commits that exceed this limit. If a commit is rejected, agents must rewrap and retry until commitlint passes.** Before making commits, agents must run the repository formatting and validation steps and use Conventional Commits for commit headers.

**Todo List Tool Reminder:**

- Before starting any multi-step or complex change, use the todo list tool to break down the work into actionable steps.
- Mark each step as in-progress and completed as you proceed.
- Update the todo list after each change to ensure nothing is forgotten.

When an agent has a motivation or rationale for a non-ledger change, include that rationale in the commit body. Do NOT include bodies for `ledger(...)` transaction commits — those must remain a single-line header to stay machine-parseable.
