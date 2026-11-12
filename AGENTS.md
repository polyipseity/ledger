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
| `bun run clopen <YYYY-MM>` | close one month and open the next (added in a later task of this restructure)                  |
| `bun run verify:migration` | monthly boundary invariants across the chain (added in a later task of this restructure)       |

### Invocation law

- `bun run <name>` from the repository root, always. It is the only invocation an agent uses; no other spelling of a command is a substitute, and any `bun run` name outside the table does not exist.
- Python runs only as `-m scripts.<mod>` from the repository root. The modules are imported relatively, so any other working directory fails with `attempted relative import with no known parent package`.
- The shell and batch files beside each Python module are conveniences for humans without bun or uv. They change directory themselves, so agents never call them.
- Hooks come from `prek` (`prek.toml`): a commit-msg hook lints the message, pre-commit hooks format and type-check, and pre-push runs `bun run test`.

## Skills

Each row is a directory under `.agents/skills/`; read its `SKILL.md` in full, and treat its stop-and-ask list as binding rather than guessing.

- `add-payee` — register a payee, or its confidential UUID, in the prelude in strict lexicographic order.
- `add-transactions` — transcribe receipts, statements, emails, and app history into entries with the right status, tags, accounts, and dedupe.
- `edit-journals` — change an existing journal's structure, includes, assertions, and formatting.
- `match-octopus-statement-transactions` — reconcile Octopus Wallet statement rows to journal entries and correct their datetimes.
- `monthly-migration` — close a month and open the next with opening balances and assertions intact.
- `upsert-octopus-transactions` — add or update Octopus card transactions from app history, including transports and reloads.
- `validate-journals` — drive the journal check and format loop and fix what it reports.

## Instructions

Each row is `.agents/instructions/<name>.instructions.md`.

- `account-hierarchy` — every account, what it means, and where a new one belongs.
- `agent-glossary` — short definitions of the terms the skills use.
- `agent-quickstart` — one-page command checklist, gotchas, and first workflows.
- `alternatives-journal` — when a holding belongs in the illiquid stream instead of the main one.
- `architecture` — journal hierarchy, includes, and file organization.
- `common-workflows` — pre-commit checklist and routine ledger operations, step by step.
- `continuous-learning` — recurring mistakes, anti-patterns, and proven fixes; start here when unsure.
- `dependencies` — required tools, versions, and troubleshooting.
- `developer-workflows` — script internals, tests, and hook invocation shapes.
- `editing-guidelines` — editing rules: ordering, payee registration, structure, anti-patterns.
- `git-commits` — commit types, message format, and the ledger transaction header.
- `python-entry-points` — the `main()`/`__main__()` shape and exit codes for scripts.
- `security` — confidential data, encryption, and UUID privacy.
- `transaction-format` — hledger syntax, required tags, status markers, and posting order.

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

- Syntax, required tags, status markers (`!` pending, `*` cleared), and posting order live in `transaction-format`; editing rules live in `editing-guidelines`.
- Every month opens with an `opening balances` transaction and closes with a `closing balances` one. Closing zeroes and asserts every account; the next month's opening restores exactly those balances, so the two months must agree.
- Closing and opening balances are generated by the boundary tool (`scripts/clopen.py`), never hand-written or hand-copied from `hledger close --migrate` output. The `monthly-migration` skill holds the procedure.

## Commit policy

- Conventional Commits; `.agents/instructions/git-commits.instructions.md` is the rule file, and the commit-msg hook enforces it.
- A commit that changes transactions is a single line, `ledger(<journals>): add N / edit M transaction(s)`, with no body.
- Run `bun run format`, then `bun run check` before committing; run `bun run test` before pushing, and the pre-push hook runs it too.
- Commit only when the owner asks; otherwise stop after validating.
