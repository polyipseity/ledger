---
name: Architecture & File Organization
description: Understand the hierarchical journal structure, file organization, and include patterns in the ledger system.
---


# Architecture & File Organization

**Note:** See `AGENTS.md` for agent workflow rules and use the Todo List Tool for multi-step tasks.

## Hierarchical Journal Structure

The ledger is organized in a hierarchical tree structure with shared definitions inherited from preludes. Payees must be registered in `preludes/*.journal` and kept alphabetized; see `.github/instructions/transaction-format.instructions.md` and the `add-payee` skill for canonical rules.

- **Entry point**: [ledger/index.journal](../../ledger/index.journal) includes `self.journal` and `self.alternatives.journal`
- **Year-level**: [ledger/YYYY/self.journal](../../ledger/2024/self.journal) includes monthly journals (e.g., `2024-01/self.journal`)
- **Month-level**: [ledger/YYYY/YYYY-MM/self.journal](../../ledger/2024/2024-01/self.journal) contains actual transactions with prelude includes
- **Preludes**: [preludes/self.journal](../../preludes/self.journal) defines account types, commodity formats, payees, and tags

Each monthly journal starts with `include ../../../preludes/self.journal` to inherit global definitions.

### Directory Example

```txt
ledger/
  index.journal              # Root: includes self.alternatives.journal, self.journal
  self.journal              # Includes 2024/self.journal, 2025/self.journal, ...
  self.alternatives.journal # Includes 2024/self.alternatives.journal, ...
  2024/
    self.journal            # Includes 2024-01/self.journal, 2024-02/self.journal, ...
    self.alternatives.journal
    2024-01/
      self.journal          # Monthly transactions with opening/closing balances
    2024-02/
      self.journal
    ...
  2025/
    ...

preludes/
  index.journal             # Includes self.alternatives.journal, self.journal
  self.journal              # Global account, commodity, payee, tag definitions
  self.alternatives.journal # Alternative scenario commodity definitions
```

## Include Hierarchy

The include system allows centralized management of account definitions and rules:

1. **Root level** (`ledger/index.journal`): Includes the two main journal streams
2. **Yearly level** (`ledger/YYYY/self.journal`): Organizes journals by year
3. **Monthly level** (`ledger/YYYY/YYYY-MM/self.journal`): Contains actual transactions
4. **Prelude inclusion**: Each monthly journal includes `../../../preludes/self.journal` for:
   - Account type definitions (assets, liabilities, equity, expenses, revenues)
   - Commodity format specifications
   - Payee definitions
   - Tag definitions
   - Account hierarchy organization

## Alternatives Tracking

Some years have `self.alternatives.journal` files for tracking alternative scenarios or investments:

- **Purpose**: Separate from primary `self.journal` files to distinguish liquid assets from illiquid/experimental holdings
- **Example years**: 2022–2026 have both `self.journal` and `self.alternatives.journal`
- **Structure**: Parallel include hierarchy to main journals
- **See also**: [Alternatives Journal Tracking](./alternatives-journal.instructions.md) for detailed explanation

## File Organization Patterns

### Monthly Journal Pattern

- **Location**: `ledger/YYYY/YYYY-MM/self.journal`
- **Naming**: Year and month are both 4-digit and 2-digit zero-padded numbers
- **Content**: Opening balances → transactions → closing balances
- **Pattern used by scripts**: Glob pattern `**/*[0-9]{4}-[0-9]{2}/*.journal`

### Include Statement Format

```hledger
include ../../../preludes/self.journal
```

Always use relative paths with consistent depth (`../` repeated 3 times for monthly journals).

## Key Design Decisions

1. **Hierarchical organization**: Yearly and monthly grouping provides logical separation while maintaining central prelude management
2. **Shared preludes**: Single source of truth for account/commodity definitions reduces duplication and ensures consistency
3. **Separate alternatives**: Distinct journal stream allows parallel tracking without mixing concepts
4. **Glob pattern discovery**: Scripts automatically find all monthly journals regardless of year, enabling future-proof operations

## Script Usage

See `.github/instructions/developer-workflows.instructions.md` for the canonical script usage policy. In short: prefer `pnpm run <script>` from the repository root; if no pnpm wrapper exists, run Python scripts with `cwd=scripts/` to avoid include and discovery errors.
