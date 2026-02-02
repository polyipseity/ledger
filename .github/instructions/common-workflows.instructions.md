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

**Script commands: Always run from the `scripts/` directory**

```powershell
# Always set cwd to scripts/ for all script commands and wrappers:
python -m check                    # Validate journals
python -m format                   # Format journals
python -m depreciate --from 2025-01 --to 2025-12 "Item" 50.00 HKD  # Depreciate
python -m shift --from 2025-01 --to 2025-12 "assets:cash" 100.00 HKD  # Shift
python -m replace "old" "new"     # Find/replace
python -m encrypt                  # Encrypt private.yaml
python -m decrypt                  # Decrypt private.yaml
```

**Always set the working directory to `scripts/` using the tool's `cwd` parameter when running any script or wrapper (including `./check`, `check.bat`, etc.).**

- Never run scripts from the root directory or any other location. Running from the wrong directory will cause include and file discovery errors.
- Only use `cd` as a fallback if the tool does not support a working directory parameter. Never rely on the current directory being correct by default.

## Pre-Commit Checklist (Husky + lint-staged)

1. Format Markdown: `pnpm run markdownlint:fix` (optional: auto-fix)
2. Validate journals: `python -m check`
3. Format journals: `python -m format`
4. If edited `private.yaml`: `python -m encrypt`
5. Review: `git status && git diff`
6. Prepare hooks: `pnpm install && pnpm run prepare` (registers Husky hooks; lint-staged is configured in `.lintstagedrc.mjs`). Note: `pnpm install` runs `python -m pip install -e "[dev]"` to install development extras declared in `pyproject.toml`. We removed `requirements.txt` to avoid duplication — `pyproject.toml` is the canonical source of dependency metadata. Because `pyproject.toml` declares no installable packages, this will only install extras and will not add project packages to the environment.7. Commit: `git commit -S -m "chore: describe changes"`

## Related Documentation

- [add-transactions](../skills/add-transactions/) - Add transactions from raw data
- [upsert-octopus-transactions](../skills/upsert-octopus-transactions/) - Upsert Octopus card transactions
- [monthly-migration](../skills/monthly-migration/) - Monthly journal migration
- [edit-journals](../skills/edit-journals/) - Edit journals with best practices
- [validate-journals](../skills/validate-journals/) - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python conventions
