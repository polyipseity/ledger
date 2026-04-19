---
name: Common Workflows
description: Practical task guides for frequently performed operations including transaction entry, monthly migration, and script usage.
---

# Common Workflows

- Asynchronous helper code should use AnyIO/Asyncer; do not import `asyncio` directly.

Skills for frequently performed operations are listed in `AGENTS.md`. See the relevant `SKILL.md` for each task.

## Pre-Commit Checklist (Husky + lint-staged)

1. Format Markdown: `bun run markdownlint:fix`
2. Format journals: `bun run format`
3. Validate journals: `bun run check`
4. Run tests: `bun run test`
5. If edited `private.yaml`: `bun run encrypt` (or `python -m scripts.encrypt` with `cwd=scripts/`)
6. Review: `git status && git diff`
7. Install hooks: `bun install` (registers Husky hooks; runs `uv sync` for Python extras)
8. Commit: `git commit -S -m "type(scope): message"`

**lint-staged note:** When a lint-staged command needs staged file paths, invoke the underlying command directly (e.g. `python -m scripts.format`) rather than `bun run format`, so file args are forwarded. See `developer-workflows.instructions.md` for details.
