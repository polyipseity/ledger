---
name: Common Workflows
description: Practical task guides for frequently performed operations including transaction entry, monthly migration, and script usage.
---

# Common Workflows

## 🚩 Agent Workflow Reminder: Use the Todo List Tool

**For all multi-step workflows (adding transactions, migration, validation, etc.), use the todo list tool to plan, track, and complete each step.**

Before starting, break down the workflow into actionable steps, mark each as in-progress and completed, and update the todo list after each change to avoid missing any required actions.

Frequently performed operations organized into Agent Skills:

## Adding Transactions

**Skill:** [add-transactions](../skills/add-transactions/)

Transcribe transactions from receipts, bank statements, OCR text with proper status markers and tagging.

## Upserting Octopus Transactions

**Skill:** [upsert-octopus-transactions](../skills/upsert-octopus-transactions/)

Upsert (add or update) Octopus card transactions, duration metadata, and card reloads from app history.

## Monthly Migration

**Skill:** [monthly-migration](../skills/monthly-migration/)

Close previous month and initialize new month with proper balance assertions.

## Script Usage

**Script commands: Always use pnpm script wrappers if available**

- For all operations, prefer `pnpm run <script>` (e.g., `pnpm run check`, `pnpm run format`, `pnpm run hledger:check`, `pnpm run hledger:format`, etc.) from the repository root. This ensures the correct environment, dependencies, and working directory are set automatically.
- Only use direct Python invocations (e.g., `python -m scripts.check`) or script wrappers in `scripts/` (e.g., `./check`, `check.bat`) if no pnpm script is available for the required operation. When using these, always set the working directory to `scripts/` using the tool's `cwd` parameter.
- **Never run scripts from the wrong directory.** Running from the wrong location will cause include errors, missing file errors, or incorrect results.
- For `hledger close --migrate`, run from the repository root as well.

**Critical:** Always use the pnpm script wrapper if it exists. Only fall back to direct invocation or script wrappers if no pnpm script is available. Always double-check the working directory before running any script command.

## Pre-Commit Checklist (Husky + lint-staged)

1. Format Markdown: `pnpm run markdownlint:fix` (optional: auto-fix)
2. Validate journals: `pnpm run check`
3. Format journals: `pnpm run format`
4. If edited `private.yaml`: use `pnpm run encrypt` if available, otherwise `python -m scripts.encrypt` (set cwd)
5. Review: `git status && git diff`
6. Prepare hooks: `pnpm install && pnpm run prepare` (registers Husky hooks; lint-staged is configured in `.lintstagedrc.mjs`). Note: `pnpm install` runs `python -m pip install -e . --group dev` to install development extras declared in `pyproject.toml` using the new dependency group syntax. We removed `requirements.txt` to avoid duplication — `pyproject.toml` is the canonical source of dependency metadata. Because `pyproject.toml` declares no installable packages, this will only install extras and will not add project packages to the environment.
7. Commit: `git commit -S -m "chore: describe changes"`

## Related Documentation

- [add-transactions](../skills/add-transactions/) - Add transactions from raw data
- [upsert-octopus-transactions](../skills/upsert-octopus-transactions/) - Upsert Octopus card transactions
- [monthly-migration](../skills/monthly-migration/) - Monthly journal migration
- [edit-journals](../skills/edit-journals/) - Edit journals with best practices
- [validate-journals](../skills/validate-journals/) - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python conventions
