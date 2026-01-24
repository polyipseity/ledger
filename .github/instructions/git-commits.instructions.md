---
name: Git Commit Conventions
description: Conventional commit rules for repository contributions and explicit rules for ledger transaction commits made by agents.
---

# Git commit conventions

All commits MUST follow the Conventional Commits style for the repository. Commit bodies are optional unless stated below.

Allowed commit types include (but are not limited to): `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `ci`, `build`, and `ledger`.

## Ledger transaction commits (required format)

When commits add and/or edit hledger transactions, use this exact header format (verbatim):

ledger(<journal-list>): add N / edit M transaction(s)

- `<journal-list>`: one or more journal filenames (no year/month), comma-separated when multiple (example: `self.journal, investments.journal`).
- If only adding transactions, omit the `edit` part: `ledger(self.journal): add 3 transaction(s)`.
- If only editing transactions, omit the `add` part: `ledger(self.journal): edit 2 transaction(s)`.
- Use `transaction(s)` exactly (to handle singular/plural uniformly).

CRITICAL: For these ledger transaction commits, DO NOT include a rationale or body. The commit message must contain only the single-line header (no body, no additional lines). This is intentional to keep transaction commits concise and machine-parseable.

## General Conventional Commit rules

- Header must be: `<type>(<scope>): <short summary>` where `<scope>` is optional for non-ledger commits.
- Body is optional for normal commits; include when explanation, provenance, or references are needed.
- Footer may include references (tickets, co-authors) as needed.

## Enforcement guidance (recommended)

- Use `commitlint` + `husky` to enforce commit header patterns and to block ledger transaction commits from having bodies. This repo uses `pnpm` for JavaScript tooling; run `pnpm install` and `pnpm run prepare` to activate Husky hooks locally.
- Local pre-commit checks: Husky calls `lint-staged` which in this repo runs `pnpm run format:check` and `pnpm run check` on staged `*.journal` files. Agents should install deps and run the pnpm scripts before committing:

 - Use `commitlint` + `husky` to enforce commit header patterns and to block ledger transaction commits from having bodies. This repo uses `pnpm` for JavaScript tooling; run `pnpm install` and `pnpm run prepare` to activate Husky hooks locally.

 - Local pre-commit checks: Husky calls `lint-staged` which in this repo runs `pnpm run hledger:format:check` and `pnpm run hledger:check` on staged `*.journal` files. Agents should install deps and run the pnpm scripts before committing:

	- pnpm install
	- pnpm run markdownlint         # markdown linting
	- pnpm run markdownlint:fix     # optional: auto-fix markdown issues
	- pnpm run hledger:format:check # check formatting (no write)
	- pnpm run hledger:check        # run hledger checks

- CI enforcement: GitHub Actions runs `pnpm install` and then the `commitlint` workflow (commit message checks) and `check`/`format-check` workflows for journal validation.

Note for agents: when committing ledger transaction changes, follow the single-line `ledger(...)` header rule exactly and do NOT include a commit body — the commit must be parsable by automated tools.
