---
name: Continuous Learning & Common Pitfalls
description: Consolidated guide to lessons learned, anti-patterns to avoid, and best practices refined through repeated use of the ledger system.
---

# Continuous Learning & Common Pitfalls 📚

This file consolidates lessons, anti-patterns, and continuous improvements discovered across all skills and workflows. It serves as a reference for both agents and maintainers to avoid recurring mistakes and apply proven practices.

**Update frequency:** Add new learnings here after discovering patterns or fixes; maintain pointers to canonical files where rules are authoritative.

---

## 🔧 Critical System Patterns (Highest Priority)

### Script Execution: Working Directory is the Most Common Error

**Lesson:** Running scripts from the wrong working directory causes include errors, missing files, and incorrect results.

**Rule:**

- **Always prefer `bun run <script>`** from repo root (sets up environment automatically)
- **Only use `python -m scripts.<cmd>` when no `bun run <script>` wrapper exists**
- **When using Python directly, set `cwd=scripts/`** in tool parameters
- **For `hledger close --migrate`, run from repo root**
- When creating temporary journals for diagnosis, put the temp file in the same journal directory or run hledger from that directory so relative `include` paths resolve correctly.
- When running multi-line Python or shell diagnostics, be mindful of the current shell. Avoid Bash-style heredoc syntax such as `python - <<'PY'` in PowerShell and prefer `python -c` or a temp script file instead.

**Examples of wrong vs. right:**

```powershell
# ❌ Wrong: python script from wrong directory
python -m format

# ✅ Right: Use bun wrapper from repo root
bun run format

# ✅ Right: Python direct with correct cwd
# Tool: set cwd=scripts/, then run: python -m format
```

**Antipattern registry:**

- Running `python -m check` from repo root (fails to find includes)
- Using `ux run ...` or other shortcuts (not reliable)
- Assuming the current directory is correct without checking

---

## 📝 Duplicated Guidance: Validation & Formatting

### When and How to Validate

**Consolidated rule:** Run **`bun run format` BEFORE `bun run check`**. Formatting often fixes validation errors automatically.

**Boundary rule:** When correcting a month-end closing balance, validate the corrected month and the following month together so the opening balances match the corrected closing balances.

### Pre-commit Validation Checklist

1. **Format Markdown** (if editing instructions): `bun run markdownlint:fix`
2. **Format journals**: `bun run format`
3. **Validate journals**: `bun run check`
4. **Run tests**: `bun run test` (if editing code or instructions)
5. **Encrypt secrets**: `bun run encrypt` (if modified `private.yaml`)
6. **Stage & review**: `git status && git diff`
7. **Commit**: Follow `.agents/instructions/git-commits.instructions.md`

**Variant commands** (use when specific subsets needed):

- `bun run format:py` — Format Python only
- `bun run format:md` — Format Markdown only  
- `bun run format:hledger` — Format journals only
- `bun run check:py` — Validate Python types/linting only

---

## 🚫 Consolidated Anti-Patterns (Avoid These!)

### Journal Structure & Editing

| Anti-Pattern                                  | Symptom                                                   | Fix                                                                                                                 | Priority     |
| --------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------ |
| **Editing year-level journals**               | Transactions out of monthly hierarchy                     | Always edit `ledger/YYYY/YYYY-MM/*.journal`; year files are includes only                                           | **CRITICAL** |
| **Out-of-chronological-order transactions**   | Validation fails; reports out-of-order; hledger confusion | Always insert transactions in strict date+time order; use `.agents/instructions/transaction-format.instructions.md` | **CRITICAL** |
| **Missing timezone tags**                     | Ambiguous transaction times; breaks reporting             | Every transaction MUST have `timezone: UTC+08:00` in comment                                                        | **CRITICAL** |
| **Payees declared in monthly journals**       | Duplicate payees; validation fails                        | **Always** declare payees in `preludes/self.journal` only, alphabetized                                             | **CRITICAL** |
| **Payees out of lexicographical order**       | Merge conflicts; maintenance issues                       | Check entire payee section; insert any new payee in correct ASCII order                                             | **HIGH**     |
| **Accounts out of lexicographical order**     | Same as payees                                            | Check entire account section; move any out-of-order entries                                                         | **HIGH**     |
| **Committing without validation**             | Downstream validation failures; CI blockers               | Always run `bun run format && bun run check` before commit                                                          | **HIGH**     |
| **Running formatter on unparseable journals** | Formatting fails before it can normalize the file         | Fix syntax and invalid account or payee definitions before running `bun run format`                                 | **HIGH**     |

