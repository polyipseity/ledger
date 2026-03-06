# Entity Registration Rules (Payee/Account)

This file contains all rules and best practices for registering new payees and accounts in the ledger system. Use this file whenever you need to add a new merchant, counterparty, or account.

**Examples:** See `./examples.md` for examples of entity and UUID registration.

## Payee Registration

- Keep payee declarations in `preludes/*.journal` alphabetized; insert any new payee in order.
- Add new payees to `preludes/self.journal` as needed.

## Account Registration

- Add new accounts as needed, using the correct account hierarchy and naming conventions.
- Example:
  - `account assets:banks:<new-bank-uuid>:Currency`
  - `account liabilities:loans:friends:<new-friend-uuid>`

## Confidential Details

- For confidential details, add UUID mapping to `private.yaml` and re-encrypt.
- Example:

  ```yaml
  <new-person-uuid>: "John Doe"
  <new-bank-uuid>: "Bank XYZ Account 123-456"
  ```

- Then run: `python -m encrypt`

## Related Files

- [preludes/*.journal](../../../preludes/)
- [private.yaml](../../../private.yaml)
- [SKILL.md](./SKILL.md)
