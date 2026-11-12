---
name: Alternatives Journal Tracking
description: "Use when deciding whether a holding belongs in the illiquid alternatives stream rather than the main journal."
applyTo: "ledger/**/self.alternatives.journal"
---

# Alternatives journal

`ledger/index.journal` includes two streams: `self.journal` for what converts into money at a known rate, and `self.alternatives.journal` for what does not. A transaction sits in the stream its accounts belong to, and `../skills/ingest/SKILL.md` applies the line when it places an entry.

## What separates the streams

- **The main stream is liquid.** Banks, cash, cards, wallets, reward points with a redemption rate, loans with a repayment expectation, and objects with a salvage value: every holding there has a market value or a redemption mechanism, and it is the stream a spending or income entry belongs to.
- **The alternatives stream is illiquid.** Cryptocurrency, a locked-in or non-transferable investment, a share in a private company, a membership point with no redemption mechanism, a digital collectible, and any "what-if" position: no published price, and no way to convert it into money that the ledger's own horizon can rely on.
- The separation keeps net worth honest: one stream is reachable, the other is a position.

## Which accounts belong there

- The preludes decide. A holding whose accounts `preludes/self.alternatives.journal` declares goes in that stream, and one whose accounts only `preludes/self.journal` declares goes in the main one; `../reference/account-hierarchy.md` describes the accounts.
- The alternatives prelude carries its own commodity declarations (`GREEN$`, the recyclable units such as `_PAP` and `_MET`, and its own point commodities), so a holding denominated in one of them cannot be booked in the main stream.
- A holding's accounts also select its keys: `collect`, `compute`, and `recycle` are declared by the alternatives prelude alone, and `../skills/ingest-tags/SKILL.md` owns which keys an entry takes.
- A movement between the streams crosses on `equity:external:self.alternatives`, negative in the stream it leaves and positive in the stream it enters, so neither stream's total silently absorbs the other's holding.

## Boundaries are per journal filename

`self.journal` and `self.alternatives.journal` are separate families with separate chains: each month's closing and the next month's opening are generated within one filename, and a family that skips a month keeps its chain across the gap. `bun run clopen <YYYY-MM> --only <filename>` restricts a run to one family, which is how a dormant family stays dormant; `../skills/migrate/SKILL.md` holds the procedure and its repair.

## Privacy

A holding is named by its account, never by a wallet address, an exchange account number, or a transaction hash. A holding that would otherwise be named by one takes a UUID placeholder whose pair stays in `private.yaml`, exactly as `security.instructions.md` requires of any confidential name, and an agent that needs one resolved stops and asks.