### Transaction Entry & Tagging

| Anti-Pattern                                  | Symptom                                  | Fix                                                                                                     | Priority     |
| --------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------ |
| **Inconsistent decimal precision**            | Formatting/validation noise              | After `bun run format`: all amounts use 2 decimals (e.g., `50.00 HKD`)                                  | **HIGH**     |
| **Missing or wrong status markers**           | Clarity issues; impacts lending tracking | Use `!` (pending) only for lending/borrowing; `*` (cleared) for verified; none for normal               | **MEDIUM**   |
| **Duplicate transactions (same date+amount)** | Overstated balances; confusion           | In Pass 1 of upsert, match existing entries before adding new ones; check time within ±1.5 hrs          | **MEDIUM**   |
| **Unencrypted `private.yaml` committed**      | Security breach                          | Always encrypt via `bun run encrypt` before commit; use `.agents/instructions/security.instructions.md` | **CRITICAL** |

### Code & Documentation

| Anti-Pattern                                       | Symptom                                           | Fix                                                                            | Priority   |
| -------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------ | ---------- |
| **Inline/runtime imports**                         | Static analysis failures; Ruff lint errors        | All imports at module top-level; use `from module import name` form            | **MEDIUM** |
| **Missing `__all__` exports**                      | Unclear public API; imports ambiguous             | Every Python module under `scripts/` MUST define `__all__` tuple at top        | **MEDIUM** |
| **Missing type annotations**                       | Pylance errors; type checker failures             | All public functions and test functions MUST include complete type annotations | **MEDIUM** |
| **Using `str(path)` instead of `os.fspath(path)`** | Path protocol violations; static checker warnings | Always use `os.fspath(path_like)` for filesystem path conversions              | **MEDIUM** |
| **Using `typing.Dict` instead of `dict`**          | Outdated style; inconsistency                     | Use `dict[K, V]` (PEP 585); use `collections.abc.Mapping` for ABCs             | **LOW**    |

### Payee & Transaction Mapping

| Anti-Pattern                                                 | Symptom                                 | Fix                                                                                | Priority     |
| ------------------------------------------------------------ | --------------------------------------- | ---------------------------------------------------------------------------------- | ------------ |
| **Guessing unmapped payee names**                            | Wrong payee; duplication; hard to audit | If a payee mapping is missing, ambiguous, or one-to-many, **ask the user first**   | **CRITICAL** |
| **Exposing confidential payee names**                        | Privacy breach; leaked personal data    | If `private.yaml` lists a payee UUID, **use the UUID in journals, never the name** | **CRITICAL** |
| **Payee mapping values not YAML lists**                      | Format error; incorrect structure       | All mapping values MUST be `[...]` sequences; single-element list for 1:1 mappings | **MEDIUM**   |
| **Identity mappings** (e.g., `"McDonald's": ["McDonald's"]`) | Redundant; clutter                      | Remove identity mappings; only map aliases or translations                         | **LOW**      |

### Food Transaction Entry

| Anti-Pattern                                              | Symptom                                  | Fix                                                                                              | Priority   |
| --------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------- |
| **Escaping quotes in `food_or_drink:` tags**              | Broken tags on format                    | Never escape quotes; write `"` directly in tag values                                            | **MEDIUM** |
| **Using commas in `food_or_drink:` tags**                 | Tag accidental splitting                 | Use semicolons (`;`) instead of commas (`,`) to avoid splitting into multiple tags               | **MEDIUM** |
| **Assuming zero-priced items without receipt evidence**   | Incorrect itemization                    | Only record zero-priced items if explicitly listed on receipt; never assume                      | **MEDIUM** |
| **Translating item names without mapping**                | Inconsistency; duplication; audit issues | If translation needed, update `food_translations.yml` first; preserve receipt language otherwise | **MEDIUM** |
| **Forgetting modifiers or using them as standalone tags** | Incomplete itemization; missing context  | Combine base item + modifiers using `+` (e.g., `奶茶 + 多奶`); never split                       | **MEDIUM** |

### Octopus Transaction Upsert

