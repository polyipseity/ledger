---
name: Architecture & File Organization
description: "Use when placing a journal, an include, or a prelude declaration: the tree, the include chain, and the monthly file pattern."
---


# Architecture & File Organization

## Hierarchical journal structure

The ledger is one tree, with every shared definition inherited from the preludes.

- **Entry point**: [ledger/index.journal](../../ledger/index.journal) includes `self.journal` and `self.alternatives.journal`
- **Year level**: [ledger/YYYY/self.journal](../../ledger/2024/self.journal) includes the year's monthly journals
- **Month level**: [ledger/YYYY/YYYY-MM/self.journal](../../ledger/2024/2024-01/self.journal) holds the transactions, and nothing above it does
- **Preludes**: [preludes/index.journal](../../preludes/index.journal) is included by both streams and declares the structural accounts, the commodities, and the tags every entry may use; each stream's own prelude declares its accounts, payees, and commodities, and `preludes/*.journal` is the single source for all of them

Each monthly journal starts with an `include` of its own stream's prelude, `../../../preludes/self.journal` or `../../../preludes/self.alternatives.journal`, to inherit those definitions.

### Directory example

```txt
ledger/
  index.journal              # Root: includes self.alternatives.journal, self.journal
  self.journal               # Includes 2024/self.journal, 2025/self.journal, ...
  self.alternatives.journal  # Includes 2024/self.alternatives.journal, ...
  2024/
    self.journal             # Includes 2024-01/self.journal, 2024-02/self.journal, ...
    self.alternatives.journal
    2024-01/
      self.journal           # Monthly transactions with opening/closing balances
    2024-02/
      self.journal
    ...
  2025/
    ...

preludes/
  index.journal              # Includes self.alternatives.journal, self.journal
  self.journal               # Global account, commodity, payee, tag definitions
  self.alternatives.journal  # Alternative scenario commodity definitions
```

## Include hierarchy

1. **Root level** (`ledger/index.journal`): includes the two journal streams
2. **Yearly level** (`ledger/YYYY/self.journal`): organizes the year's months
3. **Monthly level** (`ledger/YYYY/YYYY-MM/self.journal`): the only level holding transactions
4. **Prelude inclusion**: every monthly journal includes its own stream's prelude — `../../../preludes/self.journal`, or `../../../preludes/self.alternatives.journal` from the illiquid stream — for the account, commodity, payee, and tag declarations

## File organization

- **Location**: a transaction goes in `ledger/YYYY/YYYY-MM/<name>.journal`, named for its own date's month and year — the tree above is the whole rule, and a year file takes no transaction.
- **Naming**: the year is four digits and the month two, zero-padded.
- **Content**: the month's opening balances, then its transactions, then its closing balances; the two boundary blocks are generated rather than written (`../skills/migrate/SKILL.md`).
- **Include statement**: `include ../../../preludes/self.journal`, with the relative depth the monthly location fixes and the stream's own prelude named for an illiquid month.

## The alternatives stream

`self.journal` and `self.alternatives.journal` are parallel trees with parallel includes, and which one a holding belongs to is `alternatives-journal.instructions.md`'s rule.

## Script discovery

See `.agents/instructions/developer-workflows.instructions.md` for the canonical script usage policy. In short: `bun run <script>` from the repository root, or a Python module as `-m scripts.<mod>` from that same root, because the package imports relatively and any other working directory fails before it finds an include.
