/**
 * Prettier configuration.
 *
 * Note: we no longer export shared file-glob constants. Lint-staged specifies
 * file globs directly and the Prettier CLI is invoked via scripts
 * using explicit file globs in `package.json`.
 */
export default {
  printWidth: 88,
  tabWidth: 2,
  useTabs: false,
  singleQuote: true,
  trailingComma: "all",
  endOfLine: "lf",
};
