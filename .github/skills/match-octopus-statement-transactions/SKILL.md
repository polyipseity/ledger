---
name: match-octopus-statement-transactions
description: "Match Octopus Wallet statement rows to journal transactions and update transaction datetimes. Runs only when explicitly requested."
---

# Match Octopus Statement Transactions

## 🚩 Agent Workflow Reminder

Use the Todo List Tool for multi-step tasks (plan, mark a step `in-progress`, complete it, and update). See `AGENTS.md` for the concise agent workflow rules.

**Code & Tests:** Any Python code written to implement or extend this skill (including scripts, helpers, and tests) **MUST** include clear module-level docstrings and docstrings for all public classes and functions, and **MUST** use complete type annotations for function signatures and return types. Prefer modern typing styles (PEP 585 / PEP 604), built-in generics (`dict`, `list`, etc.), and annotate test function arguments/returns and local variables where helpful. Prefer `typing.Self` for methods that return the instance type (for example: `def clone(self) -> typing.Self:`); if supporting Python versions older than 3.11, use `typing_extensions.Self`. Code must be sufficiently typed so that **Pylance with `typeCheckingMode: "strict"` reports no type errors**. Avoid using `Any` or `Unknown` in type annotations; prefer explicit types, Protocols, or TypedDicts. Exception: `Any` or `Unknown` may be used only when there is a very strong, documented justification (for example, interfacing with untyped third-party libraries or representing truly dynamic/opaque data structures). When used, include an inline comment explaining the justification and a `# TODO` to refine the type later. If a cast is necessary, add a comment explaining why and a TODO to remove it once proper typing is available. See `.github/instructions/developer-workflows.instructions.md` and `AGENTS.md` for the canonical coding conventions.

## Purpose

Locate each entry in a monthly Octopus Wallet statement and, where a unique match exists in the repository journals, update only the transaction's datetime metadata. Record unmatched rows in the summary.

## Trigger

Run only when explicitly requested (e.g. "use match octopus statement transactions").

## Inputs

- OCR-extracted table of statement rows (columns: date, time, details, remarks, amount, balance) as CSV/JSON, or an image/PNG to OCR on demand.

## OCR command template

Use this ImageMagick template to convert a PDF to a high-res PNG. Do NOT include or echo any sensitive wallet numbers in filenames or outputs.

magick -density 300 "input-statement.pdf" -background white -alpha remove -quality 100 "output-statement.png"

Notes:

- Use an output pattern like `output-statement-%03d.png` for multi-page PDFs.
- Optional flags: `-trim`, `-shave`, `-resize`.

## Behavior and heuristics

- Matching priority (try in order):
  1. Exact date (YYYY-MM-DD), signed amount, and a details/remarks token (merchant name or reference ID).
  2. Signed amount and reference ID (e.g. FRN... or card Ref).
  3. Fallback: signed amount and nearest date within ±1 day.

- Time update rules:
  - Typical case: journal has same date, hour and minute but lacks seconds — append statement seconds to journal time (silent by default).
  - Non-typical case: any change that alters minute, hour, or date, or changes seconds when the journal already included seconds — these must be reported and shown with original and updated datetimes.

- Tie-breaking & pairing:
  - Prefer matches containing a bank transfer reference (FRN...) when present.
  - Treat paired flows (bank transfer FRN credit followed by wallet→card debit on same date) as linked and update both times consistently.
  - If multiple candidates remain, list them and require user confirmation; do not auto-apply.

- Timezones: treat statement times as local (UTC+08:00) by default; preserve timezone tags and avoid implicit conversions unless the user requests one.

- Never modify amounts or postings — only change datetime metadata.

## Summary & output

After processing produce a concise summary containing only:

- Non-typical updates: show original and updated transaction text and file path for manual review.
- Missing transactions: statement rows with no unique match.

Typical seconds-only edits are omitted from the normal summary. To include those, run with a `--verbose` flag (e.g. "use match octopus statement transactions --verbose").

## Validation

- Optionally run formatting and validation scripts after edits:

  ```powershell
  python -m format   # set cwd to scripts/
  python -m check    # set cwd to scripts/
  ```

**Scripts & working directory**: See `.github/instructions/developer-workflows.instructions.md` for canonical rules. Short: prefer `pnpm run <script>`; if running Python directly, set `cwd=scripts/`.

- The skill can produce a patch/diff for review but does not commit changes.

## Security & privacy

- Do not log or store full Octopus wallet numbers. Redact any full wallet numbers from outputs and filenames. The skill must never write the wallet number into repository files or skill outputs.

## Notes

- Be conservative: require a unique match before auto-editing. When unsure, surface candidate matches for human confirmation.
- The user is responsible for committing any repository changes.
  - If an agent commits changes on your behalf, the agent must follow `.github/instructions/git-commits.instructions.md`. For ledger transaction commits use the exact `ledger(<journal-list>): add N / edit M transaction(s)` header and no body.

## Example invocation

Use match octopus statement transactions on December 2025 PNG and update journal entries; show summary.
