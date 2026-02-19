# Platform Transaction & Payout Rules (Stripe, PayPal, etc.)

## Overview & Mandatory Best Practices

This file extends the add-transactions skill with generalized rules for transcribing both platform transactions (e.g., donations, sales, payments) and platform payouts (transfers to bank accounts) for digital payment platforms such as Stripe, PayPal, Square, Alipay, etc.

**All rules below are subject to these mandatory best practices:**

- **Net Amount Posting:** Always post the net amount (after all fees) to the digital payment asset account (e.g., Stripe, PayPal, etc.). Never use the gross payment amount for this posting. The net amount is the actual value credited to your platform balance and is essential for balanced transactions and accurate asset tracking.
- **Second Precision Time Tags:** Record full HH:MM:SS timestamps when available; see `.github/instructions/transaction-format.instructions.md` for ordering and timezone rules.

Any deviation from these rules will result in unbalanced or non-compliant journal entries.

**Reminder:** Always use the full path `ledger/[year]/[year]-[month]/[name].journal` when searching for or referring to journal files. Never omit the `ledger/` prefix.

## 1. Platform Transaction Pattern

### 1.1 Input Fields (from PDF/CSV/API)

- **Transaction date/time**: PDF files often include a date/time for PDF generation—this is IRRELEVANT and must be ignored. Always use the actual transaction date/time. If unclear, ask the user for clarification!
- **Transaction IDs**: Platform, internal, reference
- **Payee/Donor**: Masked for privacy by replacing all characters except the '@' and the dot preceding the top-level domain (TLD) in email addresses with '*'. The number of asterisks in each segment (local part and domain) must exactly match the number of characters in the unmasked email. Only the dot and the TLD (e.g., ".com") are left unmasked. The agent must count the number of characters in each segment very carefully and mask with the exact number of asterisks, preserving the positions of '@' and the final dot before the TLD.
  - For names or other identifiers (single or multiple words):
    - Preserve spaces.
    - Only the first character of the first word and the last character of the last word are unmasked.
    - All other characters (including those in middle words and within single words) are replaced with asterisks.
  - **Example (email masking):**
    - Input: `john.doe@example.com` (local: 8, domain: 7, TLD: 3)
    - Masked: `********@*******.com` (8 asterisks for 'john.doe', 7 for 'example', preserving '@' and '.com')
  - **Example (name masking, including single words):**
    - Input: `Jane Doe Smith`
    - Masked: `J**e *** *****h`
- **Amount(s) and currency**
- **Platform fees**: Itemized
- **Net amount**
- **Exchange rate**: If multi-currency
- **Platform account**: UUID
- **Activity/type**: Donation, sale, etc.

### 1.2 Journal Mapping

- **Date/Time:** Use the actual transaction date/time, not the PDF generation time. Always record the time tag with second precision if available. If the correct date/time is unclear, always ask the user for clarification.
- **IDs:** Include all available IDs in parentheses at the start of the payee line.
- **Payee/Donor:** Mask or obfuscate for privacy; never use real emails or account numbers. Register in preludes if missing.
- **Amounts:**
  - **Credit the platform asset account (UUID) with the net amount only. Never use the gross payment amount for this posting.**
  - Debit conversion/equity accounts for multi-currency, using the `rate` tag.
  - Split platform and service fees into separate expense accounts.
  - Credit the revenue account for the gross amount (negative posting).
- **Accounts:** Use UUIDs for privacy and traceability.
- **Tags:**
  - Always include `activity`, `time` (with second precision), `timezone`, and `rate` (if applicable).
- **Status Marker:**
  - For platform transactions (non-payout):
    - Use `!` for pending transactions that have not yet been paid out (funds not transferred to bank).
    - Use `*` for confirmed transactions that have been paid out (funds transferred to bank).
  - For payout transactions, do not use status markers.

**Examples:** See `./examples.md` for canonical platform transaction and payout worked examples (masked donors, net posting rules, and payout assertions).

## 2. Platform Payout Pattern

### 2.1 Input Fields (from PDF/CSV/API)

- **Payout date/time**
- **Payout IDs**: Platform, bank, reference
- **Amount and currency**
- **Platform account**: UUID
- **Bank account**: UUID
- **Status**: Only completed/paid

### 2.2 Journal Mapping

- **Date/Time:** Use the payout date/time as the transaction date, and always add `time` and `timezone` tags with second precision if available.
- **IDs:** Include payout IDs (`po_...`) and other platform-provided identifiers in parentheses at the start of the payee line. **Never include bank account identifiers (`ba_...`) in the payee line.** Do not include payout trace IDs (such as Stripe trace codes) in the payee line.
- **Payee:** The payee should always be the platform name (e.g., 'Stripe', 'PayPal'), not a transaction type (e.g., 'Stripe payout', 'PayPal withdrawal'). Never include the transaction type in the payee field.
- **Amounts:**
  - Credit the bank asset account (UUID) with the payout amount.
  - Debit the platform asset account (UUID) with the same amount.
  - Assert the platform account balance to zero after payout (`= 0.00 <currency>`).
- **Accounts:** Use UUIDs for both platform and bank accounts.
- **Tags:** Always include only the required tags: `activity: payout`, `time` (with second precision), and `timezone`. **Do not include extraneous tags such as email, description, or other metadata unless explicitly required by the project conventions.**
  - Use `activity: payout` for platform payouts (preferred over `transfer`) to make the transaction intent explicit.
- **Status:** Only journal completed/paid payouts.

### 2.3 Example: Platform Payout (Randomized, Masked)

```hledger
2026-01-20 (HD01234567891011, FRN20260120PAYC0123456789012, po_1Z9Y8X7W6V5U4T3S2R1Q) Stripe  ; activity: payout, time: 15:10:10, timezone: UTC+08:00
  assets:banks:99999999-8888-7777-6666-555555555555:HKD savings       156.00 HKD
  assets:digital:Stripe:11111111-2222-3333-4444-555555555555        -156.00 HKD = 0.00 HKD
```

**Note:** Do not include payout trace IDs (such as Stripe trace codes) in the payee line. Only use payout IDs and other relevant identifiers.

## 3. Generalization for Other Platforms

- Apply the same mapping logic for any digital payment platform.
- Always use UUIDs for privacy.
- Always itemize fees and use specific accounts.
- Always include all available reference IDs for traceability.
- Always assert balances where appropriate.
- Only journal completed/verified transactions and payouts.
- **Always post net amounts to platform asset accounts and use second precision for time tags if available.**

## 4. Ambiguities & Clarifications

- If more than three IDs are present, include all unless user requests otherwise.
- If a new fee type appears, create a new expense account.
- If only one currency is present, omit conversion accounts and rate tag.
- If additional tags (e.g., project, campaign) are present, include them as appropriate.
- If second precision is not available, use the highest available precision for time tags.

## 5. References

- See main SKILL.md for general transaction rules.
- See mapping files for payee and ID mapping.
- See currency conversion theme for multi-currency details.
- See [add-payee rules](./add-payee.md) for payee registration.

## 6. Continuous Updates

This file is continuously updated as new platforms and patterns are encountered. Always cross-reference with user feedback and update as needed.
