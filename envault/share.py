"""Secure sharing of secrets between team members via signed share tokens."""

import base64
import hashlib
import json
import time
from typing import Optional

from envault.crypto import encrypt, decrypt

SHARE_VERSION = 1
DEFAULT_TTL = 3600  # seconds


class ShareError(Exception):
    """Raised when share token creation or redemption fails."""


def create_share_token(
    secrets: dict[str, str],
    password: str,
    ttl: int = DEFAULT_TTL,
    label: Optional[str] = None,
) -> str:
    """Encrypt secrets into a portable share token string.

    Args:
        secrets: Key/value pairs to share.
        password: Password used to encrypt the payload.
        ttl: Seconds until the token expires (default 1 hour).
        label: Optional human-readable label for the share.

    Returns:
        A base64-encoded share token string.
    """
    payload = {
        "version": SHARE_VERSION,
        "created_at": time.time(),
        "expires_at": time.time() + ttl,
        "label": label or "",
        "secrets": secrets,
    }
    raw = json.dumps(payload)
    ciphertext = encrypt(raw, password)
    token_bytes = ciphertext.encode()
    return base64.urlsafe_b64encode(token_bytes).decode()


def redeem_share_token(token: str, password: str) -> dict[str, str]:
    """Decrypt and validate a share token, returning the embedded secrets.

    Args:
        token: A base64-encoded share token string.
        password: Password used to decrypt the payload.

    Returns:
        The decrypted key/value secret pairs.

    Raises:
        ShareError: If the token is expired, malformed, or the password is wrong.
    """
    try:
        ciphertext = base64.urlsafe_b64decode(token.encode()).decode()
        raw = decrypt(ciphertext, password)
        payload = json.loads(raw)
    except Exception as exc:
        raise ShareError(f"Failed to decode share token: {exc}") from exc

    if payload.get("version") != SHARE_VERSION:
        raise ShareError("Unsupported share token version.")

    if time.time() > payload["expires_at"]:
        raise ShareError("Share token has expired.")

    return payload["secrets"]


def token_fingerprint(token: str) -> str:
    """Return a short fingerprint (first 12 hex chars of SHA-256) for a token."""
    digest = hashlib.sha256(token.encode()).hexdigest()
    return digest[:12]
