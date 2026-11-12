---
name: ingest-transport
description: Rules for transcribing fares, tolls, and transit reward accruals into hledger — mode accounts, the accrual pair, and the cases that carry no duration.
---

# ingest-transport

This aspect decides how one fare-shaped charge becomes postings: which transport subaccount the mode selects, whether the operator's reward program adds an accrual pair, and which metadata a fare carries. `ingest` owns intake, matching, the add/update/no-op decision, and the validation gate; journal syntax and posting shape are `../../instructions/transaction-format.instructions.md`'s, and placement is `../../instructions/editing-guidelines.instructions.md`'s.

## When to use

A deduction for a bus, rail, ferry, tram, light-rail, minibus, taxi, or airplane fare, a toll, or a transit payment that prints a reward or points accrual, sourced from card history, bank alerts, operator receipts, or a booking confirmation. A card reload is a transfer between your own accounts rather than a fare, and `../ingest-octopus/SKILL.md` owns its shape.

## Rules

1. **The operator is mapped before the entry exists.** Resolve it through `../ingest/payee_mappings.yml`; an operator with no mapping, or with several candidates and nothing in the row to separate them, goes to `../ingest-payee/SKILL.md`.
2. **The mode picks the account.** `expenses:transport:buses`, `:trains` with `:high-speed` for a long-haul ticket, `:ferries`, `:light rail`, `:minibuses`, `:taxis`, `:trams`, or `:airplanes`, chosen from `../../instructions/account-hierarchy.instructions.md`. The amount never picks the mode.
3. **A fare carries `activity: transport`.** A points redemption from the same program is a reward transaction rather than a fare.
4. **A fare has no duration.** No `duration:` goes on a fare, and a later statement row that pairs with an existing fare entry never adds one: the fare has a start and no end.
5. **The accrual rides in the same transaction.** An operator that credits points with the fare gets two extra postings on the same date, in the order expense, accrual, payment, revenue: `assets:accrued revenues:rewards` positive and `revenues:rewards` negative, both in the program's point commodity.
6. **Confirm the point commodity.** `_PT/E` is the common transit currency; any other program's commodity is checked in the prelude before use, and a program whose commodity is undeclared stops the entry.
7. **Not every transit purchase accrues.** A public light bus fare and a vending-machine purchase accrue nothing; a vending drink is a food entry (`../ingest-food/SKILL.md`), so only a payee whose program is known gets an accrual pair.
8. **A reload is a transfer.** It moves money between your own accounts and is never a transport expense.
9. **A charge with no transport subaccount is not a fare.** A toll or a parking fee whose account no listed mode covers goes back through `../ingest/SKILL.md` rather than into an invented account.

## Procedure

1. Read the source and take the operator, the signed amount, the timestamp, and the tender that paid.
2. Resolve the operator's payee, and hand an unmapped one to `../ingest-payee/SKILL.md`.
3. Select the transport subaccount for the mode.
4. Answer the reward question for this operator and this fare.
5. Write the block with the expense, then the accrual pair when rule 5 applies, then the payment.
6. Hand the block to `../ingest/SKILL.md` for the action decision; the check loop is `../fix-journals/SKILL.md`.

## Worked example

```hledger
2025-03-04 Example Bus Operator  ; activity: transport, time: 08:15, timezone: UTC+08:00
    expenses:transport:buses                                  6.00 HKD
    assets:accrued revenues:rewards                           6.00 _PT/E
    assets:digital:Octopus cards:<uuid>                      -6.00 HKD
    revenues:rewards                                         -6.00 _PT/E
```

## Stop and ask

- The operator is unmapped, or maps to several payees with nothing in the row to choose between them.
- The row does not say which card, wallet, or account paid, or it could be a reload rather than a fare.
- The operator prints a reward but its program or point commodity is unknown.
- The amount and the printed mode disagree, as when a tram charge lands at a bus fare.
