# Add Transactions — Lessons Learned & Continuous Improvement

This file collects short, actionable lessons learned and continuous improvement notes for the Add Transactions skill. Keep it concise and append dated entries with a short rationale.

## Consolidation policy

- If this file exceeds **8 dated entries** or becomes longer than a single screen, do NOT archive entries verbatim into SKILL.md. Instead, for each older or undated entry:
  1. Interpret the entry's purpose and decide which file in this skill folder (for example: `SKILL.md`, `examples.md`, a theme file) should be improved to capture the lesson.
  2. Integrate the lesson's meaning as a concise improvement into that target file (short bullet, clarification, or example), keeping the authoritative files discoverable and actionable.
  3. Replace the original entry in `lessons.md` with a one-line pointer, e.g. `Archived → See <file> <section>`, or remove it entirely after integration.
- Always prefer improving the authoritative source (SKILL.md, `examples.md`, or a theme file) so that lessons remain actionable and easier to find.
- After making such changes, run `pnpm run format` and `pnpm run test` to validate docs and tests.

## 2026-02-01 (AI skill update, integrated)

Integrated → See the canonical files for each rule (added pointers in `SKILL.md`):

- Payee/ID rules → `payee_id_mapping_rules.md` (mapping/ID handling)
- Food/Drink tagging & translation → `food_transactions.md` + `food_translations.yml`
- Posting and tag validation → `posting_tag_rules.md`
- Lending/repayment status markers → `lending_borrowing_transactions.md`
- Octopus & specialized import heuristics → `specialized_transaction_import.md` and `examples.md`

If you need a specific lesson re-integrated as an explicit bullet or example in a canonical file, tell me which item and I'll add a concise example/clarification in the matching file and replace this pointer with `Integrated → <file>:<section>`.

## Status markers

Use status markers only for lending/borrowing transactions. Update pending (`!`) to cleared (`*`) when settled, and use liability assertions when repaying.

## Change process

- When adding a new example to `./examples.md`, append a short one-line note to `./lessons.md` explaining the reason and any rule it illuminates.
- Keep both files non-confidential; use placeholder UUIDs and anonymized data only.
- Run `pnpm run format` and `pnpm run test` after editing examples or lessons to keep docs and tests in sync.

---

(Keep this file short; historical detail and longer rationales may be stored in PR descriptions or in commit messages.)
