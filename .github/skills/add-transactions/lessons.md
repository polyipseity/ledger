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
- 2026-02-19: Added `gifts / red-packet (lai-see)` worked examples to `examples.md` — clarifies receive (equity) vs give (expense) patterns and asset-account choices.
- 2026-02-19: Added extra red-packet variants (WeChat/Alipay, group‑split, corporate, reimbursement) to `examples.md` — clarifies wallet vs bank receipts, pool distribution, and when to use `equity:organizations` vs `equity:friends`.
- 2026-02-19: Added `equity:unknown:strangers` account and worked examples for gifts from strangers/promotional sources (use this when sender is a stranger, not truly unidentified).
- Keep both files non-confidential; use placeholder UUIDs and anonymized data only.
- Run `pnpm run format` and `pnpm run test` after editing examples or lessons to keep docs and tests in sync.

## 2026-02-19 — Payee/id fixes & metadata (consolidated)

- Integrated → `SKILL.md: Generalized Learnings` (modifiers inline, discounts as item prices, split aggregated items, zero‑priced item handling, ordering‑method metadata, meal classification).
- Integrated → `id_mappings.yml` & `payee_mappings.yml` for vendor id/payee additions (Ebeneezer's, Oliver's Super Sandwiches, UNY, Dondonya, 岡山一番店拉麵, 9da2b39f-...).
- Integrated → `specialized_transaction_import.md` & `upsert-octopus-transactions/lessons.md` for Octopus/eDDA matching heuristics (do **not** use debtor‑reference tokens; prefer FRN/transfer IDs, timestamps, and amounts) and the bank→wallet verification rule.
- Archived detailed notes → see the referenced files above for the canonical rules and worked examples.

## 2026-02-19 — Octopus reload / eDDA transfer rule (continuous learning)

- 2026-02-19: Octopus reload/eDDA transfer rule integrated → see `upsert-octopus-transactions/lessons.md` for the bank→wallet verification rule when adding reloads.

## 2026-02-20 — Itemization clarification

- Ensure menu lines showing multiple separate items are split; do not use `+` except for true modifiers. Integrated → `food_transactions.md` under "Itemization, Modifiers, Item Numbers, and Tagging".
- 2026-02-20: Octopus merchant “其他” should map to Cafe 100% and match existing breakfast entry; avoid creating duplicates. Added payee mapping accordingly.

---

(Keep this file short; historical detail and longer rationales may be stored in PR descriptions or in commit messages.)
