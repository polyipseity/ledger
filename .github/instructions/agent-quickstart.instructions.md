---
name: Agent Quick Start
description: Short, actionable checklist and examples to help AI coding agents start contributing safely and productively.
---

# Agent Quick Start (one page) ✅

This file is a concise checklist for AI agents working in this repository. Read the full `SKILL.md` for task-specific rules before acting.

## Core checklist (do this every time)

- Read the relevant `.github/skills/<task>/SKILL.md` and any `examples.md` or `lessons.md` included for that skill.
- Run `pnpm install` once to get Node + Python tooling; `prepare` runs `uv sync` to provision Python dev extras.
- Format & validate: `pnpm run format && pnpm run check` (alternatively, `pnpm run format:py`, `pnpm run format:md`, `pnpm run hledger:format` as needed).
- Run tests locally: `pnpm run test` (CI runs the same suite); use `pnpm run test:py` to run pytest directly.
- When invoking Python scripts directly, set working directory to `scripts/` (tools that accept `cwd` should use that parameter).

## Quick commands & examples

- Validate journals: `pnpm run hledger:check` or `python -m scripts.check` (with `cwd=scripts/`).
- Format journals: `pnpm run hledger:format` or `python -m scripts.format`.
- Discover monthly journals (scripts use this glob): `**/*[0-9]{4}-[0-9]{2}/*.journal`.
- Encrypt/decrypt secrets: `python -m scripts.encrypt` / `python -m scripts.decrypt` (use `private.yaml.gpg` only when authorized).

## Project-specific rules & gotchas

- ALWAYS prefer `pnpm run <script>` when a wrapper exists. If no wrapper, run the Python script from `scripts/`.
- Never leak or hard-code secrets from `private.yaml` (encrypted file: `private.yaml.gpg`). If you need decrypt rights, ask.
- Follow code conventions strictly: `os.PathLike` for path parameters, timezone-aware UTC datetimes, complete type annotations, `__all__` module exports, and use Ruff for formatting. Prefer PEP 585 built-in generics for concrete containers (for example `list[str]`, `dict[str, int]`) and use `collections.abc` for abstract interfaces (for example `collections.abc.Sequence[str]`, `collections.abc.Mapping[str, int]`) instead of `typing`-based ABCs.
- Tests: one test file per production file; mirror `tests/` structure to the source layout. Prefer annotating pytest filesystem fixtures as `tmp_path: PathLike[str]` in test signatures and, when converting a path-like object to `str`, **always** use `os.fspath(path_like)` rather than `str(path_like)` so the filesystem path protocol is preserved and static checkers remain happy.

## When editing journals

- Follow `.github/instructions/editing-guidelines.instructions.md` and the `add-transactions` and `edit-journals` skills precisely.
- Journal path format: `ledger/YYYY/YYYY-MM/self.journal`.
- Use status markers correctly: `!` = pending, `*` = cleared, none = normal.

## Commit & PR guidance

- Use Conventional Commits and follow `.github/instructions/git-commits.instructions.md`.
- For journal-only commits use the single-line header format: `ledger(<list>): add N / edit M transaction(s)` (no body).
- Ensure commit bodies are wrapped to **72 characters** or fewer where possible (preferred); linting enforces a hard **100-character** maximum and will block commits that exceed it.

## If stuck or uncertain

- Ask one short clarifying question referencing the `SKILL.md` and the file(s) you plan to edit.
- If a change touches runtime scripts or validators, add tests and mention rationale in the commit body.

## Editing Skills & Instructions (short checklist)

- Add or update the `SKILL.md`/instruction text only after confirming exact behaviour with maintainers if unclear.
- Add or update unit tests that cover any changed behaviour (mirror `tests/` structure). Run `pnpm run test` and fix failures before committing.
- Update `AGENTS.md` and `agent-quickstart.instructions.md` if you introduce new commands, scripts, or workflow steps.
- Add a brief entry to the skill's `lessons.md` explaining why the change was made, and add a simple example to `examples.md` if helpful.

> Tip: The most common agent error is running scripts from the wrong directory — double-check `cwd` every time. 🔧
