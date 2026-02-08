# Monthly Migration — Lessons & Continuous Improvement

Keep this file short. Append one-line dated notes for any unusual migration cases. If this file exceeds **8 dated entries** or becomes longer than a single screen, follow the integration-first consolidation steps below.

## Consolidation policy

- For each older or undated entry:
  1. Pick a target file for the lesson (e.g., `SKILL.md` procedural step, `examples.md` command snippet).
  2. Integrate the lesson into that target file as a concise improvement.
  3. Replace or remove the lesson in `lessons.md` with a one-line pointer after integration.
- Keep `lessons.md` short and recent; run `pnpm run format` and `pnpm run test` after changes.

## 2026-02-08

- Always run migration for both `self.journal` and `self.alternatives.journal` and validate with `pnpm run format` and `pnpm run check` before commit.
