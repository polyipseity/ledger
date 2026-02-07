---
name: upsert-octopus-transactions
description: Strict, step-by-step workflow for upserting Octopus card transactions to the ledger. Requires explicit user clarification for any ambiguity. Enforces contextual matching, mapping, and privacy rules. No guessing or inference allowed.
---

# Upsert Octopus Transactions Skill

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Prefer `typing.Self` for methods that return the instance type (for example: `def clone(self) -> typing.Self:`); if supporting Python versions older than 3.11, use `typing_extensions.Self`. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. Avoid using `Any` or `Unknown` in type annotations; prefer explicit types, Protocols, or TypedDicts. Exception: `Any` or `Unknown` may be used only when there is a very strong, documented justification (for example, interfacing with untyped third-party libraries or representing truly dynamic/opaque data structures). When used, include an inline comment explaining the justification and a `# TODO` to refine the type later. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

## 🚩 Absolute Rules for Agents

**You must follow every step below, in order, with no exceptions.**

- **Journal file paths must always include the full prefix `ledger/`.** Never omit it.
- **Never guess, infer, or assume.** If anything is ambiguous, unclear, or missing, you must stop and ask the user for clarification before proceeding.
- **Always use the todo list tool** to break down the process, mark each step as in-progress/completed, and update after every change.
- **Always use two strict passes**: Pass 1 for matching and updating existing transactions only, Pass 2 for adding new transactions only. For todos, label them clearly as Pass 1 or Pass 2.
- **Never prepare or transcribe any hledger journal transactions until Pass 2.** This is critical to avoid mixing up updates and additions.
- **Never skip a mapping, privacy, or contextual check.**

**Definitions:**

- **Octopus transactions** are the transactions in the raw data (e.g., from statements, screenshots, or app exports).
- **Journal transactions** are the transactions in the hledger journal files and those that should be produced by the agent.

## 1. Preparation: Load All Context

1. **You must always read the confidential payee mapping file**: `private.yaml`, and ensure you understand which payees are confidential and require UUIDs. This must always be remembered for correct payee handling.
2. **You must always read the payee mapping file**: `.github/skills/upsert-octopus-transactions/payee_mappings.yml`. This must always be referenced for correct payee mapping.
3. **Process Octopus transactions strictly in chronological order (earliest to latest).** See `.github/instructions/transaction-format.instructions.md` for the canonical chronological rules.
   - Do not transcribe or prepare any journal transactions from the Octopus transactions until Pass 2.
4. **If any mapping is missing, ambiguous, or unclear,** you must ask the user for the correct mapping and update the file before continuing. **Never guess.**
5. **For confidential payees,** after mapping, must check `private.yaml` for a UUID. If a UUID exists, use it as the payee in the journal. **Never expose confidential names.**
6. At this point, **if the user has NOT explicitly provided a journal file snippet, you must read the entire current month's journal file** (`ledger/[year]/[year]-[month]/self.journal`). You must NOT read only a subset, or you may miss existing journal transactions. Do NOT forget the prefix `ledger/`.

## 2. Two-Pass Upsert Workflow (MANDATORY)

To ensure correct upserting, you **must** process Octopus transactions in two strict passes. You must make no changes in Pass 1 other than updates to existing journal transactions. You must make no changes in Pass 2 other than adding new journal transactions. These two passes must be strictly separated.

### Pass 1: Match and Update Only

During pass 1, do not transcribe or prepare journal transactions. Keep the Octopus transactions as-is for now. For each Octopus transaction (in chronological order):

- For each Octopus transaction, you must check every journal entry for the correct amount and date, regardless of payee/merchant or any other field. Never filter or restrict by payee/merchant name. **Absolutely ignore merchant names, payee names, activity, tags, and the nature or type of the transaction except for the reload/transfer exclusion above. Even if the merchant/payee/nature do not match or seem unrelated, you must still match if date and amount match, and time is within ±1.5 hours. Only date and amount are primary, time is secondary, and all other considerations are tertiary and must be ignored.**
  - For transport transactions, **require exact date, time (allow up to 1 minute rounding), and payee (must use payee mapping if present).** Duration is never added or updated for transport.
  - For Octopus reload/transfer transactions, **never attempt to match or update existing journal entries in Pass 1. Always add them in Pass 2, following the reload pattern (self-to-self transfer between Octopus card and Octopus account).**
