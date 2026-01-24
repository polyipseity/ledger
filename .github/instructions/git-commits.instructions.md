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

- Use `commitlint` + `husky` to enforce commit header patterns and to block ledger transaction commits from having bodies.
- Run `python -m check` in a pre-commit hook for any changes touching `*.journal` files.
