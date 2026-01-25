---
name: commit-staged-change
description: Produce a commit message for the currently staged changes and commit by default.
argument-hint: Optional extras (e.g., ticket=ABC-123). To skip committing, pass `commitNow=no`.
agent: agent
---

# Commit Staged Change

When run, follow these exact steps. Do not modify, stage, or unstage any files. After composing the commit message, create the commit for the currently staged changes by default unless the input variable `commitNow` is set to `no`. Creating the commit must not change which files are staged — only create a commit from the current index.

1. Obtain the current staged change (the index / staging area) for the workspace. Use git commands to collect the minimal summary and the full staged diff. Recommended commands:

    - git diff --cached --name-status
    - git --no-pager diff --cached --staged --patch --no-color

    Include the output of the first command (file list + status) and a brief summary of the staged diff in your reasoning.

2. Detect any commit conventions used in this workspace and follow them when composing the commit message. Search for common configuration files, scripts, and documentation that declare or imply a commit message policy. Examples to check (not exhaustive):

    - `.github/instructions/git-commits.instructions.md`, `CONTRIBUTING.md`, `README.md` or other docs that explain commit style.
    - `package.json` scripts and config fields (e.g., `commitlint`, `config.commitizen`, `husky`, `semantic-release`).
    - commitlint configs: `commitlint.config.js`, `.commitlintrc.js`, `.commitlintrc.json`, `.commitlintrc.yaml`.
    - Commitizen / cz: `.czrc`, `cz-config.js`, `commitizen` entries in `package.json`.
    - tooling/release config: `.releaserc`, `release.config.js`, `semantic-release` config.
    - presence of Git hooks in `.husky/`, `.git/hooks/` that enforce message formats.
    - repository-level conventions in `.github/` workflows, issue templates, or docs (e.g., `.github/ISSUE_TEMPLATE`, `.github/PULL_REQUEST_TEMPLATE`).
    - presence of Conventional Commits examples in CHANGELOG.md or other release notes.

    If you detect a convention, state it clearly and explain how your message conforms. If multiple conventions are present and conflict, list them and choose the one that is enforced by tooling (commitlint, husky hooks, CI) or documented in repository files; if unsure, ask one concise clarifying question and otherwise default to Conventional Commits style (type(scope): short summary) with a 50-72 character summary line and a wrapped body ~72 chars.

3. Write a commit message based on the staged change. The message must be ready-to-use. Provide:

    - A single-line commit header (subject) that follows the detected convention.
    - An optional commit body explaining the why and what changed, with bullet points for important details.
    - A one-line footer if relevant (e.g., `BREAKING CHANGE:` or `Refs:` or `Ticket:`) if the staged changes require it.

4. If the input variable `${input:commitNow:placeholder}` is set to `no` (case-insensitive), skip creating the commit and only produce the message. Otherwise (default: `yes`) create the commit from the current index using the message you produced. Use a safe single command that reads the message from stdin; for example:

    ```shell
    git commit --no-verify --file - <<'MSG'
    <the full commit message text produced above>
    MSG
    ```

    - If performing the commit, report the git commit exit status and the new HEAD commit SHA.
    - If the commit fails, report the error and do NOT attempt any corrective staging.

5. Output format (strict):

    - First, a 1–2 line summary describing which files are staged and the detected commit convention.
    - Then the proposed commit message, clearly labeled:

      ```text
      Commit message
      ----------------

      <commit header>

      <commit body (if any)>

      <commit footer (if any)>
      ```

    - If a commit was performed, also include the result of running `git commit` (success/failure and new commit SHA) after the commit message.
    - Finally, a brief (1–3 lines) justification explaining why the chosen header and body suit the staged change.

6. Constraints and rules (must follow):

    - Do not edit any files in the repository other than creating the commit object (if `${input:commitNow}` is `yes`).
    - Do not run `git add` or `git reset` and do not change which files are staged.
    - If additional clarification is required to write a good message, list the specific questions but still propose a best-effort commit message based on available staged diff.

7. Optional input variables:

    - `${input:extra:placeholder}` — if provided, incorporate it into the commit body or footer (for example a ticket number or extra reviewer note).
    - `${input:commitNow:placeholder}` — if set to `no`, skip creating the commit. Default behavior is to create the commit (default: `yes`).

End of prompt.
