#!/bin/bash
set -e
# This script propagates the exit code from the underlying command so it can be used with && in POSIX shells

# Lint and fix all Markdown files using local tool via pnpm
pnpm run markdownlint:fix
