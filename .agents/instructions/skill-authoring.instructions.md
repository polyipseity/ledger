---
name: Skill Authoring Instructions
description: "Rules for writing and editing the agent skills under .agents/skills — the file layout, the line budgets, the section skeleton, the single-source-of-truth boundary between skills, and the data-file conventions."
applyTo: ".agents/skills/**"
---

# Skill authoring

**One job per skill.** A skill's `description` names its trigger and its job in one sentence, and two skills that could both claim one request mean one description is wrong.

**The budgets.** Every skill stays inside its `SKILL.md` line budget, and this table is the single source of truth: a documentation test parses the fenced block, so it keeps one skill name and one number per line, with the numbers honest against the files.

```text
skill                      SKILL.md <= lines
add-payee                  60
fix-journals               150
ingest                     160
ingest-attachments         60
ingest-currency            80
ingest-food                120
ingest-import              110
ingest-lending             110
ingest-octopus             120
ingest-payee               90
ingest-platform            100
ingest-remove              50
ingest-statement           90
ingest-tags                80
ingest-transport           90
migrate                    130
```

**The skeleton.** An `ingest-*` aspect runs When to use, Rules, Procedure, Worked example, and Stop and ask, in that order; `ingest`, `fix-journals`, and `migrate` take sections shaped by the task they do; and `add-payee` puts Stop and ask before its Worked example.

**One rule, one file.** Journal syntax is `transaction-format.instructions.md`'s, the rules of an edit are `editing-guidelines.instructions.md`'s, the commands and their invocation are `AGENTS.md`'s, a failing check is `fix-journals`'s, and a month boundary is `migrate`'s. A skill links the owner instead of restating it.

**Assets.** Every file beside a `SKILL.md` is named in that `SKILL.md`, or the documentation test fails, and shared data lives in `.agents/skills/ingest/` for its siblings to reach as `../ingest/<file>`.

**Data files.** A `payee_mappings.yml` value is a list of one or more payees the preludes declare, never an identity mapping and never an undeclared target; `id_mappings.yml` holds each payee's identifier orders and shape hints; `food_translations.yml` holds item-name translations alone.

**Never.** No lessons file, no per-skill test directory, no dated narration, no harness mechanics such as subagent prompt blocks or tool names, no confidential data, and no wallet, card, or account number.

**Tests.** Documentation contracts and repository-state invariants live in `tests/docs/`, so a skill directory never carries a `tests_*` directory of its own.
