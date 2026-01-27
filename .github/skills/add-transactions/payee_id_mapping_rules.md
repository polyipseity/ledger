# Payee and ID Mapping Rules

This file contains all rules and best practices for payee normalization, payee mapping, and ID extraction/order for transaction entry. Use this file whenever you need to resolve payee names, apply UUIDs, or extract/normalize transaction IDs.

## Payee Mapping Rules

- Always check `private.yaml` for payee/counterparty mapping. If a UUID is present, use the UUID as the payee.
- Use canonical payee names from `payee_mappings.yml` if no UUID is present.
- Never use masked/partial names from receipts. Do not add region/location unless it is part of the canonical payee name.
- Do NOT add clearly-invalid tokens (IDs, kiosk labels, or numeric prefixes) as keys in `payee_mappings.yml`.
- Do NOT include identity mappings (e.g. "McDonald's": "McDonald's").
- Strip incidental location or terminal codes in parentheses when deciding the canonical payee key.
- Keep `payee_mappings.yml` minimal, sorted, and deduplicated.

## ID Mapping Rules

- Always check `id_mappings.yml` for the correct ID order and required fields before writing IDs.
- Place all transaction IDs in parentheses before the payee name, in the order specified by `id_mappings.yml`.
- If an expected ID is missing, use `?` as a placeholder.
- Never use tags for IDs.
- When proposing a new id mapping, include a one-line example and a brief regex hint; persist only after user confirmation.
- Only write or update `id_mappings.yml` after explicit user approval.

> **Note:** All payee-specific ID mapping rules must be defined only in `id_mappings.yml`. Do not document specific ID mapping examples or regex in this markdown file. Refer to `id_mappings.yml` for authoritative rules.

## Related Files

- [payee_mappings.yml](./payee_mappings.yml)
- [id_mappings.yml](./id_mappings.yml)
- [SKILL.md](./SKILL.md)
