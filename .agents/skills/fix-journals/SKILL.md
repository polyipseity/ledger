---
name: fix-journals
description: Fix hledger journal errors reported by the check suite — undeclared accounts, payees, tags or commodities, parse errors, ordering, failing balance assertions, unbalanced transactions, and broken month boundary balances. Use when `bun run check:journal` fails or a validation error must be repaired.
---

# fix-journals

This skill turns one failing check into the smallest edit that makes it pass. It owns diagnosis and repair; what a correct entry looks like is `../../instructions/transaction-format.instructions.md`'s, where it belongs is `../../instructions/editing-guidelines.instructions.md`'s, and the command surface is `../../../AGENTS.md`'s. No other step of a run proceeds while a check is failing.

## The loop

1. Run `bun run check:journal`: the checker first, then a formatting check over the same journals.
2. Read the first failure only. The hledger message arrives inside the `stderr:` of the `- Command (...)` entry and names the file, the line numbers, the offending line, and the check that rejected it.
3. Classify it with the table below, then make the smallest edit that answers it, touching no other line.
4. Re-run `bun run check:journal`. A second failure is the next defect, not the same one twice.
5. When the check is clean, run `bun run format:journal` once. It repeats the check and then rewrites the journals into canonical form, so it runs after the last fix; it can never repair a parse error.

A formatting diff is not a check failure and never reaches the table: `bun run check:journal` ends with a check-only pass of the formatter, so a diff it reports has no check name, no cause to classify, and one fix — `bun run format:journal`.

Both bun forms take no file argument and always cover the whole journal set. Scope a check to one file with the module form and a repository-relative path: `uv run --locked -m scripts.check ledger/<year>/<year>-<month>/self.journal`.

**Diagnosis journals.** To see what a check prints, write a self-contained scratch journal under `/tmp` with its own `account`, `payee`, `tag`, and `commodity` declarations and no `include`, and run `node_modules/.bin/hledger --strict --file <scratch> check <check>` against it; nothing is created inside the repository for this. To reproduce a real journal's failure, copy that journal beside itself in `ledger/<year>/<year>-<month>/`, because its `include ../../../preludes/self.journal` is relative: a copy in `/tmp` resolves against the wrong directory and fails with a missing-include error that has nothing to do with the defect. Delete the copy before committing.

## The error → fix table

| check | what hledger prints | usual cause here | minimal fix |
| --- | --- | --- | --- |
| `parseable` | `This is not a valid date, please fix it.`, or `unexpected newline` / `expecting '*', '=', or amount (for a balance assertion or assignment)` | a header the parser cannot read, or a posting or tag cut off mid-token | restore the syntax; the formatter cannot help, so it is not run to "see what happens" |
| `accounts` | `account "expenses:food and drinks:dining" has not been declared.` | a new account used before it is declared, or a typo in a deep account name | search the declared names with `node_modules/.bin/hledger accounts --declared -f ledger/index.journal \| rg '<search>'`, then declare the account in `preludes/self.journal` in the existing style or correct the name to a declared one; never invent a parallel account |
| `payees` | `payee "Another Merchant" has not been declared.` | a merchant spelled differently from its declared `payee` line | register it (`../add-payee/SKILL.md`) or correct the spelling |
| `tags` | `tag "eatingtype" has not been declared.` | a tag name, or an enumerated value, that the preludes do not declare | declare it, or correct it to a declared one |
| `commodities` | `commodity "USD" has not been declared.` | a commodity with no `commodity` directive, or a wrong symbol | declare it in the preludes, or fix the symbol |
| `ordereddates` | `date (2025-01-02) is out of order with the previous transaction.` | a transaction inserted above one with an earlier date | move the whole block to its chronological place by date and time; never change the date to satisfy the order |
| `balanced` | `This transaction is unbalanced.` and `The real postings' sum should be 0 but is: 10.00 HKD` | a missing or doubled posting, or two commodities that do not convert | find the posting that should not be there or should; a real difference in the source is a question for the owner, not a plug |
| `autobalanced` | `There can't be more than one real posting with no amount.` | two postings left implicit, or an implicit amount the transaction cannot infer | write the amounts explicitly |
| `assertions` | `Balance assertion failed in assets:cash`, `the asserted balance is: 100.00 HKD` / `but the calculated balance is: -50.00 HKD` | an assertion that no longer matches the running balance | recompute it with `node_modules/.bin/hledger register -I <account> -f <journal>`, then decide which side is wrong — the assertion or the transactions above it; never weaken the assertion |

Two repairs are another skill's decision, not this one's. An amount the source contradicts corrects the entry in place, and removal is `../ingest-remove/SKILL.md`'s. A boundary block is generated rather than edited, so a missing or mismatched one is `../migrate/SKILL.md`'s.

## Boundary balances

The check suite says nothing about the chain between months. `uv run --locked -m scripts.clopen verify` does: one line per defect in the form `journal:month: kind: detail`, and exit 1 while any defect stands.

- **The kinds**: `missing_opening`, `missing_closing`, `unexpected_boundary`, `closing_not_zero`, `closing_incomplete`, `opening_mismatch`, `boundary_unordered`, `unreadable`.
- **A wrong closing invalidates the next month's opening.** Repair both sides in one change, then re-run `uv run --locked -m scripts.clopen verify` over the whole chain.
- **The scope of a closing** is every account whose hledger type is Asset, Liability, or Cash, which is what `hledger accounts --types` reports. Expenses and revenues are never unclosed, and `equity:opening/closing balances` is never required in a closing; a `closing_incomplete` line naming an expense or revenue account is not a defect, and a repair must not invent one.
- **Diagnose with the same register call**, `-I` on the account the defect names, and compare the two months' figures.
- **A boundary defect goes to `../migrate/SKILL.md`** once it is diagnosed. This skill reports it and hands off; it never hand-writes an opening or a closing.

## Never

- Delete a posting to restore balance without naming why it was unbalanced.
- Comment out a failing assertion, or weaken one to match a wrong balance.
- Edit a prelude to silence a typo you introduced; fix the typo.
- Reformat a whole file to make one small edit.
- Run `bun run format` to fix a parse error, or run any formatter on a journal that does not parse.

## Evidence to report

- The file, repository-relative, and the transaction header exactly as written.
- The check name and the failing output line, copied from the run.
- The before and after of every amount, account, payee, or tag you changed.
- Any defect left standing and the skill it was handed to.
