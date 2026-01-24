---
name: Common Workflows
description: Practical task guides for frequently performed operations including transaction entry, monthly migration, and script usage.
---

# Common Workflows

Frequently performed operations organized into Agent Skills:

## Adding Transactions

**Skill:** [add-transactions](../skills/add-transactions/)

Transcribe transactions from receipts, bank statements, OCR text with proper status markers and tagging.

## Adding Octopus Transactions

**Skill:** [add-octopus-transactions](../skills/add-octopus-transactions/)

Add missing Octopus card transactions, duration metadata, and card reloads from app history.

## Monthly Migration

**Skill:** [monthly-migration](../skills/monthly-migration/)

Close previous month and initialize new month with proper balance assertions.

## Script Usage

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

1. Format Markdown: `pnpm run markdownlint:fix` (optional: auto-fix)
2. Validate journals: `python -m check`
3. Format journals: `python -m format`
4. If edited `private.yaml`: `python -m encrypt`
5. Review: `git status && git diff`
6. Prepare hooks: `pnpm install && pnpm run prepare`
7. Commit: `git commit -S -m "chore: describe changes"`

## Related Documentation

- [add-transactions](../skills/add-transactions/) - Add transactions from raw data
- [monthly-migration](../skills/monthly-migration/) - Monthly journal migration
- [edit-journals](../skills/edit-journals/) - Edit journals with best practices
- [validate-journals](../skills/validate-journals/) - Validate and format journals
- [Developer Workflows](./developer-workflows.instructions.md) - Script patterns and Python conventions
