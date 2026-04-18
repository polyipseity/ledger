# Add Transactions — Lessons (Active Queue + Integration Log)

Use this file as a lightweight queue for unresolved learnings. The authoritative rules must live in `SKILL.md`, theme files, `examples.md`, or mapping YAML files.

## Workflow

1. Add new learnings as short dated bullets under **Active queue**.
2. Integrate each learning into the right canonical file.
3. Replace the detailed bullet with a one-line pointer under **Integrated archive**.
4. Keep this file concise (single-screen target).

## Active queue

- 2026-03-28 — Corrected Genki Sushi entry to UUID resolved payee and updated id_mappings for `20b484a5-3c01-42f3-875c-e95509b3de22` (receipt/table pair). See integration pointer below.
- 2026-03-28 — TamJai SamGor itemization rule refined: base meal handling, modifier flags (不要芽菜/不要韭菜/不要腐皮), and per-item food_or_drink metadata should be explicit for all repeated C1 combos in single transaction.
- 2026-04-03 — McDonald's/food receipt detail: keep standalone item names exactly as printed; do not prefix bundled sides/drinks with `配` when the receipt already lists them separately.
- 2026-04-03 — Receipt header fidelity: keep full printed identifiers such as `000-964351` and `018-00123`; do not truncate leading zeroes or promote footer/POS codes into the transaction header.
- 2026-04-06 — Cafe 100% header fidelity: preserve the printed identifier order exactly as received (`transaction_id`, then `table_number`); do not normalize or swap the header tokens.
- 2026-04-06 — TamJai SamGor timing: when a receipt shows both `落單時間` and `結帳時間`, use the order time as `time:` and derive `duration:` from the gap to the closing time.
- 2026-04-06 — Wellcome fruit purchases: classify produce buys as `activity: eating, eating: fruits`, keep the exact printed fruit wording, and avoid relabeling them as generic consumption.

## Integrated archive

### 2026-04-18 — Food transaction pattern validation batch

Integrated → `food_transactions.md` (zero-priced itemization consistency rules, duration calculation precision), `lending_borrowing_transactions.md` (shared expense equity vs. liability distinction), `examples.md` (comprehensive 5-entry validation example with Saizeriya, TamJai SamGor, American Diner, HKUST ramen), `continuous-learning.instructions.md`

Key patterns:

- Zero-priced itemization: Each receipt component = separate posting + `food_or_drink:` tag (validated across TamJai 04-16, American Diner 04-17)
- Duration precision: ISO-8601 format with second-level accuracy (PT36M52S for 04-16, PT30M38S for 04-18, PT35M45S for 04-15)
- Shared expense equity split: HKUST 04-17 uses `equity:friends:` with negative posting for same-day splits
- ID mapping compliance: All 5 entries follow established `id_mappings.yml` patterns
- Food tag language preservation: Italian + Chinese names kept exact, no translation without approval
- All transactions balance correctly and validate with `bun run format && bun run check`

Key architectural change: For multi-entry requests (2+ transactions), main agent creates a todo list and invokes a separate subagent for each transaction to enable parallelization and focused scope. Subagents return formatted entries rather than directly editing files, which avoids merge conflicts and allows parallel processing. Main agent orchestrates merging, validation, and final formatting. This change scales gracefully from single entries to large batches.

### 2026-04-18 — Saizeriya QR-order metadata handling

Integrated → `.agents/instructions/continuous-learning.instructions.md`

### 2026-04-08 — Saizeriya and American Diner receipt header ID conventions

Integrated → `food_transactions.md`, `examples.md`, `id_mappings.yml`

### 2026-04-07 — Sushiro shared bill receipt and split pattern

Integrated → `examples.md`, `continuous-learning.instructions.md`

### 2026-03-10 — Tag formatting, language consistency, and Cafe 100% itemization

Integrated → `food_transactions.md`, `examples.md`, `id_mappings.yml`

### 2026-02-24 — Food formatting, Octopus matching, and payee/ID integration

Integrated → `food_transactions.md`, `examples.md`, `SKILL.md`, `match-octopus-statement-transactions/SKILL.md`, `upsert-octopus-transactions/lessons.md`, `specialized_transaction_import.md`, `id_mappings.yml`, `payee_mappings.yml`

Covers: complimentary coffee & 配-prefix splitting, Octopus/eDDA statement matching refinements, itemization clarification, zero-priced drink posting, payee/ID fixes, and gifts/red-packet examples.
