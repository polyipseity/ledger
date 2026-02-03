/**
 * @type {import('lint-staged').Configuration}
 */
export default {
  "**/*.{md,markdown}": [
    "pnpm run format:md",
  ],
  "**/*.{json,yml,yaml,css,scss,html,js,ts,tsx,jsx}": [
    "pnpm run format:prettier",
  ],
  "**/*.py": [
    "pnpm run format:py",
  ],
  "ledger/[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9]-[0-9][0-9]/**/*.journal": [
    "pnpm run format:journal",
  ]
};
