# Secure Secret Sharing

The `share` feature lets you securely hand off secrets to a teammate without
exposing raw values. Secrets are encrypted into a portable **share token** that
can be transmitted over any channel (Slack, email, etc.) and redeemed once the
recipient has the shared password.

## How it works

1. **Sender** encrypts vault secrets into a time-limited token.
2. **Recipient** decrypts the token using the agreed-upon password and imports
   the secrets into their own vault project.

Tokens are encrypted with the same AES-GCM scheme used by the vault itself
(see `envault/crypto.py`). Each token embeds an expiry timestamp; expired tokens
are rejected on redemption.

## CLI usage

### Create a share token

```bash
envault share create --project myapp --ttl 7200 --label "staging handoff"
```

You will be prompted for the vault password. The token is printed to stdout —
copy and send it to your teammate along with the password via a separate channel.

### Redeem a share token

```bash
envault share redeem <TOKEN> --project myapp
```

You will be prompted for the token password and your local vault password.
On success the decrypted secrets are pushed into the specified project.

## Python API

```python
from envault.share import create_share_token, redeem_share_token

token = create_share_token({"API_KEY": "secret"}, password="hunter2", ttl=3600)
secrets = redeem_share_token(token, password="hunter2")
```

## Security notes

- Choose a **strong, unique** password for each share; never reuse your vault
  master password.
- Set a short TTL for sensitive secrets.
- Tokens are single-use by convention — revoke by rotating the underlying
  secret after the recipient has imported it.