- A match only exists if date, amount, and time (±1.5 hours) all match. All three are required. Before confirming every potential match, you must always re-confirm the match by re-reading the hledger journal entry header line to confirm. Never use previous reads. Try very hard to confirm the match. If you cannot confirm even after trying very hard, discard the candidate.
- **A very important matching heuristic:** Ignoring the sign of the amount, transactions more expensive than or equal to $25 are very likely to be dining or eating transactions, which **almost always have matches**. Transactions less than $25 are very likely to be transport or small purchases, which **almost always do NOT have matches**. Use this heuristic to help confirm matches, but do not use it as a strict rule.
- If there are multiple journal entries with the same date and amount, each Octopus transaction must be matched to a unique journal entry, even if the payee, merchant, or time is different (as long as within ±1.5 hours).
- If there is a match, apply the update for a match individually using a tiny precise patch to existing journal transactions only. See below. If no match is found, apply the payee mapping logic to attempt the previous steps for exactly once again. **After this, if no match is found finally, do nothing in this pass.**
- **Do not add any new transactions in this pass.**

After each match, apply the update for a match individually using a tiny precise patch to existing journal transactions only.

- If a journal entry’s time is earlier and the Octopus time is later, and the journal entry has a `time:` tag but no `duration:`, calculate and add a `duration:` tag (Octopus time - journal time) if the difference is ≥2 minutes. If the difference is <2 minutes, do not update.
      - If the journal entry already has a `duration:`, do not update it.
      - **IMPORTANT: When adding a `duration:` tag, you must insert it directly into the transaction header comment, immediately after the `time:` field and before the `timezone:` field. Do not add a new line or posting. Only the header comment is updated.**

### Worked Examples: Pass 1 (Update Only)

#### Example 1: Union Cash Register Co. Ltd. (Octopus) → Cafe 100% (Journal)

**Octopus transaction:**

| Date         | Time   | Merchant                     | Amount |
|--------------|--------|------------------------------|--------|
| 2026-01-24   | 12:11  | Union Cash Register Co. Ltd. | -35.0  |

**Payee mapping:**
Union Cash Register Co. Ltd. → Cafe 100%

**Journal entry before:**

```hledger
2026-01-24 (41210539, 12) Cafe 100%  ; activity: eating, eating: breakfast, time: 11:27:42, timezone: UTC+08:00
   expenses:food and drinks:dining                                         35.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -35.00 HKD
```

**Matching logic:**

- Date matches (2026-01-24)
- Amount matches (35.00)
- Time within ±1.5 hours (11:27:42 vs 12:11)
- Payee mapping: Octopus merchant → journal payee

**Update rule:**

- If the Octopus time is later and the journal entry has a `time:` tag but no `duration:`, and the difference is ≥2 minutes, add a `duration:` tag (duration = Octopus time - journal time).
- If the journal entry already has a `duration:`, do not update.
- Do not change payee, merchant, or other fields.

**Journal entry after (if duration needed):**

```hledger
2026-01-24 (41210539, 12) Cafe 100%  ; activity: eating, eating: breakfast, time: 11:27:42, duration: PT43M, timezone: UTC+08:00
   expenses:food and drinks:dining                                         35.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -35.00 HKD
```

#### Example 2: Union Cash Register Co. Ltd. (Octopus) → Cafe 100% (Journal, different amount)

**Octopus transaction:**

| Date         | Time   | Merchant                     | Amount |
|--------------|--------|------------------------------|--------|
| 2026-01-24   | 18:11  | Union Cash Register Co. Ltd. | -39.0  |

