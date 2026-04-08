---
name: Python entry points
description: Convention for writing Python scripts and modules with __name__ == "__main__" entry points
applyTo: "**/*.py"
---

# Python Entry Points Convention (self/ledger)

This document establishes the convention for Python scripts and modules in the ledger project that expose entry points for direct execution. All scripts in `scripts/` and any `__main__.py` modules must follow this pattern.

**Inheritance note:** This convention extends the parent repository's Python entry points convention (see `../../instructions/python-entry-points.instructions.md`). Local scripts follow the same `__main__ == "__main__"` pattern with Asyncer integration. Refer to the parent documentation for comprehensive guidance; this file provides ledger-specific context.

## Quick Pattern (Async)

```python
"""Script purpose and usage."""

from asyncer import runnify


async def main(argv: list[str] | None = None) -> None:
    """Main async entry point."""
    if argv is None:
        import sys
        argv = sys.argv[1:]
    
    # application logic here
    pass


def __main__() -> None:
    """Entry point for running the script directly."""
    runnify(main, backend_options={"use_uvloop": True})()


if __name__ == "__main__":
    __main__()
```

## Quick Pattern (Sync)

```python
"""Script purpose and usage."""


def main(argv: list[str] | None = None) -> None:
    """Main sync entry point."""
    if argv is None:
        import sys
        argv = sys.argv[1:]
    
    # application logic here
    pass


def __main__() -> None:
    """Entry point for running the script directly."""
    main()


if __name__ == "__main__":
    __main__()
```

## Ledger-Specific Rules

1. **Script location & invocation**: All utility scripts live in `scripts/` and are run via `bun run <script>` when a wrapper exists, or `uv run -m scripts.<cmd>` otherwise. Always set `cwd=scripts/` when invoking from Python tooling.

2. **Argument handling**: If a script accepts arguments (e.g., for transaction filtering, account selection), pass them through the `argv` parameter in `main()`. Include argument parsing (argparse or manual) inside `main()` to keep it testable.

3. **Error handling**: Use exit codes consistently:
   - `0`: Success
   - `1`: General error
   - `2`: Argument parsing error
   - `3`: File/IO error (missing journal, permission denied, etc.)
   - Example:

     ```python
     try:
         journal_path = Path(argv[0]) if argv else DEFAULT_JOURNAL
         if not journal_path.exists():
             print(f"Journal not found: {journal_path}", file=sys.stderr)
             return exit(3)
     except Exception as e:
         print(f"Error: {e}", file=sys.stderr)
         return exit(1)
     ```

4. **Testing**: Import `main` directly in tests; do not trigger the entry point guard. Use `@pytest.mark.anyio` for async tests:

   ```python
   @pytest.mark.anyio
   async def test_main_validates_journal(tmp_path):
       from scripts.validate import main
       # Test with a fixture journal path
       await main(['--journal', str(tmp_path / 'test.journal')])
   ```

5. **Type hints**: Always include return type hints. Use `-> None` for scripts that don't return a value (most cases). For argparse integration, document `argv: Sequence[str] | None = None` as the parameter type.

6. **Docstrings**: Include a module-level docstring explaining the script's purpose and typical usage. Example:

   ```python
   """Validate journal structure and transaction formatting.
   
   Usage:
       python -m scripts.validate --journal ledger/2024/2024-01/self.journal
   
   Checks: date format, account hierarchy, amount consistency, etc.
   """
   ```

## Integration with Parent Convention

This ledger project inherits the parent repository's Python entry points convention. Refer to `../../instructions/python-entry-points.instructions.md` for:

- Detailed rationale and background
- Integration with argparse and Click
- Comprehensive testing patterns
- Error handling best practices
- Asyncer helper functions (`asyncify`, `soonify`, `create_task_group`)

## Implementation Checklist for Ledger Scripts

When writing a new script or updating an existing one:

- [ ] Define `main()` as the primary logic (async or sync)
- [ ] Accept optional `argv: Sequence[str] | None = None` parameter in `main()`
- [ ] Define `__main__()` sync wrapper calling `main()` (with `runnify` for async)
- [ ] Place `if __name__ == "__main__":` guard at file end, calling `__main__()`
- [ ] Include return type hints: `-> None` for both functions
- [ ] Add module-level docstring with usage example
- [ ] Add docstrings to `main()` and `__main__()`
- [ ] Use appropriate exit codes (0, 1, 2, 3)
- [ ] Test by importing `main()` directly; do not trigger the guard
- [ ] Run `pyright`, `ruff check`, and `pytest` locally before committing

## Examples

### Example 1: Validate Transactions (Sync)

```python
"""Validate journal entries for formatting and consistency.

Usage:
    python -m scripts.validate --journal <path>

Checks account hierarchy, date format, amount precision, etc.
"""

import sys
from pathlib import Path
from typing import Sequence
import argparse


def validate_journal(path: Path) -> bool:
    """Validate a single journal file. Returns True if valid."""
    # implementation
    return True


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for validation."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="Validate journal")
    parser.add_argument("--journal", required=True, help="Path to journal file")
    args = parser.parse_args(argv)
    
    journal_path = Path(args.journal)
    if not journal_path.exists():
        print(f"Journal not found: {journal_path}", file=sys.stderr)
        return exit(3)
    
    if validate_journal(journal_path):
        print("✓ Journal is valid")
        return exit(0)
    else:
        print("✗ Journal has errors", file=sys.stderr)
        return exit(1)


def __main__() -> None:
    """Entry point for running the script directly."""
    main()


if __name__ == "__main__":
    __main__()
```

### Example 2: Async File Processing

```python
"""Process and archive monthly transactions.

Usage:
    python -m scripts.archive --year 2024 --month 01

Reads transactions from monthly journal, applies closing operations,
and updates archive.
"""

import sys
from pathlib import Path
from typing import Sequence
from asyncer import runnify, asyncify
import argparse


async def process_monthly_archive(year: int, month: int) -> None:
    """Archive a monthly journal asynchronously."""
    # Blocking I/O wrapped with asyncify
    journal_data = await asyncify(read_journal)(year, month)
    # more processing


async def main(argv: Sequence[str] | None = None) -> None:
    """Main async entry point."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="Archive monthly transactions")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    args = parser.parse_args(argv)
    
    if not (1 <= args.month <= 12):
        print(f"Invalid month: {args.month}", file=sys.stderr)
        return exit(2)
    
    try:
        await process_monthly_archive(args.year, args.month)
        print(f"✓ Archived {args.year}-{args.month:02d}")
        return exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return exit(1)


def __main__() -> None:
    """Entry point for running the script directly."""
    runnify(main, backend_options={"use_uvloop": True})()


if __name__ == "__main__":
    __main__()
```

## See Also

- Parent repository convention: `../../instructions/python-entry-points.instructions.md`
- Ledger testing guidance: `testing.instructions.md`
- Developer workflows: `developer-workflows.instructions.md`
- Common workflows: `common-workflows.instructions.md`
