# migrate — repairing a broken chain

The invariant in `./SKILL.md` is what a whole chain must satisfy; a repair is one step toward it, not a licence to edit boundaries by hand. `bun run verify:migration` prints one `journal:month: kind: detail` line per defect and exits 1 while any stands, so its output is the work list and the report.

## The ordering law

Repair the oldest defect first. Every later month's opening was derived from an earlier closing, so regenerating a month while an earlier one is still wrong writes the same error forward. Re-run `bun run verify:migration` over the whole chain after each month, and never batch two months into one change: the difference between two verifier runs is what proves the repair did what it claimed. A month that cannot be read breaks its chain in both directions, so its neighbours are never compared across it and their defects wait until it parses.

## One remedy per defect kind

| kind | what the verifier saw | remedy |
| --- | --- | --- |
| `missing_closing` | a past month has no `closing balances` transaction | `bun run clopen <month>`, then re-verify. Expect the months after it to report `opening_mismatch` until their openings are re-derived, one month at a time, in ascending order |
| `missing_opening` | a month has no `opening balances` transaction | the same command writes both sides of the pair. If the month's closing exists while its opening does not, the month was half-written: read the closing and the previous month's closing before running anything, and say in the report why they disagree |
| `opening_mismatch` | an opening does not negate the previous closing, per account and commodity | the later of the two transactions is the wrong one. Delete both boundary transactions of that pair — a hand edit, so report it and review the diff — and run `bun run clopen <month of the closing>` to derive them again from one set of balances; the side that was already right comes back unchanged, so the diff names the wrong one |
| `closing_not_zero` | a closing posting has no assertion, asserts something other than zero, or does not negate the month's balance | find the account with `node_modules/.bin/hledger register -I <account> -f ledger/<year>/<year>-<month>/self.journal` and compare it with the posting. Regenerate the pair rather than correcting the figure, and never weaken the assertion to match it |
| `closing_incomplete` | an account in scope carries a non-zero balance and the closing has no posting for it | regenerate the pair. A posting added by hand repairs the account and leaves the next opening short of it, which is the same defect a month later |
| `unexpected_boundary` | a month after the current month carries a boundary | delete that transaction, and stop: a boundary there means the tool ran for the month in progress. Never create a month to hold it |
| `unreadable` | hledger could not read the journal, or the month directory is not a calendar month | fix the parse error first (`../fix-journals/SKILL.md`), then re-verify; the directory name is not the diagnosis if the file also fails to parse |
| `boundary_unordered` | a boundary is not the month's first or last transaction, or its date, `time:` tag, or count is wrong | correct the date and the position only: opening on the month's first day and first in the file, closing on its last day and last in the file, `time:` `00:00:00` and `23:59:59` respectively. Two boundaries of one kind mean one is stale — compare both with the neighbouring month before deleting either |

Regenerating always means the same three moves: delete the affected boundary transactions, `bun run clopen <month of the closing>`, `bun run format:journal`. Deleting a transaction is a hand edit even when the tool then rewrites it, so name the deleted block in the report and let the diff carry the evidence.

## Escalation

Stop and report when a repair introduces a defect kind that was not there before, or when two runs disagree about the same pair. A second attempt at the same command is not a diagnosis, and a chain repaired into a new class of defect is a question for the owner, not another iteration.

## Hand-off

A journal that does not parse, or an assertion that fails inside a month, is `../fix-journals/SKILL.md`'s job; a chain that parses but does not close is this skill's. `bun run check` failing on an account, payee, tag, or commodity is never a boundary defect, and no repair here changes one.
