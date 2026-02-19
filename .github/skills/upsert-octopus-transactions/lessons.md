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

## 2026-02-19

- Added Pass 1 example for inserting `duration:` when Octopus shows a later end time than the journal `time:` (calculate difference; add when ≥ 2 minutes). See `examples.md: Pass 1`.
- Added Pass 2 example for Kowloon Motor Bus fares showing required reward-accrual postings (`assets:accrued revenues:rewards` + `revenues:rewards`). See `examples.md: Pass 2`.
- Persisted vending-machine guidance: map `太古可口可樂` → `Swire`; also added `7-Eleven` mapping earlier.
- Added a short lesson: Octopus may report multiple small KMB fares across consecutive times (including early morning). Always add each fare as a unique transaction and include reward accrual postings per fare.
- Added a lesson: Octopus sometimes reports a second `consumption`/`Cafe` row that represents the end time only — **do not** add a separate transaction. Instead, match to the earlier journal transaction (same date & amount, time within ±1.5 hours) and add a `duration:` to the original transaction header. Remove the duplicate consumption row from Pass 2.
- Confirmed example: 2026-02-16 Cafe 100% duplicate (09:53) — converted to `duration: PT30M28S` on the 09:22:32 transaction.
- Lesson: If an Octopus row shows an aggregate/group total that does not match any single journal posting (for example a group bill total vs per-person shares), **do not attempt to split or match automatically** — stop and ask the user for instructions. Add a worked-example to `examples.md` when a repeat pattern is observed.- Lesson (public light bus): map Octopus `專線小巴` to `public light bus` and record as `expenses:transport:buses` (no `assets:accrued revenues:rewards` posting). Add worked example to `examples.md`.- Rationale: clarifies duration handling and transport reward bookkeeping discovered during 2026-02 imports.
