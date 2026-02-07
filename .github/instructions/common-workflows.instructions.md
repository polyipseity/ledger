---
name: Common Workflows
description: Practical task guides for frequently performed operations including transaction entry, monthly migration, and script usage.
---

# Common Workflows

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

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

See `.github/instructions/developer-workflows.instructions.md` for the canonical script usage policy. Short: prefer `pnpm run <script>` from the repository root; if none exists, run Python scripts with `cwd=scripts/`.

## Pre-Commit Checklist (Husky + lint-staged)

1. Format Markdown: `pnpm run markdownlint:fix` (optional: auto-fix)
2. Validate journals: `pnpm run check`
3. Format journals: `pnpm run format`
4. Run tests: `pnpm run test` (Husky registers a `pre-push` hook that will run the test suite before pushing; run tests locally to avoid blocked pushes)
5. If edited `private.yaml`: use `pnpm run encrypt` if available, otherwise `python -m scripts.encrypt` (set cwd)
6. Review: `git status && git diff`
7. Prepare hooks: `pnpm install && pnpm run prepare` (registers Husky hooks; lint-staged is configured in `.lintstagedrc.mjs`). Note: `pnpm install` runs `python -m pip install -e . --group dev` to install development extras declared in `pyproject.toml` using the new dependency group syntax. We removed `requirements.txt` to avoid duplication — `pyproject.toml` is the canonical source of dependency metadata. Because `pyproject.toml` declares no installable packages, this will only install extras and will not add project packages to the environment.
8. Commit: `git commit -S -m "chore: describe changes"`

## Related Documentation

- [add-transactions](../skills/add-transactions/) - Add transactions from raw data
- [upsert-octopus-transactions](../skills/upsert-octopus-transactions/) - Upsert Octopus card transactions
- [monthly-migration](../skills/monthly-migration/) - Monthly journal migration
- [edit-journals](../skills/edit-journals/) - Edit journals with best practices
- [validate-journals](../skills/validate-journals/) - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python conventions
