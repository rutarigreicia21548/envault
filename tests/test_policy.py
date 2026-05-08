"""Tests for envault.policy."""

import pytest
from pathlib import Path

from envault.policy import (
    Policy,
    PolicyError,
    check_env,
    enforce,
    load_policy,
    save_policy,
)


@pytest.fixture()
def storage_dir(tmp_path: Path) -> Path:
    return tmp_path / "storage"


# ---------------------------------------------------------------------------
# Policy.to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

def test_policy_roundtrip():
    p = Policy(allowed_keys=["FOO", "BAR"], denied_keys=["SECRET"], read_only=True)
    assert Policy.from_dict(p.to_dict()) == p


def test_policy_defaults():
    p = Policy()
    assert p.allowed_keys == []
    assert p.denied_keys == []
    assert p.read_only is False
    assert p.require_tags == {}


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(storage_dir):
    policy = Policy(allowed_keys=["DB_URL"], read_only=False)
    save_policy("myproject", policy, storage_dir)
    loaded = load_policy("myproject", storage_dir)
    assert loaded == policy


def test_load_missing_project_returns_none(storage_dir):
    assert load_policy("nonexistent", storage_dir) is None


# ---------------------------------------------------------------------------
# enforce
# ---------------------------------------------------------------------------

def test_enforce_allowed_key_passes():
    policy = Policy(allowed_keys=["DB_URL"])
    enforce(policy, "DB_URL")  # should not raise


def test_enforce_denied_key_raises():
    policy = Policy(denied_keys=["ADMIN_TOKEN"])
    with pytest.raises(PolicyError, match="explicitly denied"):
        enforce(policy, "ADMIN_TOKEN")


def test_enforce_key_not_in_allowlist_raises():
    policy = Policy(allowed_keys=["DB_URL"])
    with pytest.raises(PolicyError, match="not in the allowed-keys list"):
        enforce(policy, "REDIS_URL")


def test_enforce_empty_allowlist_permits_any_key():
    policy = Policy()  # no restrictions
    enforce(policy, "ANYTHING")  # should not raise


def test_enforce_read_only_write_raises():
    policy = Policy(read_only=True)
    with pytest.raises(PolicyError, match="forbids write"):
        enforce(policy, "FOO", write=True)


def test_enforce_read_only_read_passes():
    policy = Policy(read_only=True)
    enforce(policy, "FOO", write=False)  # should not raise


# ---------------------------------------------------------------------------
# check_env
# ---------------------------------------------------------------------------

def test_check_env_no_violations():
    policy = Policy(allowed_keys=["A", "B"])
    violations = check_env(policy, {"A": "1", "B": "2"})
    assert violations == []


def test_check_env_returns_all_violations():
    policy = Policy(denied_keys=["X", "Y"])
    violations = check_env(policy, {"X": "1", "Y": "2", "Z": "3"})
    assert len(violations) == 2


def test_check_env_write_read_only():
    policy = Policy(read_only=True)
    violations = check_env(policy, {"KEY": "val"}, write=True)
    assert len(violations) == 1
    assert "forbids write" in violations[0]
