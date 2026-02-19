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
- 2026-02-19: Added `gifts / red-packet (lai-see)` worked examples to `examples.md` — clarifies receive (equity) vs give (expense) patterns and asset-account choices.- 2026-02-19: Added extra red-packet variants (WeChat/Alipay, group‑split, corporate, reimbursement) to `examples.md` — clarifies wallet vs bank receipts, pool distribution, and when to use `equity:organizations` vs `equity:friends`.- Keep both files non-confidential; use placeholder UUIDs and anonymized data only.
- Run `pnpm run format` and `pnpm run test` after editing examples or lessons to keep docs and tests in sync.

## 2026-02-19 — Payee/id fixes & metadata (continuous learning)

- Added payee mapping: "Ebeneezer's" → "Ebeneezer's Kebabs & Pizzeria" and id-mapping (transaction_id, table_number).
- Corrected AC2 payee to UUID `9da2b39f-64b4-4721-a033-b50e84a4a76d` and recorded size descriptor `(細)` for `火腿絲通粉`.
- Fixed Asia Pacific receipts: do NOT use `堂食` as a payee in mappings; use the canonical payee UUID in transactions when appropriate. **Do NOT** add payee_mappings entries that map aliases to private UUIDs.
- Modifiers must be recorded inline with the food item (e.g. `food_or_drink: E. 叉燒芝士拌麵 (大盛) + 蔬菜2倍 + 蒜-多`); do **not** use a separate `modifiers:` tag.
- Do not record routine discounts as explicit negative postings — record the discounted item price directly and keep each item on its own line.
- Split aggregated item lines when the receipt shows separate items (example: `田園熱狗 25.00` + `番茄肉碎米粉(細) 5.00` → two `food_or_drink` lines).
- Added `id_mappings.yml` entries for the affected vendors (`9da2b39f-64b4-4721-a033-b50e84a4a76d`, `岡山一番店拉麵`, `UNY`) so vendor-specific IDs are captured during import.
- Added missing item normalizations where appropriate (for example `炒滑蛋`, `鮮奶滑蛋三文治`) and corrected `多奶` to be an inline modifier.
- Mapping update: `Super Sandwiches` → `Oliver's Super Sandwiches`; added id‑mapping for receipt id pattern `082-2611`.
- IDs: never use Octopus numbers as the primary transaction identifier — prefer vendor transaction IDs.
- Octopus eDDA debtor-reference tokens appearing in provider emails are constant; ignore them for matching and **do not** transcribe debtor-reference values into journal entries or id-mappings. When matching eDDA reloads prefer FRN/C transfer IDs, timestamps, and amounts.
- Parsing: treat leading `w` as `with` (not part of the item name); record accompaniments as separate `food_or_drink` lines (example: `Twister Fries (XL)`, `Hot Chocolate`, `BBQ sauce`).
- Meal classification: McDonald's combo meals consumed in the afternoon should use `eating: afternoon tea` (not `snacks`).
- Saizeriya receipts frequently include two timestamps (order vs. payment). When both timestamps appear, record `duration:` as the difference (example: 2026-02-15 Saizeriya — `duration: PT52M55S`).
- Cafe 100% receipts sometimes list zero-priced items (for example `熱咖啡 + 多奶` at $0.00). Record these as separate `expenses:food and drinks:drinks` postings with `0.00 HKD` and include the modifier inline in `food_or_drink:`.
- Do **not** record ordering-method or ordering-channel descriptors (for example `使用二維碼自助點餐`, `外賣/自取`) as zero-amount `food_or_drink` or `fee` postings — treat these as metadata and remove them during transcription.
- Dondonya receipts include table numbers in the format `A10`; add `table_number` extraction to `id_mappings.yml` and capture `(receipt_no, A10)` in the payee parenthetical when present.

Rationale: these rules improve canonical payee matching, parsing accuracy for item/modifier extraction, and automated upsert/matching against vendor IDs; they reduce false-positive mappings and make downstream analytics (item-level, modifier-level) reliable.

## 2026-02-19 — Octopus reload / eDDA transfer rule (continuous learning)

- Observation: during the Add Transactions run I found Octopus wallet→card reloads that had no preceding bank→Octopus‑wallet eDDA transfer; I inserted the missing bank→wallet transfers using the Hang Seng C‑references/FRN and timestamps.
- Rule: when adding a reload (wallet→card) in Pass 2, always verify **or** add the bank→Octopus‑wallet eDDA transfer first — use the bank C/FRN and timestamp for provenance and matching. **Do NOT** use Octopus debtor‑reference tokens for matching; prefer FRN/C transfer IDs, timestamps, and amount.
- Action: updated `ledger/2026/2026-02/self.journal` (5 bank→wallet inserts) and integrated the rule into `upsert-octopus-transactions/SKILL.md`.

---

(Keep this file short; historical detail and longer rationales may be stored in PR descriptions or in commit messages.)
