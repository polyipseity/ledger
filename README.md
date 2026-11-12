# ledger

A personal double-entry ledger in [hledger](https://hledger.org) plain text: journals under `ledger/`, shared account and payee definitions under `preludes/`, and Python tooling under `scripts/` driven by a small Bun task surface.

## Prerequisites

- **git**
- **bun** — runs every task here; `package.json` pins the version in its `packageManager` field.
- **uv** with **Python 3.13 or newer** — runs the scripts and the test suite. `pyproject.toml` requires 3.13, and `uv sync` downloads a matching interpreter when none is installed.
- **gpg** — needed only to open or update the confidential mappings.
- **hledger** — nothing separate to install: `bun install` fetches the managed binary, and the scripts prefer it to any `hledger` on your `PATH`.

## Setup

Run `bun install` once from the repository root. Its `prepare` script provisions the Python dependencies with `uv sync`, installs the managed hledger binary into `node_modules/.bin/hledger`, and registers the git hooks with `prek`.

The shell and batch files beside each Python module (`scripts/check.sh`, `scripts/check.bat`, and their siblings) invoke the module directly and change to the repository root themselves, as a convenience for a human without bun or uv.

## Validate and format by hand

- `bun run format` rewrites what it can: journals, Markdown, Prettier-handled files, and Python.
- `bun run check` is the gate that has to pass: the journal check, Markdown lint, the Prettier check, and the Ruff and `ty` passes over Python.
- For one concern at a time, use its pair: `bun run check:journal` and `bun run format:journal` for journals, `bun run check:md` and `bun run format:md` for Markdown, `bun run check:py` and `bun run format:py` for Python.
- `bun run test` runs the pytest suite.

Run `format` before `check`, since the second only reports what the first has already fixed. The hooks do overlapping work — a pre-commit pass formats and type-checks, a pre-push pass runs the suite — so a clean `bun run format` and `bun run check` keep a commit quiet, and `bun run test` keeps a push quiet.

CI (`.github/workflows/ci.yml`) installs the same way, then runs `bun run test` and a build step that chains the full check, since there is nothing to compile.

[`AGENTS.md`](AGENTS.md) holds the full command table, one row per task, with guidance on when to reach for each.

## Where a transaction goes

`ledger/index.journal` includes the two streams: `self.journal` for liquid assets and `self.alternatives.journal` for illiquid ones. A transaction belongs in `ledger/<year>/<year>-<month>/<name>.journal`, and the month in that path is the month of the transaction date. `preludes/` is the single source of account, commodity, payee, and tag definitions; [`AGENTS.md`](AGENTS.md) describes the rest of the layout and the rules each journal file follows.

## Confidential data

Journals name payees and accounts by UUID placeholder. Each placeholder resolves through `private.yaml`, which holds the real names, account numbers, and institutions. Only the gpg-encrypted `private.yaml.gpg` is committed; `.gitignore` excludes the plaintext file.

Touch the mappings only when you are adding or changing one: decrypt with the `scripts/decrypt.*` wrapper, make the edit, then encrypt with `scripts/encrypt.*` before committing. A confidential value never belongs in a journal, a document, or a commit.

## Editor setup

In VS Code with Copilot Chat, enable `chat.useAgentsMdFile` and leave `chat.useNestedAgentsMdFiles` disabled, so the single root `AGENTS.md` is the file that loads as context.

Markdown is linted by `markdownlint-cli2` and formatted by Prettier, configured by `.markdownlint-cli2.mjs`, `.markdownlint.jsonc`, `.prettierrc.mjs`, and `.editorconfig`. `bun run check:md` lints them, and `bun run format:md` applies the linter's fixes.
