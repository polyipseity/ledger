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

## Common Scripts Usage

Practical examples for running utility scripts:

### Check Journals

Validate all journals before committing:

```powershell
python -m check
```

Output shows any errors found. Fix errors before proceeding.

### Format Journals

Auto-format all journals:

```powershell
python -m format
```

Always run after editing to ensure consistent formatting.

### Add Depreciation

Add depreciation entries for a depreciable asset:

```powershell
# Add monthly depreciation for an asset
python -m depreciate --from 2025-01 --to 2025-12 "iPad 10th" 69.00 HKD
```

Adds depreciation postings to each monthly journal in the range.

### Shift Account Balance

Adjust account balance across multiple months:

```powershell
# Adjust cash balance across all 2025 months
python -m shift --from 2025-01 --to 2025-12 "assets:cash" 100.00 HKD
```

Modifies balance assertions to reflect the adjustment.

### Find and Replace

Search and replace text across all journals:

```powershell
# Replace old text with new text everywhere
python -m replace "old text" "new text"
```

Applies changes across all monthly journals.

### Encrypt Confidential Data

Encrypt private.yaml before committing:

```powershell
python -m encrypt
```

Required after editing private.yaml. Always run before `git commit`.

### Decrypt Confidential Data

Decrypt for editing confidential mappings:

```powershell
python -m decrypt
```

Prompts for GPG password. Remember to encrypt again after editing.

## Pre-Commit Checklist

Before committing changes:

```powershell
# 1. Validate all journals
python -m check

# 2. Format all journals
python -m format

# 3. If edited private.yaml
python -m encrypt

# 4. View changes
git status
git diff --cached

# 5. Commit
git commit -S -m "Describe changes"
```

(Use `-S` flag for signed commits if configured.)

## Related Skills and Documentation

- [add-transactions](../skills/add-transactions/) skill - Add transactions from raw data
- [monthly-migration](../skills/monthly-migration/) skill - Monthly journal migration
- [edit-journals](../skills/edit-journals/) skill - Edit journals following best practices
- [validate-journals](../skills/validate-journals/) skill - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python code conventions
