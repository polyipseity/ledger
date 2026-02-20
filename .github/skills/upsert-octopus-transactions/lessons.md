# Upsert Octopus Transactions — Lessons & Continuous Improvement

Keep this file short and append dated one-line notes when adding examples or rule clarifications. If this file exceeds **8 dated entries** or becomes longer than a single screen, follow the integration-first consolidation steps below.

## Consolidation policy

- For each older or undated entry:
  1. Determine the best target file in this skill folder (e.g., `SKILL.md`, `examples.md`, or a helper file) where the rule belongs.
  2. Integrate the lesson as a concise improvement in that file (bullet, example, or short clarification).
  3. Replace the lesson entry in `lessons.md` with a one-line pointer (e.g., `Archived → See examples.md: Octopus Pass 1`) or delete it after integration.
- Keep `lessons.md` focused on recent, actionable items only. Run `pnpm run format` and `pnpm run test` after edits.

## 2026-02-08

- When adding a worked example to `./examples.md`, add a one-line explanation here with the reason (e.g., why Pass 1 needed a duration update for a specific pattern).
- Keep examples non-confidential and use placeholder UUIDs.

## 2026-02-19 — Consolidation

- Integrated worked examples into `examples.md` (duration insertion, KMB reward accrual, vending‑machine & public light bus mappings). Operational rules (bank→wallet verification, duplicate end‑time rows → `duration:`) are captured in `SKILL.md` and `specialized_transaction_import.md`.
- Archived detailed bullets here — see `examples.md`, `SKILL.md`, and `specialized_transaction_import.md` for canonical guidance and worked examples.

## 2026-02-20 — Payee mapping & matching

- 2026-02-20: Octopus merchant “其他” was a duplicate Cafe 100% breakfast entry; added mapping and confirmed matching should occur instead of creating a new transaction.
