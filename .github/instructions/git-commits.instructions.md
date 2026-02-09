---
name: Git Commit Conventions
description: Conventional commit rules for repository contributions and explicit rules for ledger transaction commits made by agents.
---

# Git commit conventions

**Note:** See `AGENTS.md` and `.github/instructions/agent-quickstart.instructions.md` for agent workflow rules and use the Todo List Tool for multi-step tasks.

All commits MUST follow the Conventional Commits style for the repository. Commit bodies are optional unless stated below.

**Commit body lines MUST be ≤100 characters to pass commitlint (this is a hard limit and commits exceeding it will be blocked). Agents SHOULD prefer wrapping commit body lines to **72 characters** or fewer for readability and as a buffer when quoting in other tools.**

Allowed commit types include (but are not limited to): `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `ci`, `build`, and `ledger`.

## Ledger transaction commits (required format)

When commits add and/or edit hledger transactions, use this exact header format (verbatim):

```text
ledger(<journal-list>): add N / edit M transaction(s)
```

- `<journal-list>`: one or more journal filenames (no year/month), comma-separated when multiple (example: `self.journal, investments.journal`).
- If only adding transactions, omit the `edit` part: `ledger(self.journal): add 3 transaction(s)`.
- If only editing transactions, omit the `add` part: `ledger(self.journal): edit 2 transaction(s)`.
- Use `transaction(s)` exactly (to handle singular/plural uniformly).

CRITICAL: For these ledger transaction commits, DO NOT include a rationale or body. The commit message must contain only the single-line header (no body, no additional lines). This is intentional to keep transaction commits concise and machine-parseable.

## General Conventional Commit rules

- Header must be: `<type>(<scope>): <short summary>` where `<scope>` is optional for non-ledger commits.
- Body is optional for normal commits; include when explanation, provenance, or references are needed.
- **Each line in the commit body must not exceed 100 characters (commitlint will block non-conforming commits). Prefer wrapping to **72 characters** or fewer for readability and to provide a buffer when lines are wrapped or quoted in other tools.**
- Footer may include references (tickets, co-authors) as needed.

## Enforcement guidance (required)

- This repository uses `commitlint` + `husky` to enforce commit header patterns and body line length (100 chars max), and to block ledger transaction commits from having bodies. This is a hard requirement: commits that do not comply will be rejected.

- Local pre-commit checks: Husky calls `lint-staged` which in this repo runs `pnpm run hledger:format:check` and `pnpm run hledger:check` on staged `*.journal` files. Agents should install deps and run the pnpm scripts before committing:
  - pnpm install
  - pnpm run markdownlint         # markdown linting
  - pnpm run markdownlint:fix     # optional: auto-fix markdown issues
  - pnpm run hledger:format       # format journals (may modify files)
  - pnpm run hledger:check        # run hledger checks
  - pnpm run test                 # run unit tests (Husky also registers a `pre-push` that will run this)

- CI enforcement: GitHub Actions runs `pnpm install` and then the `commitlint` workflow (commit message checks) and `check`/`format-check` workflows for journal validation.

Note for agents: when committing ledger transaction changes, follow the single-line `ledger(...)` header rule exactly and do NOT include a commit body — the commit must be parsable by automated tools.

## Agent / automated commits

Agents and automation (bots, assistants) MUST follow the same Conventional Commits rules as humans. In addition, before committing, agents MUST run the repository's formatting and validation steps using the pnpm script wrappers (e.g., `pnpm run format`, `pnpm run check`). Only use direct Python invocations or script wrappers in `scripts/` if no pnpm script is available, and set cwd to `scripts/`.

When an agent makes a normal (non-ledger) commit and a motivation or rationale is available, the agent SHOULD include that rationale in the commit body. Keep commit bodies concise and wrapped to a reasonable line length. For ledger transaction commits, the existing rule still applies: use the exact single-line `ledger(...)` header and do NOT include a commit body.
