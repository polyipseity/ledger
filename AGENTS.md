# Personal ledger — agent instructions

**Never write confidential data into this repository.** Journals and docs name payees and accounts by UUID placeholder, with generic names and example amounts; the real names, account numbers, and institutions live only in the encrypted `private.yaml.gpg`. Do not decrypt or print it unless the owner explicitly authorizes it.

**Ask when a value is ambiguous; never invent an amount, a date, a payee, an account, or a tag value.**

## Repository shape

- `ledger/` — hledger journals, all reachable from `ledger/index.journal`. Transactions go in the monthly file `ledger/<year>/<year>-<month>/<name>.journal`, whose month is the transaction date. `self.journal` tracks liquid assets, `self.alternatives.journal` illiquid ones, and each stream includes its own prelude.
- `preludes/` — the single source of account, commodity, payee, and tag definitions.
- `scripts/` — Python utilities and `scripts/utils/`. Relative imports mean a module runs only as `-m scripts.<mod>` from the repository root.
- `.agents/skills/` — task playbooks; read the matching `SKILL.md` in full before starting.
- `.agents/instructions/` — rule files, loaded by the paths each one targets; indexed below.
- `.github/workflows/`, `prek.toml` — CI and git hooks. `bun install` provisions Python dependencies, the managed hledger binary, and the hooks.

## Commands

These names are the whole agent-facing surface, and every one runs from the repository root.

| command                    | use when                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| `bun run check`            | before every commit; the full gate (`check:journal`, `check:md`, `check:prettier`, `check:py`) |
| `bun run format`           | after any edit, before `check` (`format:journal`, `format:md`, `format:prettier`, `format:py`) |
| `bun run check:journal`    | journal edits only: strict hledger check, then a formatting check                              |
| `bun run format:journal`   | journal edits only: strict check, then reflow                                                  |
| `bun run check:md`         | markdown docs only                                                                             |
| `bun run format:md`        | markdown docs only, with fixes                                                                 |
| `bun run check:py`         | Python only: ruff lint, ruff format check, ty                                                  |
| `bun run format:py`        | Python only: ruff fixes and format, then ty                                                    |
| `bun run test`             | before pushing: pytest                                                                         |

Two maintenance commands are the owner's to run, never an agent's: `uv run --locked -m scripts.clopen close <YYYY-MM>` writes a month boundary, and `uv run --locked -m scripts.clopen verify` reports boundary defects. `scripts/clopen.py` holds both.

### Invocation law

- `bun run <name>` from the repository root, always. It is the only invocation an agent uses, no other spelling of a command is a substitute, and a `bun run` name outside the table is not part of an agent workflow.
- Python runs only as `-m scripts.<mod>` from the repository root. A check narrowed to particular files names them there by repository-relative path, `uv run --locked -m scripts.check ledger/<year>/<year>-<month>/self.journal`, because the bun check composes the checker and the formatter, so a file argument reaches the formatter while the checker still covers the whole ledger. The modules are imported relatively, so a run from another working directory reports `No module named 'scripts'`, and running a file by path instead of as a module fails with `attempted relative import with no known parent package`.
- The shell and batch files beside each Python module are conveniences for humans without bun or uv. They change directory themselves, so agents never call them.
- Hooks come from `prek` (`prek.toml`): a commit-msg hook lints the message, pre-commit hooks format and type-check, and pre-push runs `bun run test`.

## Skills

Each row is a directory under `.agents/skills/`; read its `SKILL.md` in full, and treat its stop-and-ask list as binding rather than guessing. `ingest` routes to the twelve `ingest-*` aspects, one per class of transaction.

