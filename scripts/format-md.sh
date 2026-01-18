#!/bin/bash
set -e

# Lint and fix all Markdown files
markdownlint-cli2 --fix "**/*.md"