**Payee mapping:**
Union Cash Register Co. Ltd. → Cafe 100%

**Journal entry before:**

```hledger
2026-01-24 (?, 52) Cafe 100%  ; activity: eating, eating: dinner, time: 17:34:45, timezone: UTC+08:00
   expenses:food and drinks:dining                                         39.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -39.00 HKD
```

**Matching logic:**

- Date matches (2026-01-24)
- Amount matches (39.00)
- Time within ±1.5 hours (17:34:45 vs 18:11)

**Update rule:**

- If the Octopus time is later and the journal entry has a `time:` tag but no `duration:`, and the difference is ≥2 minutes, add a `duration:` tag (duration = Octopus time - journal time). Include seconds in the duration.

**Journal entry after (if duration needed):**

```hledger
2026-01-24 (?, 52) Cafe 100%  ; activity: eating, eating: dinner, time: 17:34:45, duration: PT36M15S, timezone: UTC+08:00
   expenses:food and drinks:dining                                         39.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -39.00 HKD
```

#### Example 3: Pin Me Limited (Octopus) → Comebuytea (Journal)

**Octopus transaction:**

| Date         | Time   | Merchant        | Amount |
|--------------|--------|-----------------|--------|
| 2026-01-24   | 22:55  | Pin Me Limited  | -39.0  |

**Payee mapping:**
Pin Me Limited → Comebuytea

**Journal entry before:**

```hledger
2026-01-24 (2026012422550754619, 1082) Comebuytea  ; activity: eating, eating: drinks, time: 22:54:45, timezone: UTC+08:00
   expenses:food and drinks:drinks                                         39.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -39.00 HKD
```

**Matching logic:**

- Date matches (2026-01-24)
- Amount matches (39.00)
- Time within ±1.5 hours (22:54:45 vs 22:55)
- Payee mapping: Pin Me Limited → Comebuytea

**Update rule:**

- If the Octopus time is later and the journal entry has a `time:` tag but no `duration:`, and the difference is ≥2 minutes, add a `duration:` tag (duration = Octopus time - journal time). In this case, the duration is 15 seconds, so do not update.

**Journal entry after (if duration needed):**

```hledger
2026-01-24 (2026012422550754619, 1082) Comebuytea  ; activity: eating, eating: drinks, time: 22:54:45, timezone: UTC+08:00
   expenses:food and drinks:drinks                                         39.00 HKD  ; food_or_drink: ...
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -39.00 HKD
```

### Pass 2: Add Unmatched Transactions

Only in pass 2, transcribe or prepare journal transactions for any Octopus transactions that were not matched in pass 1. At this point, you must remember all payee mapping and confidentiality rules.

1. For each Octopus transaction that was not matched in Pass 1:
   - **Must check the payee mapping file for the merchant name.** If missing, ambiguous, or one-to-many and context is insufficient, ask the user for the correct mapping and update the file before proceeding.
   - For confidential payees, after mapping, check `private.yaml` for a UUID and use it in the journal. Never expose confidential names.
   - Add a new journal transaction using the mapping. Insert transactions in strict chronological order (see `.github/instructions/transaction-format.instructions.md`).
      - For vending machine transactions (e.g., Swire), use `expenses:food and drinks:drinks` as the expense account.
      - For bus transport transactions (Kowloon Motor Bus/Long Win Bus), also record the reward accrual and revenue postings. Add an `assets:accrued revenues:rewards` posting with the fare amount in `_PT/E` (positive) and a corresponding `revenues:rewards` posting with the negative same amount in `_PT/E`. This ensures accumulated reward points are tracked consistently for bus fares.
   - For each new payee, register it in `preludes/self.journal` (alphabetized); for confidential payees register the UUID. See `add-payee` skill for process.
   - If any ambiguity exists, ask the user for clarification.

**Never add a transaction in Pass 1. Never update an existing transaction in Pass 2.**

