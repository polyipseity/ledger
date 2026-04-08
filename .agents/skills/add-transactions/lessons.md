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

### 2026-04-08 — Saizeriya and American Diner receipt header ID conventions

Integrated → `food_transactions.md`, `examples.md`, `id_mappings.yml`

### 2026-04-07 — Sushiro shared bill receipt and split pattern

Integrated → `examples.md`, `continuous-learning.instructions.md`

### 2026-03-10 — Tag formatting, language consistency, and Cafe 100% itemization

Integrated → `food_transactions.md`, `examples.md`, `id_mappings.yml`

### 2026-02-24 — Complimentary coffee, 配-prefix splitting, and ordering discipline

Integrated → `food_transactions.md`, `examples.md`, `SKILL.md`

### 2026-02-22 — Octopus/eDDA statement matching refinements

Integrated → `match-octopus-statement-transactions/SKILL.md`, `upsert-octopus-transactions/lessons.md`, `specialized_transaction_import.md`

### 2026-02-20 — Itemization clarification and zero-priced drink posting

Integrated → `food_transactions.md`, `examples.md`, `payee_mappings.yml`

### 2026-02-19 — Payee/ID fixes and metadata cleanup

Integrated → `SKILL.md`, `id_mappings.yml`, `payee_mappings.yml`, `specialized_transaction_import.md`

### 2026-02-19 — Gifts/red-packet example expansion

Integrated → `examples.md`
