---
name: Agent Glossary
description: Short, canonical definitions of common agent terms and quick reminders used by skills and instructions.
---

# Agent Glossary (Quick Reference)

This short glossary lists concise definitions and canonical reminders for agents. Use this for quick lookups; refer to full instructions for details.

- Todo List Tool: Plan multi-step tasks, mark one step `in-progress`, complete it, then continue. Always use for complex work.
- Status markers: `!` = pending, `*` = cleared; use only where specified by the skill (e.g., lending/borrowing patterns).
- Prelude include: Monthly journals must start with `include ../../../preludes/self.journal` (or the alternatives prelude for alternatives journals).
- Journal path format: Use full paths: `ledger/[year]/[year]-[month]/[name].journal`.
- Scripts & working directory: Prefer `pnpm run <script>` from repo root; when invoking Python directly, set `cwd=scripts/`. See `.github/instructions/agent-quickstart.instructions.md` for a concise checklist of the most-used commands and gotchas.
- Formatting & validation: Run `pnpm run format` then `pnpm run check` before committing; fix errors first.
- Ledger commits: Use `ledger(<journal-list>): add N / edit M transaction(s)` for transaction commits — **single-line header only**.
- Migration: Run `hledger close --migrate` for monthly migration and copy opening/closing transactions into the correct monthly files.
- Confidential data: Never commit unencrypted `private.yaml`; use `python -m encrypt` / `python -m decrypt` per security instructions.
- Two-pass upserts (Octopus flow): Pass 1 = match & update existing journal entries only; Pass 2 = add unmatched transactions only.

Keep this file short and scan it when you need quick reminders while working in skills.
