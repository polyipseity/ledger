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

## Troubleshooting

**`hledger` is missing.** `bun install` provisions it into `node_modules/.bin/hledger`, and every script prefers that file over anything on your `PATH`. When provisioning did not finish, `bun run hledger:install` writes the binary and `--force` replaces a partial or wrong-version download. To use a hand-installed hledger instead, install one from [hledger.org](https://hledger.org) or with `brew install hledger` on macOS and `apt install hledger` on Debian and Ubuntu.

**The Python interpreter is too old.** `pyproject.toml` requires 3.13 or newer, and `uv sync` downloads a matching interpreter when none is installed. If it refuses the one it finds, install a known-good version with `uv python install 3.13` and run `uv sync` again.

**`uv sync` did not finish.** It provisions the runtime dependencies and the dev group that `ruff`, `ty`, and `pytest` come from, so a partial sync fails the Python checks. Run `uv sync` by hand to see its error; `--locked` reproduces what CI installs from `uv.lock`.

**`gpg` is missing.** Install it with `brew install gnupg` on macOS, `apt install gnupg` on Debian and Ubuntu, or an installer from [gnupg.org](https://www.gnupg.org) on Windows.

**`gpg` has no key for the mappings.** `gpg --list-secret-keys` shows the keys this machine holds; `gpg --gen-key` creates one. `scripts/encrypt.sh` encrypts to the recipient its own line names, so a key that is not that recipient produces a mapping nothing here can open, and `scripts/decrypt.sh` prompts for the passphrase of a key that is.

**A task cannot find `bun`, `uv`, or `gpg`.** Every task reads `PATH`. `command -v bun uv gpg` names the ones your shell resolves.

**The shell scripts will not run on Windows.** Each module that ships a wrapper has a `.sh` and a `.bat` one side by side; both change to the repository root themselves, so either runs from any directory. There is no PowerShell script left to need an execution policy.
