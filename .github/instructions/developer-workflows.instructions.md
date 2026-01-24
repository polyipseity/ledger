---
name: Developer Workflows
description: Development workflows, utility scripts, code patterns, and testing/validation practices for maintaining the ledger system.
---

# Developer Workflows

Development workflows, utility scripts, code patterns, and testing/validation practices.

## Running Scripts

All utility scripts have three versions for different operating systems:

- `.sh` (Shell script for Linux/macOS)
- `.bat` (Batch file for Windows)
- `.py` (Python module for all platforms, executable as `python -m <script>`)

Note: the `.sh` and `.bat` wrapper scripts assume they are run with the current working directory set to the `scripts/` folder (they invoke the Python module relative to that directory).

### Available Scripts

**Validation and Formatting:**

- **Check journals**: `python -m check` - Validates all monthly journals using hledger's strict checking
- **Format journals**: `python -m format` - Auto-formats journals using `hledger print`, sorts comment properties
- **Check formatting**: `python -m format --check` - Validates that journals are formatted without modifying them (exits with code 1 if unformatted files found)

**Modifications:**

- **Depreciate assets**: `python -m depreciate [--from YYYY-MM] [--to YYYY-MM] ITEM AMOUNT CURRENCY` - Adds depreciation entries to specified date range
- **Shift balances**: `python -m shift [--from YYYY-MM] [--to YYYY-MM] ACCOUNT AMOUNT CURRENCY` - Adjusts account balances across date range
- **Replace text**: `python -m replace FIND REPLACE` - Find/replace text across all journal files

**Security:**

- **Encrypt**: `python -m encrypt` - Encrypts private.yaml using GPG
- **Decrypt**: `python -m decrypt` - Decrypts private.yaml.gpg for editing

### Markdown Formatting & Linting

- Use markdownlint (VS Code extension) for on-save fixes where supported
- Prefer using pnpm and the repo scripts: `pnpm install` then `pnpm run lint:md` to lint; to auto-fix use the `scripts/format-md.sh` or `scripts/format-md.bat` helpers which invoke the local tool
- CI runs use `.github/workflows/markdownlint.yml` which installs deps via pnpm and runs `pnpm run lint:md`
- Configuration: `.markdownlint.jsonc` and `.editorconfig` at repo root

### Monthly Journal Discovery Pattern

Scripts use glob pattern `**/*[0-9]{4}-[0-9]{2}/*.journal` to find monthly journals:

- Pattern matches: `2024-01/self.journal`, `2025-12/self.journal`, etc.
- Works recursively across any year/month structure
- Ensures future-proof journal discovery as new months are added

## Python Code Patterns

- Scripts use `asyncio.BoundedSemaphore` to limit concurrency to CPU count (or 4 as fallback)
- Frozen dataclasses with `@dataclass(frozen=True, slots=True, kw_only=True, match_args=False)` for config
- Path operations via `anyio.Path` for async file I/O

## Testing & Validation

### Pre-Commit Validation Workflow

Run `python -m check` before committing to validate all changes:

1. **Finds all monthly journals** recursively using glob pattern
2. **Runs hledger validation** with strict mode checking:
   - `accounts`: Verifies all accounts are defined
   - `assertions`: Validates balance assertions
   - `autobalanced`: Ensures balanced postings
   - `balanced`: Verifies double-entry bookkeeping
   - `commodities`: Validates commodity usage
   - `ordereddates`: Checks date ordering
   - `parseable`: Confirms valid hledger syntax
   - `payees`: Verifies payee definitions
   - `tags`: Validates tag usage
3. **Limits concurrency** using semaphore to CPU count

**Best Practice**: Always run `python -m check` before `git commit`.

### Format Validation

- Run `python -m format` after editing to ensure consistent formatting
- The formatter:
  - Rewrites journals using `hledger print` for canonical format
  - Sorts comment properties alphabetically
  - Standardizes spacing and indentation
  - Preserves include statements unchanged

### Script Execution Patterns

**Common pattern across all scripts:**

1. Collect all monthly journals via glob
2. Create async task per journal
3. Execute with BoundedSemaphore concurrency control
4. Gather results with return_exceptions=True
5. Report any BaseExceptionGroup errors

## Key Implementation Details

- **Thread-safe**: Uses asyncio for I/O-bound operations, not multi-threading
- **Resource-aware**: BoundedSemaphore prevents overwhelming system resources
- **Batch processing**: Glob pattern enables processing all journals in one operation
- **Error resilient**: Collects all errors before reporting, doesn't stop on first failure
- **Extensible**: New scripts follow same async/dataclass/error handling patterns

### Commit message format

Agents and humans should follow repository commit conventions. See `.github/instructions/git-commits.instructions.md` for the canonical rules. In short:

- Use Conventional Commits for all commits.
- For ledger transaction commits use the exact `ledger(<journal-list>): add N / edit M transaction(s)` header format. When such ledger commits are made by agents, they MUST contain only the single-line header (no body).
- Run `python -m check` before committing changes to journal files.