| Anti-Pattern                                        | Symptom                                             | Fix                                                                                                                                                    | Priority     |
| --------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| **Guessing matches (Pass 1)**                       | Duplicates; incorrect duration                      | Match **only** on date + amount + time (±1.5 hrs); ignore payee/merchant/tags                                                                          | **CRITICAL** |
| **Filtering Pass 1 by payee name**                  | Missed matches; unintended duplicates               | **Absolutely ignore** merchant/payee/nature; check **every** journal entry by date+amount                                                              | **CRITICAL** |
| **Forgetting to update `duration:` when matching**  | Time tracking incomplete; pass 1 errors             | When matching: if journal entry has `time:` but no `duration:`, add duration tag                                                                       | **HIGH**     |
| **Updating duration but leaving it out of comment** | Validation failure; missing metadata                | Duration MUST be inserted into the header comment, between `time:` and `timezone:`                                                                     | **HIGH**     |
| **Not checking if duration already exists**         | Overwriting intentional durations; fixes needed     | **Most frequently overlooked rule:** If journal entry already has `duration:`, leave it alone                                                          | **HIGH**     |
| **Adding transactions in Pass 1**                   | Duplicates; confused workflow                       | Pass 1 = match existing only; Pass 2 = add new only; never mix                                                                                         | **CRITICAL** |
| **Skipping todo list for multi-step upsert**        | Confusion; incomplete work; lost progress           | Always use `manage_todo_list` to track Pass 1, Pass 2, validation, commit separately                                                                   | **MEDIUM**   |
| **Failing to update next-month openings**           | Month boundary balances disagree                    | After month-end closing fixes, update the next month's `opening balances` to match the corrected closing balances and verify both months with hledger. | **HIGH**     |
| **Not asking for mapping clarification**            | Wrong payee; privacy violations; later fixes needed | If any payee mapping is missing, ambiguous, or contextually unclear, stop and ask                                                                      | **CRITICAL** |

---

## 💡 Lessons Learned by Workflow

### Add Transactions Skill

**Dating & time ordering (2026-03-28):**

- Genki Sushi entry: receipt/table pair ID format refined; always check `id_mappings.yml` for format rules
- TamJai SamGor: base meal + modifier metadata (不要芽菜/不要韭菜/不要腐皮) must be explicit for all repeated combos

**Saizeriya & American Diner (2026-04-08):**

- Receipt header ID conventions now in `id_mappings.yml`; update mapping when adding new payee receipts
- Saizeriya QR-order metadata lines should not be recorded.

**Food transaction pattern validation (2026-04-18):**