- `add-payee` — register a payee, or its confidential UUID, in the prelude in strict lexicographic order.
- `fix-journals` — turn one failing journal check into the smallest edit that makes it pass.
- `ingest` — settle what one piece of outside material becomes: the entries its claims match, the action each takes, and the run's report.
- `ingest-attachments` — what a scan, photo, or PDF may be transcribed into, and the printed text alone.
- `ingest-currency` — a conversion's equity pair, the printed rate, and the postings around them.
- `ingest-food` — a receipt's printed itemization, modifiers, fees, vouchers, and meal timing.
- `ingest-import` — locating an outside source, parsing it mechanically, and proving a second run adds nothing.
- `ingest-lending` — loans, repayments, and shared bills, including the three friend-sharing shapes.
- `ingest-octopus` — card rows: the mandatory payee mapping, the reload pair, and updating an entry without rewriting it.
- `ingest-payee` — resolving a printed name to a declared payee, its UUID mask, and the identifiers ahead of it.
- `ingest-platform` — a platform sale's gross, fee, and net, and the payout that empties the balance.
- `ingest-remove` — removing a wrong entry: its evidence, the balances that depend on it, and the report that restores it.
- `ingest-statement` — matching a statement row to an entry that exists: the match order and the rows that stop the batch.
- `ingest-tags` — the comment keys an entry requires, the order they keep, and the prelude line that makes one legal.
- `ingest-transport` — fares, tolls, and transit reward accruals: the mode account and the cases that carry no duration.
- `migrate` — close a month and open the next, and repair a boundary chain that is already broken.

## Instructions

Each row is `.agents/instructions/<name>.instructions.md`. `.agents/reference/` holds the account taxonomy as reference material rather than rules.

- `alternatives-journal` — when a holding belongs in the illiquid stream instead of the main one.
- `architecture` — journal hierarchy, includes, and file organization.
- `dependencies` — the four tools an agent needs, and what to do when one is missing.
- `developer-workflows` — script internals, tests, and hook invocation shapes.
- `editing-guidelines` — ordering, the smallest safe edit, assertions, and the journal anti-patterns.
- `git-commits` — commit types, message format, and the ledger transaction header.
- `security` — confidential data, encryption, and UUID privacy.
- `skill-authoring` — the budgets, the section skeleton, and the one-rule-one-file boundary every skill obeys.
- `transaction-format` — hledger syntax, status markers, alignment, assertions, and posting order.

## Code conventions

- Path parameters take `os.PathLike` and are annotated `PathLike[str]`; tests annotate `tmp_path` the same way. Convert a path to a string with `os.fspath`, never `str`.
- Datetimes are timezone-aware: `datetime.now(timezone.utc)`, never `utcnow()`.
- Imports stay at module top level; Ruff's `import-outside-top-level` rule rejects inline ones.
- Every module under `scripts/` and every test module declares `__all__`; tests use `()`.
- Generic types are built in (`dict`, `list`, `tuple`) with ABCs from `collections.abc`, unions as `X | Y`, and `Self` for instance-returning methods.
- Modules, classes, functions, and tests carry docstrings and complete annotations. `ty` runs with every rule as an error, so `Any` and `Unknown` need an inline justification.
- Ruff is the only Python formatter and import sorter; `black` and `isort` stay out of the toolchain.
- No legacy cache compatibility branches; a format upgrade replaces the old one.
- Async tests are `async def` with `@pytest.mark.anyio`; no event-loop runner such as `asyncio.run`.
- A script exposes `main(argv)`, a `__main__()` wrapper, and the `if __name__ == "__main__"` guard, with `runnify` for async entry points.
- Exit codes: `0` success, `1` error, `2` usage, `3` file or IO failure.
- Tests mirror the source tree, one file per source file, under `tests/`; new behaviour gets a test in the same change.

## Journal invariants

- Syntax, status markers (`!` pending, `*` cleared), and posting order live in `transaction-format`, the comment keys in `ingest-tags`, and the editing rules in `editing-guidelines`.
- Every month opens with an `opening balances` transaction and closes with a `closing balances` one. The closing zeroes and asserts every account whose hledger type is Asset, Liability, or Cash — expenses and revenues never take a posting in it — and it never requires an `equity:opening/closing balances` line; the next month's opening restores exactly those balances, so the two months must agree. The `migrate` skill holds the invariant and its repair.
- Closing and opening balances are generated by the boundary tool (`scripts/clopen.py`), never hand-written or copied from another tool's output. The `migrate` skill holds the procedure.

## Commit policy

- Conventional Commits; `.agents/instructions/git-commits.instructions.md` is the rule file, and the commit-msg hook enforces it.
- A commit that changes transactions is a single line, `ledger(<journals>): add N / edit M transaction(s)`, with no body.
- Run `bun run format`, then `bun run check` before committing; run `bun run test` before pushing, and the pre-push hook runs it too.
- Commit only when the owner asks; otherwise stop after validating.
