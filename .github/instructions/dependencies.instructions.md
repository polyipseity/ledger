---
name: Critical Dependencies
description: Required software and tools that enable this accounting system, including hledger, Python, anyio, and GPG with installation and troubleshooting guidance.
---


# Critical Dependencies

**Note:** See `AGENTS.md` for agent workflow rules and use the Todo List Tool for multi-step tasks.

Required software and tools that enable this accounting system.

## Required Software

### hledger

**What it is:** The core accounting engine—a plain text accounting system supporting double-entry bookkeeping.

**How it's used:**

- Validates journal syntax and correctness (`python -m check` uses `hledger --strict`)
- Formats journals into canonical format (`python -m format` uses `hledger print`)
- Generates migration transactions (`hledger close --migrate` for monthly boundaries)
- Supports powerful queries and reporting (can query with `hledger [options] ACCOUNTS`)

**Installation:** Download from [hledger.org](https://hledger.org) or install via package manager

**Verification:** `hledger --version` should show version info

**In PATH requirement:** Must be in system PATH so scripts can execute `hledger` command

### Python 3.11+

**What it is:** Programming language used for utility scripts.

**Features used:**

- **Modern syntax**: `match_args`, `kw_only`, `slots` in dataclasses
- **Async/await**: Concurrent subprocess execution
- **Type hints**: Full type annotations throughout. All code should be written and annotated so that Pylance configured with `typeCheckingMode: "strict"` produces no errors in CI or locally.
- **No `Any`/`Unknown`**: Do **not** use `Any` or `Unknown` in type annotations. Use explicit types, small Protocols, or TypedDicts instead and document any temporary casts with a TODO to replace them with proper types.
- **Docstrings**: All Python code (modules, classes, functions and tests) must include clear docstrings describing purpose and behaviour.

**Installation:** Download from [python.org](https://python.org)

**Verification:** `python --version` should show 3.11 or newer

**In PATH requirement:** Python executable must be in PATH

### anyio

**What it is:** Async compatibility library for I/O operations.

**Installation:**

```powershell
# Add to `pyproject.toml` (project or dev deps), then install:
uv sync
```

**How it's used:** Provides async path objects (`anyio.Path`) for concurrent file I/O. For public APIs prefer `os.PathLike` and coerce `PathLike` to `anyio.Path` inside functions that perform async file operations. When a `PathLike` needs to be converted to a string, **always** use `os.fspath(path_like)` rather than calling `str(path_like)` directly; `os.fspath` is the canonical conversion that respects objects implementing the filesystem path protocol. Imports must be at module top-level; both `import ...` and `from ... import ...` forms are allowed at module top-level — prefer `from module import name` where practical (for example, `from os import fspath`) and never use inline/runtime imports.

**Requirement in:** `pyproject.toml` (see `pyproject.toml` in the repository root)

### GPG (GNU Privacy Guard)

**What it is:** Encryption/decryption tool using OpenPGP standard.

**How it's used:**

- Encrypts `private.yaml` to `private.yaml.gpg` before committing
- Decrypts `private.yaml.gpg` for editing confidential mappings
- Uses public key for encryption, private key for decryption
- Private key is password-protected for security

**Installation:**

- **Windows**: Download from [gnupg.org](https://www.gnupg.org) or use package manager (Chocolatey: `choco install gnupg`)
- **macOS**: `brew install gnupg`
- **Linux**: `apt-get install gnupg` (Debian/Ubuntu) or equivalent

**Verification:** `gpg --version` should show version info

**In PATH requirement:** GPG executable must be in PATH

**Key setup:** Requires GPG keypair already generated with `gpg --gen-key`

## Optional but Recommended

### Git

**Why:** Version control for the ledger repository

**Installation:** Download from [git-scm.com](https://git-scm.com)

**Verification:** `git --version`

### Type checking

**Why:** Fast editor and CI feedback for Python types. This repository uses **Pyright** for static type checking and **Ruff** for linting/formatting (Ruff is the single tool used for Python linting, formatting, and import-sorting; neither Black nor isort are used here). Run locally with `pnpm run check:py` (this runs Pyright alongside Ruff); CI runs the Python linters (`pnpm run check:py`).

### PowerShell (for Windows users)

**Why:** Recommended shell for running scripts on Windows

**Version:** PowerShell 7+ (cross-platform) recommended, or PowerShell 5.1 (Windows built-in)

**Installation:** Built-in on Windows; can upgrade to PowerShell Core

## Dependency Versions

| Dependency | Minimum Version | Verified With     |
| ---------- | --------------- | ----------------- |
| hledger    | 1.30+           | Latest 1.x        |
| Python     | 3.11            | 3.11, 3.12, 3.13  |
| anyio      | 3.6.2           | 4.0+              |
| GPG        | 2.0+            | 2.2, 2.3          |
| Git        | 2.20+           | Latest            |

## Verification Checklist

Verify all dependencies are installed and accessible:

```powershell
# Check hledger
hledger --version
# Output: hledger 1.x.x

# Check Python
python --version
# Output: Python 3.11+ 

# Check anyio
python -c "import anyio; print(anyio.__version__)"
# Output: 4.0+ or 3.x+

# Check pytest and friends
uv run --locked pytest --version
# Output: pytest X.Y.Z

# Run tests
pnpm run test
# Equivalent to: uv run --locked pytest

# Check GPG
gpg --version
# Output: gpg (GnuPG) 2.x.x

# Check Git (optional but recommended)
git --version
# Output: git version 2.x+
```

All should show **no errors**.

### Dev/test dependencies

Testing and async support are provided via these dev extras (installed by `uv sync`):

- `pytest` (test runner)
- `pytest-asyncio` (async test support)
- `pytest-cov` (coverage)
- `ruff` (formatting & linting tool)

When adding tests that require additional packages, add them to the `dev` dependency group in `pyproject.toml` and ensure `prepare` (runs `uv sync`) will install them locally.  Note: you do not need to invoke `prepare` explicitly; package managers run it for you on installs that do not use `--ignore-scripts`.

## Troubleshooting Dependencies

### hledger not found

```powershell
# Error: "hledger not found" or "command not found: hledger"

# Solution 1: Check PATH
$env:PATH -split ';' | Select-String 'hledger'

# Solution 2: Add to PATH
# [Windows] Add C:\Program Files\hledger\ to System Environment Variables

# Solution 3: Reinstall and ensure PATH option is checked
```

### Python version mismatch

```powershell
# Error: "Unsupported Python version"

# Check version
python --version

# If shows Python 2.x, use python3 instead
python3 --version

# Create alias if needed
Set-Alias -Name python -Value python3 -Scope CurrentUser
```

### anyio not installed

```powershell
# Error: "No module named anyio"

# Add the requirement to `pyproject.toml` (dev or project deps), then run:
uv sync
# Prefer using `uv sync` with `pyproject.toml` + `uv.lock` for reproducible installs
```

### GPG not found

```powershell
# Error: "gpg not found" when running encrypt/decrypt

# Check installation
gpg --version

# Install via Chocolatey (Windows)
choco install gnupg

# Install via Homebrew (macOS)
brew install gnupg

# Install via apt (Linux)
apt-get install gnupg
```

### GPG key not found

```powershell
# Error: "No public/private key found"

# List existing keys
gpg --list-secret-keys

# Generate new keypair
gpg --gen-key

# For automated/batch operations
gpg --batch --generate-key <<EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Your Name
Name-Email: your.email@example.com
Expire-Date: 0
%no-protection
%commit
EOF
```

## Platform-Specific Notes

### Windows

- Use PowerShell 5.1+ or PowerShell Core 7+
- All scripts have `.bat` and `.py` versions for Windows compatibility
- Ensure hledger and GPG are added to PATH via System Environment Variables
- May need to allow script execution: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### macOS

- Python 3.x should be installed via `brew install python@3.11`
- hledger available via Homebrew: `brew install hledger`
- GPG available via Homebrew: `brew install gnupg`
- Use `.sh` shell scripts for best experience

### Linux

- Python 3.11+ available via package manager (Python 3.10 likely already available)
- hledger available via package manager or [hledger.org](https://hledger.org)
- GPG included with most distributions: `apt-get install gnupg`
- Use `.sh` shell scripts

## System Requirements

### Minimum

- **OS:** Windows 10, macOS 10.14, or modern Linux distribution
- **RAM:** 512 MB free
- **Disk:** 100 MB free
- **Network:** Optional (only needed for git push/pull)

### Recommended

- **OS:** Windows 11, macOS 12+, or recent Linux
- **RAM:** 2+ GB
- **Disk:** 500 MB free
- **Network:** Broadband for repository operations
