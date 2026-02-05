<!-- markdownlint-disable MD013 MD036 -->

# Personal Ledger Project - Instructions

**IMPORTANT: This documentation must not contain confidential information.** All examples should use non-confidential placeholders (UUIDs, generic names, example amounts) instead of real account numbers, personal names, locations, or actual financial data. Confidential mappings are stored in the encrypted `private.yaml.gpg` file only.

## 🚩 Agent Workflow Reminders

**Read relevant skill files before use.** When a user asks you to perform a skill, read its SKILL.md in full before doing any work.

**Use the Todo List Tool for multi-step tasks.** Plan steps, mark one step `in-progress`, complete it, then continue. Keep the todo list updated and concise.

**Ask instead of guessing.** If anything is ambiguous, pause and request clarification rather than making assumptions.

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

## Agent Code Conventions

Please follow these coding conventions in agent edits and new scripts. They are enforced to keep the codebase consistent and easy to review:

- Use `anyio.Path` for file/script identifiers:
  - APIs that accept a script identifier (for example, `JournalRunContext`) **must** accept an :class:`anyio.Path` (alias `Path`) only, not strings. Call sites should pass `Path(__file__)`.
  - The script identifier must be a readable file. The helper that derives a script cache key will fail-fast and raise :class:`FileNotFoundError` if the script path cannot be opened for reading.
- Use timezone-aware UTC datetimes:
  - Avoid `datetime.utcnow()`; instead use `datetime.now(timezone.utc)` and store or format ISO timestamps from timezone-aware objects.
- Prefer `from ... import ...` over `import ...`:
  - Import specific names rather than whole modules (for example `from hashlib import sha256`, `from json import loads, dumps`). This makes uses explicit and easier to statically analyse.
  - Inline imports may be used sparingly for optional runtime-only imports (e.g. in exception handlers), but prefer `from ... import ...` at module level where practical.
- Type hints & PEP 585: Prefer modern built-in generic types (PEP 585) and `collections.abc` abstract types in all new code and agent guidance. Use `dict`, `list`, `set`, `tuple`, `frozenset` etc. instead of `typing.Dict`, `typing.List`, etc., and prefer `collections.abc` names for ABCs (for example, `collections.abc.Awaitable` instead of `typing.Awaitable`). When appropriate, use the PEP 604 union operator (`X | Y`) for optionals/union types instead of `typing.Optional`.
- No legacy cache compatibility in new code paths:
  - Where cache formats or APIs were upgraded, new code should not re-introduce legacy compatibility branches. Keep cache formats structured and document upgrades.
- Be explicit with public exports:
  - Keep `__all__` tuples up-to-date for modules under `scripts/`.

These conventions are lightweight but help keep agent-generated edits consistent and easy to review.

## Key Concepts

**Status markers**: `!` = pending (awaiting confirmation), `*` = cleared (verified), no marker = normal

**Journal types**: `self.journal` (liquid assets), `self.alternatives.journal` (illiquid/crypto)

**Journal file naming reminder:** Always use the full path `ledger/[year]/[year]-[month]/[name].journal` when referring to monthly journals, not just `[year]/[year]-[month]/[name].journal`.

**Script commands: Always use pnpm script wrappers if available**

- For all operations, prefer `pnpm run <script>` (e.g., `pnpm run check`, `pnpm run format`, `pnpm run hledger:check`, `pnpm run hledger:format`, etc.) from the repository root. This ensures the correct environment, dependencies, and working directory are set automatically.
- Only use direct Python invocations (e.g., `python -m scripts.check`) or script wrappers in `scripts/` (e.g., `./check`, `check.bat`) if no pnpm script is available for the required operation. When using these, always set the working directory to `scripts/` using the tool's `cwd` parameter.
- **Never run scripts from the wrong directory.** Running from the wrong location will cause include errors, missing file errors, or incorrect results.
- For `hledger close --migrate`, run from the repository root as well.

**Critical:** Always use the pnpm script wrapper if it exists. Only fall back to direct invocation or script wrappers if no pnpm script is available. Always double-check the working directory before running any script command.

**Module exports:** All Python modules in `scripts/` MUST define a module-level `__all__` tuple at the beginning of the module (immediately after the module docstring and imports) to explicitly control the module's public exports. If a module has no public exports, use an empty tuple `()`. Keep `__all__` tuples up-to-date and place them at the top-level of the file; do not use underscore-prefixed aliases for imported names to hide them (for example, `ArgumentParser as _ArgParser`). Instead import names normally and use `__all__` to control what the module exports.

**Final Reminder:**

> **Agents must always check and set the working directory to `scripts/` for all script commands and wrappers.** This is the most common source of agent errors. Never assume the current directory is correct—always set it explicitly.

**Note:** `pnpm install` runs a `postinstall` hook which will run `python -m pip install -e . --group dev` to install development extras declared in `pyproject.toml` using the new PEP 722 dependency group syntax. `requirements.txt` has been removed — `pyproject.toml` is the canonical source of dependency metadata. Because `pyproject.toml` declares no installable packages, this only installs extras and will not add project packages to the environment.

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
- Husky + lint-staged: [common-workflows.instructions.md](.github/instructions/common-workflows.instructions.md) — Step-by-step local pre-commit checklist and common ledger workflows (hooks are managed by Husky; run `pnpm run prepare` to register hooks). The lint-staged configuration is stored in `.lintstagedrc.mjs`.

## VS Code Setup

**Chat configuration**: Enable `chat.useAgentsMdFile` in settings. Leave `chat.useNestedAgentsMdFiles` disabled (single root AGENTS.md). Use "Chat: Configure Instructions" to verify active files.

**Markdown formatting**: Use `.editorconfig` (UTF-8, 2-space indent) and `.markdownlint.jsonc`. Markdown linting covers multiple extensions (for example: `.md`, `.mdx`, `.mdown`, `.rmd`) via the CLI's globs. Format via VS Code extension or CLI (`pnpm run markdownlint:fix`). Always format before commit.

**Agent commits**: Agents and automation (including bots and assistants) MUST follow the repository's Git commit conventions described in `.github/instructions/git-commits.instructions.md`. **Commit body lines must be wrapped to 100 characters or fewer—this is strictly enforced by commitlint and will block commits that exceed this limit. If a commit is rejected, agents must rewrap and retry until commitlint passes.** Before making commits, agents must run the repository formatting and validation steps using the pnpm script wrappers (e.g., `pnpm run format`, `pnpm run check`) and use Conventional Commits for commit headers.

**Todo List Tool Reminder:**

- Before starting any multi-step or complex change, use the todo list tool to break down the work into actionable steps.
- Mark each step as in-progress and completed as you proceed.
- Update the todo list after each change to ensure nothing is forgotten.

When an agent has a motivation or rationale for a non-ledger change, include that rationale in the commit body. Do NOT include bodies for `ledger(...)` transaction commits — those must remain a single-line header to stay machine-parseable.
