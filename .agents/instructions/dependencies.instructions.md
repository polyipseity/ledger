---
name: Critical Dependencies
description: "Use when a tool is missing, a version is wrong, or a script cannot find hledger, Python, the lockfile, or gpg."
---

# Dependencies

Four tools make up the machine surface. `README.md` holds the human install steps and the per-tool troubleshooting; this file holds what an agent needs to know about each.

| tool | what an agent needs to know |
| --- | --- |
| `bun` | the task surface. Every command is `bun run <name>` from the repository root, and `package.json` pins bun's own version in its `packageManager` field. |
| `uv` with Python 3.13 | runs `scripts/` and the tests. `pyproject.toml` requires 3.13, and `bun install` runs `uv sync` from its `prepare` script, which provisions the locked runtime dependencies (`anyio`, `asyncer`, `pydantic`, `pydantic-yaml`) together with the dev group that supplies `pytest`, `hypothesis`, `ruff`, and `ty`. |
| `hledger` | provisioned rather than installed by hand: `bun run hledger:install` writes `node_modules/.bin/hledger` at the version `scripts/install-hledger.mjs` pins, and `bun install` runs it. `scripts/utils/journals.py` resolves that path first and consults `PATH` only when the file is absent; with neither present it raises `FileNotFoundError` instead of running a different binary. |
| `gpg` | reaches `private.yaml.gpg` alone. Decryption and encryption are the owner's actions (`security.instructions.md`), so an agent that needs a mapping resolved stops and asks. |

## Troubleshooting

- **`hledger executable not found in node_modules/.bin/ or PATH`** — provisioning did not finish. `bun run hledger:install` writes the binary, and `--force` replaces a partial download.
- **`No module named 'scripts'`** — the module was run outside the repository root. The package imports relatively, so it runs only as `-m scripts.<mod>` from that root, or through its `bun run` name.
- **`uv sync` refuses the interpreter** — `pyproject.toml` requires Python 3.13. Install one with `uv python install 3.13`, then run `uv sync` again.
- **`ruff` or `ty` is missing** — both come from the dev group that `uv sync` installs, and `bun run check:py` runs `ruff check`, `ruff format --check`, and `ty check`.
- **`gpg: decryption failed: No secret key`** — the owner's private key is not in this keyring, and no agent-side fix exists: report it.
