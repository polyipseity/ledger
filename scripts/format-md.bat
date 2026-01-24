@echo off
REM Lint and fix all Markdown files using pnpm
pnpm exec -- markdownlint-cli2 --fix "**/*.md"
