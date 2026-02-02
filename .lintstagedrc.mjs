/**
 * @type {import('lint-staged').Configuration}
 */
export default {
  "**/*.{json,yml,yaml,css,scss,html,js,ts,tsx,jsx}": [
    "prettier --write",
  ],
  "**/*.{md,markdown}": [
    "pnpm run markdownlint:fix",
  ],
  "**/*.py": [
    "python -m ruff check --fix .",
    "python -m isort .",
    "python -m black ."
  ],
  "ledger/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]/**/*.journal": [
    "pnpm run hledger:format",
    "pnpm run hledger:check",
  ]
};
