"""Tests for envault.crypto encryption/decryption module."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_decrypt_roundtrip():
    token = encrypt(PLAINTEXT, PASSWORD)
    recovered = decrypt(token, PASSWORD)
    assert recovered == PLAINTEXT


def test_encrypt_produces_different_ciphertexts():
    """Each call should produce a unique ciphertext due to random salt/nonce."""
    token1 = encrypt(PLAINTEXT, PASSWORD)
    token2 = encrypt(PLAINTEXT, PASSWORD)
    assert token1 != token2


def test_decrypt_with_wrong_password_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(Exception):
        decrypt(token, "wrong-password")


def test_encrypt_empty_string():
    token = encrypt("", PASSWORD)
    assert decrypt(token, PASSWORD) == ""


def test_encrypt_multiline_env():
    multiline = "KEY1=val1\nKEY2=val2\nSECRET=abc123"
    token = encrypt(multiline, PASSWORD)
    assert decrypt(token, PASSWORD) == multiline


def test_decrypt_tampered_payload_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    # Flip a character in the middle of the token
    mid = len(token) // 2
    tampered = token[:mid] + ("A" if token[mid] != "A" else "B") + token[mid + 1:]
    with pytest.raises(Exception):
        decrypt(tampered, PASSWORD)
