---
name: Common Workflows
description: Practical task guides for frequently performed operations including transaction entry, monthly migration, and script usage.
---

# Common Workflows

- Asynchronous helper code should use AnyIO/Asyncer; do not import `asyncio` directly.

Skills for frequently performed operations are listed in `AGENTS.md`. See the relevant `SKILL.md` for each task.

## Pre-Commit Checklist (prek hooks)

1. Format: `bun run format`
2. Validate: `bun run check`
3. Run tests: `bun run test`
4. If `private.yaml` was edited: the owner re-encrypts it; stop and ask.
5. Review: `git status && git diff`
6. Install hooks: `bun install` (provisions Python dependencies, the managed hledger binary, and the prek hooks)
7. Commit: `git commit -S -m "type(scope): message"`

A hook receives the matching paths on its own command line, and the journal formatter and Prettier both take them; `developer-workflows.instructions.md` describes each hook's shape.
