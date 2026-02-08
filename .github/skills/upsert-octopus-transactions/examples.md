# Upsert Octopus Transactions — Examples

Use these non-confidential, canonical worked examples when performing Pass 1 (update) and Pass 2 (add) workflows. Keep examples short and anonymized.

## Pass 1 (Update Only)

- Example: Octopus row 2026-01-24 12:11 amount 35.00 matches an existing journal transaction dated 2026-01-24 11:27:42.
  - Action: Re-open the journal, confirm date & amount match. If time difference ≥ 2 minutes and the journal entry has `time:` but no `duration:`, insert `duration: PT43M` immediately after `time:` in the header comment and run `pnpm run format` and `pnpm run check`. Do not change postings or payee. If ambiguous, stop and ask the user.

## Pass 2 (Add Only)

- Example: Unmatched Octopus row 2026-01-25 12:38 amount 78.00 for a confidential payee.
  - Action: Check `payee_mappings.yml` and `private.yaml`. If a UUID exists, use it; if not, ask the user. Register any new payee in `preludes/self.journal`, insert the new transaction in strict chronological order, run `pnpm run format` and `pnpm run check`, and commit with the single-line ledger header (e.g., `ledger(self.journal): add 1 transaction(s)`).

## Worked Example (Conceptual)

```hledger
2026-01-25 a2ccd533-7a2e-4fa1-ad63-e4f1d3bdc159  ; activity: medical, time: 12:38, timezone: UTC+08:00
   expenses:healthcare:medication               78.00 HKD
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521   -78.00 HKD
```

**See also:** Pass 1 examples above and the matching heuristics in `SKILL.md`.

## When to ask for clarification

- Mapping missing or ambiguous
- Multiple candidate matches by date/amount/time
- Confidential payee without UUID
- Unclear reload source or unusual amounts

---

When adding a new worked example, append a one-line note to `./lessons.md` explaining why the example was added and any rule it illustrates.
