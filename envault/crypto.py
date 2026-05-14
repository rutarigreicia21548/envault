"""AES-GCM encryption/decryption utilities for envault secrets."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256-bit
MIN_PAYLOAD_SIZE = SALT_SIZE + NONCE_SIZE + 16  # 16-byte GCM auth tag minimum


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using Scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=2**14, r=8, p=1)
    return kdf.derive(password.encode())


def encrypt(plaintext: str, password: str) -> str:
    """
    Encrypt plaintext with a password.
    Returns a base64-encoded string: salt + nonce + ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt(encoded: str, password: str) -> str:
    """
    Decrypt a base64-encoded payload produced by `encrypt`.
    Returns the original plaintext string.

    Raises:
        ValueError: If the payload is malformed or the password is incorrect.
    """
    try:
        payload = base64.b64decode(encoded.encode())
    except Exception as exc:
        raise ValueError("Invalid encrypted payload: not valid base64.") from exc

    if len(payload) < MIN_PAYLOAD_SIZE:
        raise ValueError(
            f"Invalid encrypted payload: too short ({len(payload)} bytes)."
        )

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise ValueError("Decryption failed: incorrect password or corrupted data.") from exc

    return plaintext.decode()
