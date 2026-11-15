---
name: migrate
description: Close a month and open the next in the hledger ledger — run the boundary tool, verify the closing zeroes every balance while the opening restores it, and repair broken month boundaries in ascending order. Use for monthly migration, month-end closing, opening-balance repair, or a boundary that the verifier reports as missing or mismatched.
---

# migrate

A month boundary is two generated transactions: a `closing balances` at the end of one month and an `opening balances` at the start of the next. `scripts/clopen.py` derives both from the month's own balances, and this skill runs it, verifies the result, and repairs a chain that is already broken. The syntax of a boundary transaction is `../../instructions/transaction-format.instructions.md`'s, the command surface is `../../../AGENTS.md`'s, and a journal that does not parse is `../fix-journals/SKILL.md`'s.

## Prerequisites

- The month that ended is final: every transaction of it is entered and `bun run check:journal` is clean, because a closing is only as correct as the entries it sums.
- The working tree is clean, so the diff the tool writes is the only change in it and can be read as one.
- A boundary is written once. A second run refuses a month that already carries one, so a second run never means "try again": it means the first one is wrong, and that is a repair, not a retry.

## The invariant

The closing transaction zeroes every account whose hledger type is Asset, Liability, or Cash (never expenses or revenues, which hledger's own `close` does not touch, and never `equity:opening/closing balances` as a required line) and asserts each posting to zero, keeping the net on `equity:opening/closing balances`; the next month's opening transaction restores exactly those balances and asserts each one; therefore `opening(M+1)` equals `−closing(M)` for every account and commodity.

A wrong closing invalidates the next opening, so the two are repaired together and no edit touches one side alone. `uv run --locked -m scripts.clopen verify` reports every disagreement with that invariant as one defect line, and `./migrate-repair.md` turns one defect into one repair.

## Procedure

1. `uv run --locked -m scripts.clopen close <YYYY-MM>`, naming the month that ended.
2. `uv run --locked -m scripts.clopen verify`, which prints one `journal:month: kind: detail` line per defect and exits 1 while any stands.
3. `bun run format:journal`, because the written block joins the journal's own text and the formatter sorts and reflows it.
4. `bun run check`, the full gate, before reporting anything.

The tool computes the boundary with hledger's own `close` and writes the result back rather than printing it to the terminal, so no figure passes through a copy step.

| where | header | postings |
| --- | --- | --- |
| appended to the month that ended | its last date, `closing balances` | every account in scope, amount negated, `= 0.00 <CUR>`, then the net on `equity:opening/closing balances` |
| inserted into the month after it | its first date, `opening balances` | the same accounts with the same figures, `= <amount> <CUR>`, then the net on `equity:opening/closing balances` |

Both headers carry `clopen:`, `time:` (`23:59:59` closing, `00:00:00` opening), and `timezone: UTC+08:00`, and the formatter sorts those tags. The net lands on `equity:opening/closing balances` in one of two forms, both of them normal output: a single line with no amount, which hledger infers, or one line per commodity with the amount written out. A block showing either form is never rewritten to match the other. The closing is appended to the end of its journal; the opening is inserted after the last `include` line, so the prelude still loads first. When the next month's journal does not exist, it is created with the current one's `include` lines and the opening.

## What clopen refuses

It processes each journal on its own, so a refusal in one journal family does not stop the other, and every refusal is information rather than a failure: the message names the file and the reason.

- **An existing closing** — the computed closing header is already in the month's journal, so the month was closed before. Nothing is written for that journal and the run exits 1; compare the existing boundary with the month's balances in `./migrate-repair.md` instead of adding a second one.
- **An existing opening** — the next month already carries the opening this run would write, so the pair exists. Both refusals happen before either file is touched, so the month is left whole.
- **A journal hledger cannot parse** — the run fails for that file with hledger's message and writes nothing. Fix the journal first (`../fix-journals/SKILL.md`); no tool repairs a parse error by writing a boundary over it.
- **A period with no journal** — nothing is found, nothing is written, and the exit code is 0. That is not a migrated month: only `uv run --locked -m scripts.clopen verify` says whether a month has its boundaries.

## Journal families

`self.journal` and `self.alternatives.journal` are separate families with separate chains, and a boundary is only ever compared with the boundary in the previous journal of the same family — the previous one that exists, since a month the family skips keeps the link across the gap, and only an unreadable journal breaks it. `uv run --locked -m scripts.clopen close <YYYY-MM> <filename>` keeps the run to the family that filename names, and each further filename adds a family; a bare run covers every family the month has. One month can therefore be migrated in one family and not the other, and a family that was dormant for a month must not be resurrected silently: when the month's journal exists but the family was never used in it, name the other family as the only filename rather than letting a bare run create a boundary for a journal nobody is keeping. The verifier reports each family independently.

A family whose last journal carries an opening and no closing is the case this skill cannot settle: closing that month revives the family with a new journal, and excluding it leaves a `missing_closing` the verifier never stops reporting, so the chain can never reach zero. Ask the owner whether the family continues or its trailing boundary month is dropped, and report the question instead of choosing.

## Future months

A month after the current month may exist as a scaffold — the `include` lines and nothing else — and must carry no boundary transaction: a closing there would assert balances that month cannot know, and an opening there would restore a closing that does not exist. `uv run --locked -m scripts.clopen verify` reports either as `unexpected_boundary`. The `close` subcommand is run for the month that ended and never for the month in progress, which would leave an opening in the month after it. The current month is the month of the last commit's committer date; `--now <YYYY-MM>` overrides it when that date names the wrong one: pass it the month in progress, never the month just closed, which would turn the opening just written into a future month's boundary.

## Never hand-copy output

Never transcribe another tool's boundary output into a journal, never type a boundary transaction in an editor, and never migrate two months in one step: each opening is the previous closing negated, so a batch hides which of the two a wrong figure came from. The tool exists because hand-copying lost postings, and the months it left unclosed in this repository still have to be repaired one pair at a time.

## Verification and report

Run, in order:

```sh
uv run --locked -m scripts.clopen verify
bun run format:journal
bun run check
```

A clean chain prints no `journal:month:` line and logs `0 boundary defect(s) for <YYYY-MM>`; any defect line is one repair and belongs in `./migrate-repair.md`. Report the months migrated and the journal families they were migrated in, the verifier's output verbatim (its defect lines, or the zero count), and the result of `bun run check`. `./migrate-examples.md` shows the pair as the tool writes it, and a month whose closing was missing.

## A chain that is already broken

Read `./migrate-repair.md` before the first repair. It holds the ordering law, one remedy per defect kind, the escalation rule, and the boundary between a broken journal, which is `../fix-journals/SKILL.md`'s, and a broken chain, which is this skill's.
