"""Tests for envault.share — secure share token creation and redemption."""

import time

import pytest

from envault.share import (
    ShareError,
    create_share_token,
    redeem_share_token,
    token_fingerprint,
)

SECRETS = {"DB_HOST": "localhost", "API_KEY": "s3cr3t"}
PASSWORD = "hunter2"


def test_create_share_token_returns_string():
    token = create_share_token(SECRETS, PASSWORD)
    assert isinstance(token, str)
    assert len(token) > 0


def test_redeem_share_token_roundtrip():
    token = create_share_token(SECRETS, PASSWORD)
    result = redeem_share_token(token, PASSWORD)
    assert result == SECRETS


def test_redeem_wrong_password_raises():
    token = create_share_token(SECRETS, PASSWORD)
    with pytest.raises(ShareError):
        redeem_share_token(token, "wrongpassword")


def test_redeem_expired_token_raises():
    token = create_share_token(SECRETS, PASSWORD, ttl=-1)
    with pytest.raises(ShareError, match="expired"):
        redeem_share_token(token, PASSWORD)


def test_redeem_malformed_token_raises():
    with pytest.raises(ShareError):
        redeem_share_token("not-a-valid-token!!", PASSWORD)


def test_create_share_token_with_label():
    token = create_share_token(SECRETS, PASSWORD, label="staging creds")
    result = redeem_share_token(token, PASSWORD)
    assert result == SECRETS


def test_create_share_token_empty_secrets():
    token = create_share_token({}, PASSWORD)
    result = redeem_share_token(token, PASSWORD)
    assert result == {}


def test_two_tokens_differ_for_same_input():
    t1 = create_share_token(SECRETS, PASSWORD)
    t2 = create_share_token(SECRETS, PASSWORD)
    # Encryption is nonce-based, so tokens should differ
    assert t1 != t2


def test_token_fingerprint_is_12_chars():
    token = create_share_token(SECRETS, PASSWORD)
    fp = token_fingerprint(token)
    assert len(fp) == 12
    assert fp.isalnum()


def test_token_fingerprint_is_deterministic():
    token = create_share_token(SECRETS, PASSWORD)
    assert token_fingerprint(token) == token_fingerprint(token)
