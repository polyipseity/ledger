import { FILE_GLOBS as PRETTIER_FILE_GLOBS } from "./.prettierrc.mjs";

/**
 * @type {import('lint-staged').Configuration}
 */
export default {
  [PRETTIER_FILE_GLOBS[0]]: [
    "prettier --write",
  ],
  "**/*.{md,markdown}": [
    "pnpm run markdownlint:fix",
  ],
  "**/*.sh": [
    "shfmt -w"
  ],
  "**/*.py": [
    "python -m ruff --fix .",
    "python -m isort .",
    "python -m black ."
  ],
  "ledger/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]/**/*.journal": [
    "pnpm run hledger:format",
    "pnpm run hledger:check",
  ]
};
