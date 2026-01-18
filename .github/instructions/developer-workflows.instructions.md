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

### Available Scripts

**Validation and Formatting:**
- **Check journals**: `python -m check` - Validates all monthly journals using hledger's strict checking
- **Format journals**: `python -m format` - Auto-formats journals using `hledger print`, sorts comment properties

**Modifications:**
- **Depreciate assets**: `python -m depreciate [--from YYYY-MM] [--to YYYY-MM] ITEM AMOUNT CURRENCY` - Adds depreciation entries to specified date range
- **Shift balances**: `python -m shift [--from YYYY-MM] [--to YYYY-MM] ACCOUNT AMOUNT CURRENCY` - Adjusts account balances across date range
- **Replace text**: `python -m replace FIND REPLACE` - Find/replace text across all journal files

**Security:**
- **Encrypt**: `python -m encrypt` - Encrypts private.yaml using GPG
- **Decrypt**: `python -m decrypt` - Decrypts private.yaml.gpg for editing

### Monthly Journal Discovery Pattern

Scripts use glob pattern `**/*[0-9]{4}-[0-9]{2}/*.journal` to find monthly journals:
- Pattern matches: `2024-01/self.journal`, `2025-12/self.journal`, etc.
- Works recursively across any year/month structure
- Ensures future-proof journal discovery as new months are added

## Python Code Patterns

### Async/Await with Concurrency Control
```python
from asyncio import BoundedSemaphore, run as _run, gather
from anyio import Path as _Path

_BSemp = BoundedSemaphore(_cpu_c() or 4)  # Limit to CPU count or 4

async def task():
    async with _BSemp:
        # Concurrent work here
        pass

_run(gather(*[task() for _ in ...], return_exceptions=True))
```

All scripts use asyncio with `BoundedSemaphore` to limit concurrent subprocess execution to CPU count (or 4 as fallback). This prevents resource exhaustion.

### Frozen Dataclasses
```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True, kw_only=True, match_args=False)
class Config:
    """Configuration arguments."""
    
    start: str  # YYYY-MM format
    end: str    # YYYY-MM format
    value: float
```

Arguments defined as:
- **frozen=True**: Immutable after creation
- **slots=True**: Memory efficient storage
- **kw_only=True**: Keyword-only arguments
- **match_args=False**: Disable pattern matching on init params

### Path Handling
```python
from anyio import Path as _Path

async def process_file(path: _Path) -> None:
    if await path.is_file():
        content = await path.read_text()
        # Process content
```

Use `anyio.Path` for async file operations with async context managers. Enables concurrent file I/O without blocking.

### Import Aliases
Heavy use of underscore prefixes for cleaner code:
```python
from asyncio import run as _run, gather as _gather
from pathlib import Path as _Path
from os import cpu_count as _cpu_c
```

Aliases reduce visual clutter while maintaining clarity.

### Error Handling
```python
results = await _gather(*tasks, return_exceptions=True)
errors = [r for r in results if isinstance(r, Exception)]

if errors:
    raise BaseExceptionGroup("Task failures", errors)
```

Collect exceptions with `return_exceptions=True`, then raise `BaseExceptionGroup` if any errors occurred. Enables reporting all failures, not just the first.

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
