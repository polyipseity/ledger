# Upsert Octopus Transactions — Examples

Use these non-confidential, canonical worked examples when performing Pass 1 (update) and Pass 2 (add) workflows. Keep examples short and anonymized.

## Pass 1 (Update Only)

- Example: Octopus row 2026-01-24 12:11 amount 35.00 matches an existing journal transaction dated 2026-01-24 11:27:42.
  - Action: Re-open the journal, confirm date & amount match. If time difference ≥ 2 minutes and the journal entry has `time:` but no `duration:`, insert `duration: PT43M` immediately after `time:` in the header comment and run `pnpm run format` and `pnpm run check`. Do not change postings or payee. If ambiguous, stop and ask the user.

- Example (duration insertion): Octopus row 2026-02-09 09:34 amount 35.00 matches a journal transaction at 2026-02-09 09:01:31 (difference 32m29s).
  - Action: add `duration: PT32M29S` directly in the transaction header (immediately after `time:` and before `timezone:`). Run `pnpm run format` and `pnpm run check`.

  Worked header example:

  2026-02-09 (41215328, 13) Cafe 100%  ; activity: eating, eating: breakfast, time: 09:01:31, duration: PT32M29S, timezone: UTC+08:00
      expenses:food and drinks:dining                                         35.00 HKD
      assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -35.00 HKD

## Pass 2 (Add Only)

- Example: Unmatched Octopus row 2026-01-25 12:38 amount 78.00 for a confidential payee.
  - Action: Check `payee_mappings.yml` and `private.yaml`. If a UUID exists, use it; if not, ask the user. Register any new payee in `preludes/self.journal`, insert the new transaction in strict chronological order, run `pnpm run format` and `pnpm run check`, and commit with the single-line ledger header (e.g., `ledger(self.journal): add 1 transaction(s)`).

- Example (group-bill mismatch — ask the user): Octopus row 2026-02-10 20:00 amount 300.00 HKD; the journal contains two separate postings (100.00 HKD and 200.00 HKD) representing per-person shares.
  - Action: **Do not** match the Octopus aggregate total to any individual posting or attempt to split automatically. Stop and ask the user whether the Octopus row should be left unmatched, applied to one of the existing postings, or transcribed as a new aggregated transaction. Add a worked-note to `lessons.md` if the chosen action is to be repeated in future imports.

- Example (KMB fare with reward accrual): Octopus row 2026-02-13 13:25 amount 10.00 for a Kowloon Motor Bus fare.
  - Action: Add transport posting plus reward accrual and revenue reversal as separate postings so reward points are tracked.

  Worked posting example:

  2026-02-13 Kowloon Motor Bus/Long Win Bus  ; activity: transport, time: 13:25, timezone: UTC+08:00
      expenses:transport:buses                                                10.00 HKD
      assets:accrued revenues:rewards                                        10.00 _PT/E
      assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -10.00 HKD
      revenues:rewards                                                      -10.00_PT/E
- Example (public light bus — Pass 2 add): Octopus row 2026-02-14 21:21 amount 8.80 `專線小巴`/`public light bus`.
  - Action: Map merchant name to `public light bus` (use existing payee). Add a single transport posting; **do not** add KMB-style reward accrual for public light bus.

  Worked posting example:

  2026-02-14 public light bus  ; activity: transport, time: 21:21, timezone: UTC+08:00
      expenses:transport:buses                                                 8.80 HKD
      assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -8.80 HKD
- Example (vending-machine mapping → Swire): Octopus row 2026-02-09 20:09 amount 4.00 `太古可口可樂`.
  - Action: Map merchant name to `Swire` in `payee_mappings.yml` and add a simple consumption posting.

  Worked posting example:

  2026-02-09 Swire  ; activity: consumption, time: 20:09, timezone: UTC+08:00
      expenses:food and drinks:drinks                                         4.00 HKD
      assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521      -4.00 HKD

## Worked Example (Conceptual)

```hledger
2026-01-25 a2ccd533-7a2e-4fa1-ad63-e4f1d3bdc159  ; activity: medical, time: 12:38, timezone: UTC+08:00
   expenses:healthcare:medication               78.00 HKD
   assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521   -78.00 HKD
```

**See also:** Pass 1 examples above and the matching heuristics in `SKILL.md`.

## When to ask for clarification

- Mapping missing or ambiguous
- Multiple candidate matches by date/amount/time
- Confidential payee without UUID
- Unclear reload source or unusual amounts

---

When adding a new worked example, append a one-line note to `./lessons.md` explaining why the example was added and any rule it illustrates.
