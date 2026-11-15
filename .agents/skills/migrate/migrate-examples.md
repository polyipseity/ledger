# migrate — examples

Two boundaries in the shape the tool writes them, and one month whose closing went missing. Accounts, UUIDs, and amounts are placeholders; the invariant in `./SKILL.md` is what the figures have to satisfy.

## A clean month

`uv run --locked -m scripts.clopen close 2025-12` appends the closing to `ledger/2025/2025-12/self.journal` and inserts the opening into `ledger/2026/2026-01/self.journal` after its `include` line, creating that journal from the December one's `include` lines when it does not exist yet.

```hledger
2025-12-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:banks:<bank-uuid>:HKD savings        1 000.00 HKD = 0.00 HKD
    assets:cash                                   200.00 HKD = 0.00 HKD
    liabilities:credit cards:<card-uuid>         -500.00 HKD = 0.00 HKD
    equity:opening/closing balances

2026-01-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:banks:<bank-uuid>:HKD savings        1 000.00 HKD = 1 000.00 HKD
    assets:cash                                   200.00 HKD = 200.00 HKD
    liabilities:credit cards:<card-uuid>         -500.00 HKD = -500.00 HKD
    equity:opening/closing balances
```

`uv run --locked -m scripts.clopen verify` reports no defect for these two months, and `bun run check` passes on the reflowed file.

## A missing closing

The same December journal, holding those three balances and no boundary, verifies as:

```text
ledger/2025/2025-12/self.journal:2025-12: missing_closing: no closing balances transaction
```

`uv run --locked -m scripts.clopen close 2025-12` then writes the pair above, `bun run format:journal` reflows it, and the verifier reports no defect. The opening is written in the same run as the closing, so the pair never exists half-made; `./migrate-repair.md` has the case where it already did.
