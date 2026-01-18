---
name: Security Practices
description: Guidance for handling confidential data in this personal accounting system, including private.yaml encryption/decryption and UUID usage for privacy.
applyTo: "private.yaml*"
---

# Security Practices

Guidance for handling confidential data in this personal accounting system.

## private.yaml File Management

### Purpose and Structure

The [private.yaml](../../private.yaml) file contains a mapping of UUIDs to confidential strings:
- **Account numbers**: Real bank account numbers, card numbers
- **Personal names**: Full names of individuals, family members
- **Locations**: Home address, workplace, sensitive locations
- **Institution names**: Real names of banks, insurance companies, employers
- **Contact information**: Phone numbers, email addresses

This separation allows journals to remain readable and shareable (with UUIDs as placeholders) while keeping sensitive information encrypted.

### Security Requirements

**CRITICAL: Only commit encrypted `private.yaml.gpg`**

- Unencrypted `private.yaml` must never be committed or pushed
- Ensure `.gitignore` contains `private.yaml` (but not `private.yaml.gpg`)
- Never inline confidential values in journals, code, or commits—use UUID placeholders only
- Always encrypt immediately after editing `private.yaml`

## Encryption Workflow

### Encrypting Private Data

After editing `private.yaml` locally:

```powershell
python -m encrypt
```

Or use the equivalent script:
```powershell
.\scripts\encrypt.sh       # Linux/macOS
.\scripts\encrypt.bat      # Windows
```

**What happens:**
1. Script reads the unencrypted `private.yaml`
2. Uses GPG to encrypt it to `private.yaml.gpg`
3. Overwrites original with encrypted version
4. Safe to commit `private.yaml.gpg` to repository

**Requirements:**
- GPG installed and in PATH
- Non-password-protected GPG public key available
- Recipient key specified in script configuration

### Decrypting Private Data

To edit confidential mappings:

```powershell
python -m decrypt
```

Or use the equivalent script:
```powershell
.\scripts\decrypt.sh       # Linux/macOS
.\scripts\decrypt.bat      # Windows
```

**What happens:**
1. Script reads `private.yaml.gpg`
2. Prompts for GPG key password
3. Decrypts and overwrites `private.yaml` locally
4. **WARNING**: Leaves decrypted file on disk until encrypted again

**Requirements:**
- GPG installed and in PATH
- Password-protected GPG private key available
- Correct password for private key

### Encryption/Decryption Workflow Example

```powershell
# 1. Decrypt to edit
python -m decrypt
# [Prompted for password]

# 2. Edit private.yaml with your editor
# [Add new UUID mappings or update existing ones]

# 3. Encrypt immediately after editing
python -m encrypt

# 4. Verify encrypted version
ls -la private.yaml*       # Should show both files
git status                 # Should show only private.yaml.gpg as modified

# 5. Commit the encrypted version
git add private.yaml.gpg
git commit -m "Update confidential data mappings"
```

## UUID Usage

### How UUIDs Replace Confidential Data

Throughout journals, sensitive information is replaced with UUIDs:

```hledger
# Journal entry (public, safe to share)
2025-01-19 Generic Cafe
    expenses:food and drinks:dining    50.00 HKD
    assets:banks:<bank-uuid>          -50.00 HKD
```

The `<bank-uuid>` placeholder is an actual UUID that maps to:
```yaml
<bank-uuid>: "Account 123-456789 at Bank XYZ"
```

**Stored in**: `private.yaml` (encrypted as `private.yaml.gpg`)

### UUID Benefits

1. **Readable journals**: UUIDs are concise and consistent
2. **Privacy**: Can share journals without exposing account details
3. **Security**: Confidential mappings isolated in encrypted file
4. **Flexibility**: Can change confidential details without re-editing all journals
5. **Traceability**: UUIDs maintain referential integrity across time

### UUID Consistency

- **Payees**: Use same UUID for repeated counterparties
- **Accounts**: Use same UUID for same account across multiple journals
- **Conventions**: See [preludes/self.journal](../../preludes/self.journal) for existing UUID definitions
- **New UUIDs**: Generate new UUID only for new entities, reuse existing ones otherwise

## Best Practices

### For Editing Confidential Data

1. **Decrypt minimally**: Only decrypt when actively editing
2. **Encrypt immediately**: After finishing edits, encrypt right away
3. **Verify encryption**: Confirm `private.yaml.gpg` changed before committing
4. **Secure key**: Keep GPG private key password secure and memorized
5. **Test decryption**: Periodically verify you can decrypt to catch key issues early
6. **Backup key**: Keep secure backup of GPG private key (separate from repository)

### For Sharing Journals

1. **Only share journals with UUIDs**: Never share with decrypted private.yaml
2. **Share public-safe copies**: Create journals with UUIDs intact
3. **Note limitations**: When sharing, document that recipient cannot resolve UUIDs
4. **Version control**: Always commit encrypted `private.yaml.gpg`, never unencrypted version

### For Repository Maintenance

1. **Verify .gitignore**: Confirm `private.yaml` is ignored, `private.yaml.gpg` is tracked
2. **Check git history**: Search for accidental `private.yaml` commits:
   ```powershell
   git log --all --full-history -- private.yaml
   ```
3. **Monitor changes**: Before committing, verify only `private.yaml.gpg` appears in `git status`
4. **Encryption verification**: Confirm `private.yaml.gpg` is binary and reasonably sized for encryption overhead

## Recovery and Troubleshooting

### Lost Decryption Access

If you lose the GPG private key or password:
1. All confidential mappings in `private.yaml.gpg` become inaccessible
2. Journals with UUIDs remain valid but unmapped
3. Recovery requires either:
   - Finding the lost key/password
   - Re-creating mappings in a new `private.yaml` and encrypting
   - Reverting to an earlier commit with accessible encryption

**Prevention**: Maintain secure backup of private key and password in separate location.

### Encryption Errors

If `python -m encrypt` fails:
1. Verify GPG is installed: `gpg --version`
2. Check public key exists: `gpg --list-keys`
3. Verify file permissions: `ls -la private.yaml`
4. Check disk space

If `python -m decrypt` fails:
1. Verify GPG is installed: `gpg --version`
2. Check private key exists: `gpg --list-secret-keys`
3. Ensure `private.yaml.gpg` exists and is readable
4. Verify password is correct
