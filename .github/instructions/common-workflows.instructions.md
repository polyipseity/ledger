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

Before committing changes:

```powershell
# 1. Format Markdown files
markdownlint-cli2 --fix "**/*.md"

# 2. Validate all journals
python -m check

# 3. Format all journals
python -m format

# 4. If edited private.yaml
python -m encrypt

# 5. View changes
git status
git diff --cached

# 6. Commit
git commit -S -m "Describe changes"
```

(Use `-S` flag for signed commits if configured.)

## Related Skills and Documentation

- [add-transactions](../skills/add-transactions/) skill - Add transactions from raw data
- [monthly-migration](../skills/monthly-migration/) skill - Monthly journal migration
- [edit-journals](../skills/edit-journals/) skill - Edit journals following best practices
- [validate-journals](../skills/validate-journals/) skill - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python code conventions
