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

| Anti-Pattern                                | Symptom                                                   | Fix                                                                                                                 | Priority     |
| ------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------ |
| **Editing year-level journals**             | Transactions out of monthly hierarchy                     | Always edit `ledger/YYYY/YYYY-MM/*.journal`; year files are includes only                                           | **CRITICAL** |
| **Out-of-chronological-order transactions** | Validation fails; reports out-of-order; hledger confusion | Always insert transactions in strict date+time order; use `.agents/instructions/transaction-format.instructions.md` | **CRITICAL** |
| **Missing timezone tags**                   | Ambiguous transaction times; breaks reporting             | Every transaction MUST have `timezone: UTC+08:00` in comment                                                        | **CRITICAL** |
| **Payees declared in monthly journals**     | Duplicate payees; validation fails                        | **Always** declare payees in `preludes/self.journal` only, alphabetized                                             | **CRITICAL** |
| **Payees out of lexicographical order**     | Merge conflicts; maintenance issues                       | Check entire payee section; insert any new payee in correct ASCII order                                             | **HIGH**     |
| **Accounts out of lexicographical order**   | Same as payees                                            | Check entire account section; move any out-of-order entries                                                         | **HIGH**     |
| **Committing without validation**           | Downstream validation failures; CI blockers               | Always run `bun run format && bun run check` before commit                                                          | **HIGH**     |

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

| Anti-Pattern                                        | Symptom                                             | Fix                                                                                           | Priority     |
| --------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------ |
| **Guessing matches (Pass 1)**                       | Duplicates; incorrect duration                      | Match **only** on date + amount + time (±1.5 hrs); ignore payee/merchant/tags                 | **CRITICAL** |
| **Filtering Pass 1 by payee name**                  | Missed matches; unintended duplicates               | **Absolutely ignore** merchant/payee/nature; check **every** journal entry by date+amount     | **CRITICAL** |
| **Forgetting to update `duration:` when matching**  | Time tracking incomplete; pass 1 errors             | When matching: if journal entry has `time:` but no `duration:`, add duration tag              | **HIGH**     |
| **Updating duration but leaving it out of comment** | Validation failure; missing metadata                | Duration MUST be inserted into the header comment, between `time:` and `timezone:`            | **HIGH**     |
| **Not checking if duration already exists**         | Overwriting intentional durations; fixes needed     | **Most frequently overlooked rule:** If journal entry already has `duration:`, leave it alone | **HIGH**     |
| **Adding transactions in Pass 1**                   | Duplicates; confused workflow                       | Pass 1 = match existing only; Pass 2 = add new only; never mix                                | **CRITICAL** |
| **Skipping todo list for multi-step upsert**        | Confusion; incomplete work; lost progress           | Always use `manage_todo_list` to track Pass 1, Pass 2, validation, commit separately          | **MEDIUM**   |
| **Not asking for mapping clarification**            | Wrong payee; privacy violations; later fixes needed | If any payee mapping is missing, ambiguous, or contextually unclear, stop and ask             | **CRITICAL** |

---

## 💡 Lessons Learned by Workflow

### Add Transactions Skill

**Dating & time ordering (2026-03-28):**

- Genki Sushi entry: receipt/table pair ID format refined; always check `id_mappings.yml` for format rules
- TamJai SamGor: base meal + modifier metadata (不要芽菜/不要韭菜/不要腐皮) must be explicit for all repeated combos

**Saizeriya & American Diner (2026-04-08):**

- Receipt header ID conventions now in `id_mappings.yml`; update mapping when adding new payee receipts

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

**Prelude ordering (Ongoing):**

- Payees and accounts must stay in strict lexicographical order
- When editing, scan entire section for out-of-order entries and correct proactively

**Balance assertions (Ongoing):**

- Use on sensitive postings (transfers, loans) to catch entry errors early
- Closing transactions must assert all accounts to `= 0.00 CURRENCY`

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

---

## 📋 Continuous Improvement Process

### Adding New Lessons

1. **Discover a pattern** (through use or bug fix)
2. **Document it here** as a dated bullet under the relevant workflow section
3. **Integrate into canonical file** (SKILL.md, theme file, examples.md, or mapping YAML)
4. **Replace lesson with pointer** (e.g., "Archived → See examples.md#section-name")
5. **Keep this file concise** (single-screen target)

### Pruning Outdated Patterns

- Review lessons quarterly or when the system has stabilized
- Move confirmed best practices into `SKILL.md` main sections
- Remove lessons that are no longer relevant
- Update examples with edge cases discovered

---

## Related Documentation

- [Agent Quick Start](./agent-quickstart.instructions.md) — Checklist for getting started
- [add-transactions skill](../skills/add-transactions/SKILL.md) + lessons.md — Food, lending, specialized imports
- [upsert-octopus-transactions skill](../skills/upsert-octopus-transactions/SKILL.md) + lessons.md — Two-pass workflow, duration rules
- [edit-journals skill](../skills/edit-journals/SKILL.md) + lessons.md — Editing best practices
- [Transaction Format](./transaction-format.instructions.md) — Canonical transaction structure & tags
- [Editing Guidelines](./editing-guidelines.instructions.md) — Account/payee ordering, chronological rules
- [Security](./security.instructions.md) — Confidential data handling
