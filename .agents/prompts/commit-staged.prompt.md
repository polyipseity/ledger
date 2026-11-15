---
name: commit-staged
description: Produce a commit message for the currently staged changes and commit by default.
argument-hint: Optional extras (e.g., ticket=ABC-123). To skip committing, pass `commitNow=no`.
---

# Commit Staged Change

**Never ask for confirmation or clarification. Always proceed automatically using best-effort defaults and available context.**

**Argument text:** `${@:-}` is whatever the caller passed with the prompt. If it contains `commitNow=no`, produce the commit message only and do not commit; any other text is extra guidance to apply.

## Workflow

1. **Read staged changes**
   - Run a single compound command to print the staged file list and full staged patch:

     ```shell
     git diff --cached --name-status --no-color && git --no-pager diff --cached --staged --patch --no-color
     ```

   - Present the exact command to be run. If not executed, produce a best-effort commit message from available context and stop.

2. **Compose commit message**

- Inspect Command 1 output and repository conventions (CONTRIBUTING.md, `.agents/`, `package.json`, `commitlint`, `prek.toml`, `CHANGELOG.md`, etc.).
- Produce a commit message with:
  - Short subject (~50 chars)
  - Optional body (each line **must be wrapped to 72 characters or fewer**; bullets allowed)
  - Footer (BREAKING CHANGE / Refs / Ticket), including the argument text `${@:-}` when it carries guidance to record
- **If the commit is rejected by commitlint due to line length or other formatting, rewrap and retry until the commit passes.**
- Prefer tooling-enforced rules. If unsure, default to Conventional Commits. **Strictly enforce commit header and body line length (72 chars max) as required by commitlint.**
- Do not show the proposed commit message to the user for confirmation before creating the commit. Proceed automatically to creating the commit using best-effort defaults and available context.

1. **Create the commit**
   - If the argument text contains `commitNow=no`, skip this step and only present the message.
   - Otherwise, present the exact command to create the commit from stdin and print the new SHA. **Both commands must be run in the same shell command block to ensure correct context.** Use the correct heredoc/here-string syntax for the detected shell:
     - **PowerShell (Windows):**

       ```powershell
       (@'
       <full commit message>
       '@ | git commit --file=-) ; git rev-parse HEAD
       ```

       **Note on special characters and quoting:**
       Prefer PowerShell single-quoted here-strings (`@'...'@`) to prevent variable expansion and avoid backtick (\`) escaping. If a double-quoted here-string (`@"..."@`) is used, be careful to escape backticks and `$` or switch to the single-quoted form.

     - **Bash/zsh (Linux/macOS):**

       ```bash
       (git commit --file - <<'MSG'
       <full commit message>
       MSG
       ) && git rev-parse HEAD
       ```

       **Note on special characters and quoting:**
       Use a single-quoted heredoc delimiter (`<<'MSG'`) to prevent shell expansion (backticks and `$` are preserved). If the delimiter (e.g., `MSG`) appears verbatim in the message, choose a different delimiter to avoid conflicts.

   - If Command 2 fails due to quoting/heredoc syntax, retry up to 3 corrected forms. For other failures, report the error and do not modify the index.

2. **Output**
   - 1–2 line summary: staged files and detected convention
   - Commit message block labelled `Commit message` (header/body/footer)
   - If Command 2 ran: `Commit result` with exit status and new commit SHA
   - 1–3 line justification why this message fits the change

## Rules

- Never ask for confirmation or clarification. Always proceed automatically using best-effort defaults and available context.
- Only run the two approved shell commands. Do not run `git add`, `git reset`, or otherwise change the index.
- If Command 1 is denied, still propose a best-effort commit message using available context.

## Inputs

- `${@:-}` — the caller's argument text: `commitNow=no` produces the commit message only, and any other text is extra guidance to apply

End of prompt.
