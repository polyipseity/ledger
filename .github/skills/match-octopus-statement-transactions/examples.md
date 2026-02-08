# Match Octopus Statement Transactions — Examples

Canonical examples for time updates and matching heuristics.

## Exact-match update (seconds added)

- Statement row: 2026-01-10 12:34:56, Amount: -12.50, Ref: FRN20260110
- Journal match: 2026-01-10 12:34 (no seconds)
- Action: Update journal time to `12:34:56` (silent summary by default).

## Non-typical update (minute/hour/date change)

- Statement row: 2026-01-11 00:05:00, Amount: -200.00
- Journal match: 2026-01-10 23:55 (different day/hour)
- Action: Report original and updated datetimes in the summary for manual review.

(Keep examples non-confidential and concise.)
