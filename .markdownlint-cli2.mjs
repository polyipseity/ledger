import config from './.markdownlint.json' with { type: 'json' };

export default {
  ...config,
  globs: ["**/*.md"],
  // Use repository gitignore to exclude files (faster for large trees)
  gitignore: true
};
