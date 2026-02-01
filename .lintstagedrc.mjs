/**
 * @type {import('lint-staged').Configuration}
 */
export default {
  "**/*.{md,markdown}": [
    "pnpm run markdownlint:fix",
  ],
  "ledger/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]/**/*.journal": [
    "pnpm run hledger:format",
    "pnpm run hledger:check",
  ],
};
