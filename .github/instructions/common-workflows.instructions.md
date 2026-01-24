---
name: Common Workflows
description: Practical task guides for frequently performed operations on the personal ledger including transaction entry, monthly migration, and script usage examples.
---

# Common Workflows

Practical task guides for frequently performed operations on the personal ledger.

This documentation has been organized into reusable Agent Skills that Copilot can load automatically when relevant. See the sections below for guidance on common tasks.

## Adding Transactions from Raw Data

Process for transcribing transactions from source documents into the ledger.

**See the dedicated skill:** [add-transactions](../skills/add-transactions/) - Complete step-by-step procedure with examples

This skill covers:

- Finding template transactions
- Understanding transaction status markers (!, *)
- Applying status markers correctly
- Registering new entities (payees, accounts)
- Handling currency conversions
- Applying comprehensive tagging

## Monthly Journal Migration

Performed at the start of each month to close the previous month and initialize the new month.

**See the dedicated skill:** [monthly-migration](../skills/monthly-migration/) - Complete migration workflow with validation

This skill covers:

- Running migration commands for both journals
- Understanding the output (closing/opening balances)
- Creating new monthly journals
- Adjusting entry dates
- Verifying balance assertions
- Validation and post-migration checklist

## Script Examples

```powershell
python -m check                    # Validate journals
python -m format                   # Format journals
python -m depreciate --from 2025-01 --to 2025-12 "Item" 50.00 HKD  # Depreciate
python -m shift --from 2025-01 --to 2025-12 "assets:cash" 100.00 HKD  # Shift
python -m replace "old" "new"     # Find/replace
python -m encrypt                  # Encrypt private.yaml
python -m decrypt                  # Decrypt private.yaml
```

## Pre-Commit Checklist

Before committing changes, run the steps below to ensure markdown and journals are clean and commit hooks are prepared.

1. Format Markdown files

	- Install dependencies and run markdown lint (and optionally auto-fix):

```powershell
pnpm install --frozen-lockfile=false
pnpm run markdownlint
pnpm run markdownlint:fix   # optional: auto-fix issues
```

2. Validate all journals

```powershell
python -m check
```

3. Format all journals

```powershell
python -m format
```

4. If you edited `private.yaml`

```powershell
python -m encrypt
```

5. View changes

```powershell
git status
git diff --cached
```

6. Prepare pre-commit helpers and commit

	- Install pnpm deps and prepare Husky hooks so `lint-staged` and `commitlint` run locally:

```powershell
pnpm install
pnpm run prepare
```

	- Commit as usual. Commit messages are linted locally by `commitlint` (Husky `commit-msg` hook) and in CI. For ledger transaction commits use the ledger header and no body per `.github/instructions/git-commits.instructions.md`.

```powershell
git commit -S -m "chore: describe changes"
```

(Use `-S` flag for signed commits if configured.)

## Related Skills and Documentation

- [add-transactions](../skills/add-transactions/) skill - Add transactions from raw data
- [monthly-migration](../skills/monthly-migration/) skill - Monthly journal migration
- [edit-journals](../skills/edit-journals/) skill - Edit journals following best practices
- [validate-journals](../skills/validate-journals/) skill - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python code conventions