- **Zero-priced itemization consistency:** TamJai SamGor (04-16) and American Diner (04-17) validated pattern: each bundled meal component gets its own posting line + `food_or_drink:` tag, even if zero-priced. Saizeriya entries (04-15, 04-18) show simple two-line structure (2 paid items + 1 payment). Consistency rule: preserve receipt structure exactly—do not collapse or group postings beyond what's printed. See `food_transactions.md` for detailed rule.
- **Duration precision:** TamJai (04-16) PT36M52S (order 10:27:01 → checkout ~11:03:53) and Saizeriya (04-18) PT30M38S (order 12:27:18 → checkout ~12:57:56) validate second-level precision. Always calculate from receipt timestamps + explicit UTC+08:00 timezone tag. Format as ISO-8601 `duration:` in transaction header. See `food_transactions.md` for rule.
- **Shared expense equity vs. liability:** HKUST ramen (04-17) demonstrates immediate same-day split: itemizes dining + drinks postings, then adds single `equity:friends:4491140b-7e34-48fe-8e3d-aca591ed6d6e` posting with -50.50 HKD (negative = friend's share offset). Contrast with deferred reimbursements (2026-04-04 DZô DZô on credit): use `liabilities:credit cards:` + pending `!` marker + settlement assertion. See `lending_borrowing_transactions.md` for distinction rule.
- **Food tag language preservation:** Saizeriya entries preserve Italian-style names (意式野菜烤蛋, A香蒜辣汁野菌西蘭花), American Diner preserves Chinese + dish-code (G.鮮蘑菇炒蛋). No translation without approval. See `food_transactions.md` for rule.
- **ID mapping compliance:** All 5 entries follow `id_mappings.yml` ordering: Saizeriya (receipt_id, table_number), American Diner (receipt_id, kiosk_code), TamJai (receipt_id, table_id). No new mappings required; existing rules applied correctly across multiple transactions. Validates established patterns are working at scale.

**Sushiro shared bill splitting (2026-04-07):**

- Keep the receipt ID in the header, split the bill into full item/fee postings, and balance the other person's share with negative expense postings plus `equity:friends:<uuid>`

**Tag formatting & language consistency (2026-03-10):**

- Cafe 100% itemization rule: always check receipt for zero-priced items; never assume
- Preserve original receipt language in food tags; only translate via `food_translations.yml`

**Complimentary items & prefix splitting (2026-02-24):**

- Never assume complimentary coffee; only record if on receipt
- 配-prefix splitting: follow `food_transactions.md` rules for base item + modifiers

**Itemization & zero-priced drinks (2026-02-20):**

- Zero-priced drink postings: evidence required; incorporated into `food_transactions.md` examples

**Payee & ID fixes (2026-02-19):**

- Validate all IDs against `id_mappings.yml` prior to entry
- Discovered patterns: Octopus Genki, Cafe 100%, Saizeriya all have standardized formats

**Lending & group expenses (Ongoing):**

- Shared expense pattern: Itemize + add `equity:friends:<uuid>` for splits + liability posting for balance
- Repayment: debit asset, credit liability, assert to zero
- For new friends: use placeholder UUID; update once real UUID assigned

### Upsert Octopus Transactions Skill

**Octopus/eDDA statement matching (2026-02-22):**

- Never use debtor-reference tokens; match with FRN/transfer IDs + timestamp + amount
- Bank→wallet verification rules: see `specialized_transaction_import.md`

**Duration tag insertion (2026-02-22):**

- When matching Octopus end-time rows: add `duration:` only if no duration exists
- **Most critical rule:** Do not overwrite intentional durations
- Duration must land in comment, between `time:` and `timezone:`

**KMB & vending machine patterns (2026-02-19):**

- KMB (Kowloon Motor Bus): record reward accrual + revenue posting; see examples
- Vending (Swire): use `expenses:food and drinks:drinks`; no reward accrual
- Public Light Bus: no reward accrual

**Payee mapping & matching (2026-02-20):**

- 其他 merchant: was duplicate Cafe 100% breakfast entry; added to mappings
- When ambiguous: ask user before proceeding

**Matching heuristic (Consolidated):**

- Transactions ≥ $25: almost always have matches (dining/eating)
- Transactions < $25: almost always do NOT have matches (transport/small purchases)
- Use heuristic to help confirm matches; not a strict rule

### Edit Journals Skill

**Format & validation workflow (2026-02-08):**

- Prefer `bun run format` and `bun run check` (established pattern)
- Always run format before validate to reduce noisy failures
- `scripts.format` uses `hledger print`; if the file is not parseable or contains invalid accounts, formatting can fail before it runs. Fix ledger syntax and account declarations first.

**Prelude ordering (Ongoing):**

- Payees and accounts must stay in strict lexicographical order
- When editing, scan entire section for out-of-order entries and correct proactively

**Balance assertions (Ongoing):**

- Use on sensitive postings (transfers, loans) to catch entry errors early
- Closing transactions must assert all accounts to `= 0.00 CURRENCY`
- When correcting monthly closing balances, update the next month's `opening balances` immediately and validate both months together to avoid boundary mismatches.
- Small rounding mismatches (for example, 0.03 HKD) can still make a closing/opening block unbalanced; use the affected bank account's running balance to diagnose the precise adjustment.

### Validation Skill

**Format-then-check rule (Integrated):**

- Running `bun run format` first reduces validation failures by auto-fixing formatting issues
- Documented in `SKILL.md` as standard practice

---

## 🎯 Quick Reference: When to Ask for Clarification

Stop and ask the user in these situations:

1. **Payee not in mapping file** — demand clarification before proceeding
2. **Mapping has multiple candidates** and context is insufficient — ask which payee intended
3. **Octopus transaction time close to multiple journal entries** — ask which to match
4. **Aggregate/group bill total** that doesn't match any single posting — ask how to handle
5. **Confidential payee with no UUID in `private.yaml`** — ask for clarification
6. **Unusual amount or type** that doesn't fit known patterns — ask for context
7. **Missing reload source** (e.g., no bank email) — ask for clarification
8. **Unknown food/drink items** in dining transaction — ask for item details
9. **Any ambiguity in date, amount, payee, or posting** — ask; never guess
