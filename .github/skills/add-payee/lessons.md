# Add Payee — Lessons & Continuous Improvement

Keep this file concise. Append dated one-line notes when adding examples or clarifications. If this file exceeds **8 dated entries** or becomes longer than a single screen, use the integration-first consolidation process below.

## Consolidation policy

- For each older or undated entry:
  1. Decide where the entry's meaning best belongs (e.g., `SKILL.md` guidance, `examples.md`), and add a short improvement there.
  2. Replace the lesson entry in `lessons.md` with a one-line pointer (e.g., `Integrated → SKILL.md: Payee insertion`) or delete it after integration.
- Keep `lessons.md` short and recent. Run `pnpm run format` and `pnpm run test` after changes.

## 2026-02-08

- When adding a payee, remember to place it in strict lexicographic order in `preludes/self.journal` and validate with `pnpm run format` and `pnpm run check`.
