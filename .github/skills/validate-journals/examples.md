# Validate Journals — Examples

Short examples for validation commands and common fixes.

## Validate single month

```bash
python -m check   # runs hledger --strict across all journals
# or
hledger -f ledger/2025/2025-01/self.journal --strict bal
```

## Fix a missing payee

1. Add `payee Example Payee` to `preludes/self.journal`.
2. Run `pnpm run format` and `pnpm run check` again.

(Keep examples concise and non-confidential.)
