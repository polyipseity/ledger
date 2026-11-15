---
name: Security Practices
description: Guidance for handling confidential data in this personal accounting system, including private.yaml encryption/decryption and UUID usage for privacy.
applyTo: "**"
---

# Security practices

**The agent never encrypts, never decrypts, and never commits confidential data.** Opening `private.yaml`, re-encrypting it, and the commit that carries `private.yaml.gpg` are the owner's actions. The agent's part is the placeholder it can name without the value, and the question it asks when it needs more.

## Which file holds the secrets

The [private.yaml.gpg](../../private.yaml.gpg) file carries the mapping of UUIDs to confidential strings, encrypted and tracked. It decrypts to `private.yaml`, which sits beside it in the owner's working copy only:

- **Account numbers**: real bank account numbers and card numbers
- **Personal names**: full names of individuals, family members
- **Locations**: home address, workplace, sensitive locations
- **Institution names**: real names of banks, insurance companies, employers
- **Contact information**: phone numbers, email addresses

Only the ciphertext is committed. `.gitignore` excludes `private.yaml` and keeps excluding it; the plaintext is the owner's alone, and a copy of it in the working tree is never staged, quoted, or attached to a report.

## What the journals carry

Journals and docs name a payee or an account by UUID placeholder, so an entry reads the same whether or not the reader can resolve it:

```hledger
2025-01-19 Generic Cafe
    expenses:food and drinks:dining       50.00 HKD
    assets:banks:<bank-uuid>             -50.00 HKD
```

The `<bank-uuid>` placeholder stands for a UUID whose pair sits in `private.yaml`. A confidential value never enters a journal, a document, a commit message, or a test fixture; what enters is the UUID, and `.agents/skills/add-payee/SKILL.md` declares the prelude line that carries it.

- **One entity keeps one UUID.** Reuse the pair a prelude already carries instead of minting a second one, so the ledger's history resolves consistently.
- **A new confidential entity needs a new UUID**, and that pair is the owner's to add, because adding it means decrypting and re-encrypting.

## A mapping change is the owner's

When an entry needs a name the mapping does not hold, the agent stops and asks, naming what the owner has to add: the confidential string, the UUID the entry will carry, and where the pair belongs. The owner decrypts, adds the pair, re-encrypts, and commits the ciphertext. The agent never edits `private.yaml`, never runs a decrypt or encrypt step, and never commits the mapping.

`.agents/skills/add-payee/SKILL.md` is where that request is made from, and it holds the declaration the prelude then needs.

## When the agent stops and asks

- A printed name looks confidential — a person, an institution, an account or card number — and `private.yaml` is the only place it could be resolved.
- A UUID in a prelude or a journal resolves to no pair the agent can see, and the task needs the name rather than the placeholder.
- A mapping change is required, since the owner adds the pair and the agent never does.
- A commit would include `private.yaml`, or a file whose content came out of it.

What the agent may read instead is always at hand: the UUID a journal already carries, or the placeholder a prelude declares. Neither is a secret, and neither is decrypted.

## Sharing

A journal handed outside the repository keeps its UUIDs and loses nothing: the recipient can read every entry and cannot resolve a name. Say so when handing one over, and never attach `private.yaml`, a decrypted copy, or a screenshot of either.

## Recovery and diagnosis

- **A lost key or passphrase** makes every mapping in `private.yaml.gpg` unreadable. The journals stay valid and their UUIDs simply stop resolving. Recovery is the owner's: restore the key from their backup, or rebuild the pairs and encrypt a new file.
- **`gpg: decryption failed: No secret key`** means the owner's private key is not in this keyring. No agent-side fix exists; `.agents/instructions/dependencies.instructions.md` holds the tool surface, so report the message and stop.
- **A pair that resolves to nothing** is a question for the owner, never a value to invent or approximate.
