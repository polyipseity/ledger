# ingest — owner notes

Two things a run owes the owner: the report that closes it, and the list of cases that stop it. Both live here so `SKILL.md` stays a procedure.

## The report

One table per run, in source order, one row per source row, and a row that stopped gets one too:

| column | holds |
| --- | --- |
| source | the file, message, or screen, with the row's number or printed sequence in it |
| action | `add`, `update`, `no action`, `remove`, or `stopped` |
| date | the date the entry takes, `YYYY-MM-DD` |
| payee | the payee line as written: printed identifiers first, the declared payee after |
| amount | the signed amount and commodity, as the journal writes it |
| file | `ledger/<year>/<year>-<month>/<name>.journal` |
| note | one clause: what an update changed, or why a row stopped |

Below the table:

- **A seconds-only update is not listed.** A row that adds seconds to a `time:` holding none changes nothing else, so it is applied quietly and the run reports the count. A change that moves a minute, an hour, or a date shows both datetimes, before and after.
- **An unmatched row stays in the table** with its reason: no candidate at all, several candidates that the amount and the payee do not separate, or a row held for a question below. It is never dropped to make the table look finished.
- **A removal is quoted verbatim** — the entry's own lines, its file, and the balances that depended on it — because the report is what lets the owner put it back.
- **Every question is a bullet under the table**, naming the source row it holds; nothing is deferred without one.

## Confidentiality

The table carries UUIDs, the aspects' generic payees, and its own amounts. It never carries a confidential merchant's name, a wallet, card, or bank account number, a statement's account summary, or a scan name that holds one; a row whose identity would need one is reported by its date, amount, and time instead.

## Stop and ask

- A printed name that no `./payee_mappings.yml` alias, `private.yaml` pair, or prelude declaration covers.
- An alias with several targets that the row's amount, items, and venue do not separate.
- Several candidate entries that the amount and the time do not reduce to one.
- An aggregate total that matches no single posting, or matches several payers' shares.
- An item the source prints in a form no approved translation covers.
- A reload with no credit behind it, or a credit with no reload.
- Any other ambiguity in the date, the amount, the payee, or the posting.
