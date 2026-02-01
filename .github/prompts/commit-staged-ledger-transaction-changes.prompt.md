---
name: commit-staged-ledger-transaction-changes
description: Commit staged hledger transaction changes using strict ledger(...) format. Journal files are detected from staged changes. User provides number of transactions added/edited via input or extra.
argument-hint: added=3 edited=2 (optional extras; see below)"
agent: agent
---

# Commit Staged Ledger Transaction Changes

**Never ask for confirmation or clarification. Always proceed automatically using best-effort defaults and available context.**

## Workflow

1. **Read staged changes**
   - Run a single compound command to print the staged file list and full staged patch:

     ```shell
     git diff --cached --name-status --no-color && git --no-pager diff --cached --staged --patch --no-color
     ```

   - Present the exact command to be run. If not executed, produce a best-effort commit message from available context and stop.

2. **Determine affected journal files**
   - From the staged file list, collect all files matching `*.journal` **excluding** any under `preludes/`.
   - For each, use only the filename (not path/year/month) for the commit message (e.g., `self.journal`).
   - If multiple, join with comma (`,`).

3. **Get transaction counts**
   - The user must provide the number of transactions added and/or edited, either via input fields or as `added=N edited=M` in `${input:extra}`.
   - If only added or only edited, omit the other part from the commit message.
   - If neither is provided, stop and report an error.

4. **Compose commit message**
   - Use the strict format (no body, no extra lines):

     ```text
     ledger(<journal-list>): add N / edit M transaction(s)
     ```

   - Use only the parts relevant (see above).
   - Use `transaction(s)` exactly (for both singular and plural).
   - **No commit body.**

5. **Create the commit**
   - Present the exact command to create the commit from stdin and print the new SHA. Use the correct heredoc/here-string syntax for the detected shell:
     - **PowerShell (Windows):**

       ```powershell
       (@"
       <full commit message>
       "@ | git commit --file=-) ; git rev-parse HEAD
       ```

     - **Bash/zsh (Linux/macOS):**

       ```bash
       (git commit --file - <<'MSG'
       <full commit message>
       MSG
       ) && git rev-parse HEAD
       ```

   - If Command 2 fails due to quoting/heredoc syntax, retry up to 3 corrected forms. For other failures, report the error and do not modify the index.

6. **Output**
   - 1–2 line summary: staged journal files and detected convention
   - Commit message block labelled `Commit message` (header only)
   - If Command 2 ran: `Commit result` with exit status and new commit SHA
   - 1–3 line justification why this message fits the change

## Rules

- Never ask for confirmation or clarification. Always proceed automatically using best-effort defaults and available context.
- Only run the two approved shell commands. Do not run `git add`, `git reset`, or otherwise change the index.
- If Command 1 is denied, still propose a best-effort commit message using available context.

## Inputs

- `${input:added}` — number of transactions added (optional; can be in extra)
- `${input:edited}` — number of transactions edited (optional; can be in extra)
- `${input:extra}` — may contain `added=N edited=M` (parsed if present)
- `${input:commitNow}` — `no` to skip committing; default is to commit

---

**Prompt:**

Commit the currently staged changes using the strict ledger transaction commit format. Detect affected journal files from the staged file list (excluding `preludes/` and non-`.journal` files). Get the number of transactions added and/or edited from user input or `${input:extra}`. Then, generate a commit message in the required format and commit the staged changes with that message. Do not include a commit body or any extra lines.
