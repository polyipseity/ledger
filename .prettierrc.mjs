/**
 * Centralized Prettier config and canonical file globs.
 * The `FILE_GLOBS` export is intended to be imported by other tooling
 * such as `.lintstagedrc.mjs` so file-patterns are defined in one place.
 */
export const FILE_GLOBS = [
  "**/*.{json,yml,yaml,css,scss,html,js,ts,tsx,jsx}"
];

export default {
  printWidth: 88,
  tabWidth: 2,
  useTabs: false,
  singleQuote: true,
  trailingComma: "all",
  endOfLine: "lf",
  overrides: [
    {
      files: FILE_GLOBS,
      options: {},
    },
  ],
};
