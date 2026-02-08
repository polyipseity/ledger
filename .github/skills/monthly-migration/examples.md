# Monthly Migration — Examples

Canonical migration examples and verification steps.

## Quick Example (commands)

```bash
# Generate migrations for closing month
hledger close -f ledger/2025/2025-12/self.journal --migrate > migration-2025-12.txt
hledger close -f ledger/2025/2025-12/self.alternatives.journal --migrate > migration-2025-12-alternatives.txt

# Inspect and copy outputs
# Append closing balances to ledger/2025/2025-12/self.journal (end of file)
# Prepend opening balances to ledger/2026/2026-01/self.journal (after prelude)
```

## Verification

- Verify closing timestamp `23:59:59` and opening `00:00:00`.
- Run `pnpm run format` and `pnpm run check`.
- Commit with `chore(migration): migrate 2025-12 → 2026-01` and short rationale.

(Keep examples concise and non-confidential.)