### Worked Example: Pass 2 (Add Only)

#### Example: (confidential payee) (Octopus) → (confidential payee) (Journal, UUID)

**Octopus transaction:**

| Date       | Time  | Merchant             | Amount |
| ---------- | ----- | -------------------- | ------ |
| 2026-01-25 | 12:38 | (confidential payee) | -78.0  |

**Payee mapping:**
(confidential payee) → (confidential payee) (UUID: a2ccd533-7a2e-4fa1-ad63-e4f1d3bdc159)

**Journal entry before:**
_(No matching entry exists)_

**Action in Pass 2:**

- Add a new journal transaction in strict chronological order.
- Use the mapped payee (UUID for confidential payees).
- Register the new payee in `preludes/self.journal` if not already present.

**Journal entry after:**

```hledger
2026-01-25 a2ccd533-7a2e-4fa1-ad63-e4f1d3bdc159  ; activity: medical, time: 12:38, timezone: UTC+08:00
   expenses:healthcare:medication                                       78.00 HKD
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521   -78.00 HKD
```

## 3. Transaction Formatting and Insertion

- Insert new transactions in strict chronological order within the journal file.
- Within each transaction, order postings with debits first (increases), then credits (decreases).
- For each new payee, register it in `preludes/self.journal` (alphabetized). For confidential payees, register the UUID.
- **If any ambiguity exists in transaction details, ordering, or payee registration, ask the user for clarification.**

## 4. Validation and Commit

- After all changes, run formatting and validation scripts:

   ```powershell
   python -m format   # set cwd to scripts/
   python -m check    # set cwd to scripts/
   ```

**Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical guidance — prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

- Review changes and commit using the correct ledger commit header.
- **If any error or ambiguity arises during validation, ask the user for clarification.**

## 5. Examples of When to Ask for Clarification

- The Octopus merchant name is not in the mapping file.
- The mapping file gives multiple possible payees and context is insufficient to choose.
- The Octopus transaction time is close to multiple journal entries and it is unclear which to match.
- The payee is confidential but no UUID is found in `private.yaml`.
- The transaction amount or type is unusual or does not fit known patterns.
- The reload source is unclear (e.g., bank email not provided).
- The food/drink items are unknown for a dining transaction.
- Any other detail is missing, ambiguous, or could be interpreted in more than one way.

**In all such cases, STOP and ask the user for clarification before proceeding.**

## 6. Anti-Patterns (STRICTLY FORBIDDEN)

- Never guess or infer a mapping or payee.
- Never add a transaction if a contextual match exists (in Pass 1).
- Never update a transaction in Pass 2.
- Never expose confidential payee names in the journal.
- Never add a transaction for 八達通轉賬 (typo: 八達通專帳) as payee—always map.
- Never skip the todo list tool for multi-step work.
- Never proceed past any ambiguity—always ask the user.

## 7. Summary Table (Strict Two-Pass)

| Pass   | Octopus Transaction (date & amount primary, time secondary, all else ignored) | Contextual Match in Journal? | Action                                   |
| ------ | ----------------------------------------------------------------------------- | ---------------------------- | ---------------------------------------- |
| Pass 1 | Date, amount, ±2hr (ignore all merchant/payee/nature differences)             | Yes                          | Update existing journal transaction only |
| Pass 1 | Date, amount, ±2hr (ignore all merchant/payee/nature differences)             | No                           | Do nothing                               |
| Pass 2 | (Unmatched from Pass 1)                                                       | N/A                          | Add new transaction using mapping        |

## 9. Final Checklist

- [ ] All mappings checked and clarified with user if needed
- [ ] All contextual matches checked, no duplicates
- [ ] All durations updated where required
- [ ] All confidential payees use UUIDs
- [ ] All new payees registered in prelude
- [ ] All transactions in strict chronological order
- [ ] All ambiguities resolved by asking the user
- [ ] All changes validated and committed

**If you are ever unsure, always ask the user for clarification before proceeding.**
