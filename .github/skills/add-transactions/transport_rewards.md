# Transport Reward Transactions

This theme documents reward accrual patterns for transport transactions (for example Kowloon Motor Bus / Long Win Bus) and the posting pattern to use when the transport provider issues reward points on payment.

When to use

- Use this pattern for transport transactions where a reward or points program is earned concurrently with payment (for example, Octopus or operator schemes that credit reward points).
- Use the pattern even when the exact point currency is not labeled, using `_PT/E` or the appropriate point currency declared in the prelude.

Posting pattern

- Add an accrual posting to `assets:accrued revenues:rewards` with the point amount (use the same numeric value when parity applies or as specified by the reward program).
- Add the usual payment (negative asset) posting (e.g., `assets:digital:Octopus cards:<uuid>`).
- Add a balancing posting to `revenues:rewards` as a negative value in the point currency (e.g., `-5.90 _PT/E`).
- Place the accrual posting between the expense posting and the payment posting to make the pattern clear and consistent.

Example

2026-01-01 Kowloon Motor Bus/Long Win Bus  ; activity: transport, time: 23:59, timezone: UTC+08:00
    expenses:transport:buses                                                 5.90 HKD
    assets:accrued revenues:rewards                                        5.90 _PT/E
    assets:digital:Octopus cards:1608ef20-afcd-4cd0-9631-2c7b15437521       -5.90 HKD
    revenues:rewards                                                      -5.90_PT/E

Notes and validation

- Confirm the correct point currency and account when the reward program differs from `_PT/E` and update the posting accordingly.
- When automating imports, prefer to detect this pattern by payee name (`Kowloon Motor Bus`, `Long Win Bus`) or by explicit program metadata in the source data. If uncertain, prompt the user before adding accrual lines.
- Remember to include `timezone:` on transport transactions that include a time and to follow the standard chronological ordering rules when inserting these transactions.
