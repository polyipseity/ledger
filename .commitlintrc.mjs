import process from "node:process";

export default {
  extends: ["@commitlint/config-conventional"],
  ignores: [
    () =>
      Boolean(
        process.env.GITHUB_DEPENDABOT_CRED_TOKEN ||
        process.env.GITHUB_DEPENDABOT_JOB_TOKEN,
      ),
    (message) => message.includes("Signed-off-by: dependabot[bot]"),
  ],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "build",
        "chore",
        "ci",
        "docs",
        "feat",
        "fix",
        "ledger", // custom type for ledger-related commits
        "perf",
        "refactor",
        "revert",
        "style",
        "test",
      ],
    ],
  },
};
