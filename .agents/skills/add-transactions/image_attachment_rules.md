# Image and Attachment Handling Rules

This file contains all rules and best practices for handling images and attachments during transaction entry. Use this file whenever you are transcribing from receipts, photos, or other attachments.

**Examples:** See `./examples.md` for examples of attachment-related workflows and placeholder transactions.

## Image/Attachment Checklist

- Each attachment must be related to at least one transaction (some images may represent multiple transactions, and some transactions may have multiple images).
- After processing all attachments, determine if any attachment has not been referenced in any transaction. If so, ask the user for clarification on that attachment.
- For any image with unclear merchant/amount/payment method, add a pending transaction (`!`) with the attachment filename in a comment and an explicit `0.00` or the known amount, then follow up with the user to confirm and replace the placeholder.
- Do NOT use the filename as the transaction ID.
- When inserting placeholders, include the exact attachment filename in the transaction comment (not the header ID) so automation or future reviewers can match image → journal easily.

## Related Files

- [SKILL.md](./SKILL.md)
