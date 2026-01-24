#!/bin/bash
set -e

# Lint and fix all Markdown files using local tool via pnpm
pnpm exec -- markdownlint-cli2 --fix "**/*.md"
