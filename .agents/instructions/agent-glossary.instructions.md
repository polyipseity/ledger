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
- Scripts & working directory: `bun run <script>` from the repository root, or `-m scripts.<mod>` from that same root. See `.agents/instructions/agent-quickstart.instructions.md` for a concise checklist of the most-used commands and gotchas.
- Formatting & validation: Run `bun run format` then `bun run check` before committing; fix errors first.
- Ledger commits: Use `ledger(<journal-list>): add N / edit M transaction(s)` for transaction commits — **single-line header only**.
- Migration: `bun run clopen <YYYY-MM>` writes the closing and the next opening. See `.agents/skills/migrate/SKILL.md`.
- Confidential data: Never commit unencrypted `private.yaml`; decrypt and encrypt with `scripts/decrypt.sh` and `scripts/encrypt.sh` per security instructions.
- Two-pass upserts (Octopus flow): Pass 1 = match & update existing journal entries only; Pass 2 = add unmatched transactions only.

Keep this file short and scan it when you need quick reminders while working in skills.
