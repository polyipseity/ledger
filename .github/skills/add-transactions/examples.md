# Add Transactions — Canonical Examples

This file collects canonical, non-confidential worked examples for the Add Transactions skill. Use these for guidance, tests, and to standardize examples across aspect files.

## 1. Food: Drink with Modifiers

Original: 冰蜜檸檬綠茶, 去冰, 7分甜

Result (posting comment only):

```text
expenses:food and drinks:dining  28.00 HKD  ; food_or_drink: 冰蜜檸檬綠茶 + 去冰 + 7分甜
assets:digital:Octopus cards:...      -28.00 HKD
```

Notes: combine base item and modifiers with `+` and keep tags in posting comments only.

## 2. Lending/Borrowing: Pending → Cleared

```hledger
2026-01-15 ! Friend Lunch                    # Pending loan to friend
  assets:loans:friends:<uuid>      50.00 HKD
  assets:cash                     -50.00 HKD

2026-01-20 * Friend Lunch                    # Cleared when repaid
  assets:loans:friends:<uuid>      50.00 HKD = 0.00 HKD
  assets:banks:<bank-uuid>        -50.00 HKD
```

Notes: only the original loan uses a status marker; the repayment transaction has no marker and uses an assertion (`= 0.00`).

## 3. Currency Conversion

```hledger
2026-01-10 Currency Exchange  ; activity: transfer, time: 14:30:00, timezone: UTC+08:00
  equity:conversions:HKD-USD:HKD                   -1 000.00 HKD  ; 1000 HKD → 130 USD, rate: 0.1300
  assets:banks:...:HKD                             1 000.00 HKD
  equity:conversions:HKD-USD:USD                     130.00 USD
  assets:banks:...:USD                             -130.00 USD
```

Notes: record the rate in a comment and use `equity:conversions` accounts to balance currencies.

## 4. Platform Transaction (Masked Payee)

```hledger
2026-01-15 * (pi_1A2B3C4D5E6F) **********@*******.com  ; activity: donation, time: 12:34:56, timezone: UTC+08:00
  equity:conversions:HKD-USD:USD                      20.00 USD  ; rate: 7.80000
  assets:digital:Stripe:<uuid>                       156.00 HKD
  expenses:fees:Platform                              6.00 HKD
  expenses:fees:Stripe                                8.00 HKD
  equity:conversions:HKD-USD:HKD                    -170.00 HKD
  revenues:donations:Platform:projectX              -20.00 USD
```

Notes: post net amounts to platform asset accounts and mask donor identifiers as specified.

## 5. Platform Payout

```hledger
2026-01-20 (payout_id_123, po_1Z9Y8X7W6V) Stripe  ; activity: payout, time: 15:10:10, timezone: UTC+08:00
  assets:banks:<bank-uuid>:HKD savings       156.00 HKD
  assets:digital:Stripe:<uuid>              -156.00 HKD = 0.00 HKD
```

Notes: assert platform account to zero; use `activity: payout` and second precision time when available.

## 6. Transport Reward Accrual

```hledger
2026-01-01 Kowloon Motor Bus/Long Win Bus  ; activity: transport, time: 23:59, timezone: UTC+08:00
    expenses:transport:buses                         5.90 HKD
    assets:accrued revenues:rewards                 5.90 _PT/E
    assets:digital:Octopus cards:<uuid>            -5.90 HKD
    revenues:rewards                              -5.90_PT/E
```

Notes: add accrual posting between expense and payment posting; use `_PT/E` or appropriate point currency.

## 7. Octopus eDDA Top-Up (Specialized Import)

- Pass 1 (update existing): If an Octopus row matches date+amount within heuristics, update the existing transaction header (add `duration:` or missing tags), do not duplicate.
- Pass 2 (add new): If no match, insert new transaction at correct chronological position with full IDs in parentheses, tags (`activity`, `time`, `timezone`), and validate with `pnpm run format` and `pnpm run check`.

Example (conceptual):

```hledger
2026-01-25 12:38 (C1K62243986, FRN...) Octopus eDDA top-up  ; activity: transfer, time: 12:38:00, timezone: UTC+08:00
  assets:digital:Octopus cards:<uuid>     78.00 HKD
  assets:banks:<bank-uuid>               -78.00 HKD
```

Notes: See `payee_mappings.yml`, `id_mappings.yml`, and `private.yaml` for mapping and confidentiality rules.

---

For additional edge cases and tests, update `./examples.md` and notify maintainers; keep all examples non-confidential and use placeholder UUIDs and randomized IDs. If a new worked example is added, also add a short note to `./lessons.md` explaining why the example was introduced.
