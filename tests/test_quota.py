"""Tests for envault.quota."""

from __future__ import annotations

import pytest

from envault.quota import (
    QuotaError,
    check_quota,
    clear_quota,
    get_quota,
    set_quota,
    DEFAULT_MAX_KEYS,
    DEFAULT_MAX_BYTES,
)


@pytest.fixture()
def project_dir(tmp_path):
    d = tmp_path / "myproject"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# set_quota / get_quota
# ---------------------------------------------------------------------------

def test_set_and_get_quota_roundtrip(project_dir):
    set_quota(project_dir, max_keys=50, max_bytes=512)
    quota = get_quota(project_dir)
    assert quota == {"max_keys": 50, "max_bytes": 512}


def test_get_quota_returns_none_when_not_set(project_dir):
    assert get_quota(project_dir) is None


def test_set_quota_defaults(project_dir):
    set_quota(project_dir)
    quota = get_quota(project_dir)
    assert quota["max_keys"] == DEFAULT_MAX_KEYS
    assert quota["max_bytes"] == DEFAULT_MAX_BYTES


def test_set_quota_missing_project_raises(tmp_path):
    with pytest.raises(QuotaError, match="does not exist"):
        set_quota(tmp_path / "ghost")


def test_set_quota_invalid_max_keys_raises(project_dir):
    with pytest.raises(QuotaError, match="max_keys"):
        set_quota(project_dir, max_keys=0)


def test_set_quota_invalid_max_bytes_raises(project_dir):
    with pytest.raises(QuotaError, match="max_bytes"):
        set_quota(project_dir, max_bytes=0)


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def test_check_quota_no_quota_set_is_noop(project_dir):
    content = "\n".join(f"KEY{i}=value{i}" for i in range(200))
    check_quota(project_dir, content)  # must not raise


def test_check_quota_within_limits_passes(project_dir):
    set_quota(project_dir, max_keys=5, max_bytes=1024)
    content = "A=1\nB=2\nC=3\n"
    check_quota(project_dir, content)  # must not raise


def test_check_quota_key_count_exceeded_raises(project_dir):
    set_quota(project_dir, max_keys=2, max_bytes=10240)
    content = "A=1\nB=2\nC=3\n"
    with pytest.raises(QuotaError, match="Secret count 3 exceeds quota limit of 2"):
        check_quota(project_dir, content)


def test_check_quota_byte_size_exceeded_raises(project_dir):
    set_quota(project_dir, max_keys=100, max_bytes=10)
    content = "LONGKEY=averylongvalue\n"
    with pytest.raises(QuotaError, match="exceeds quota limit"):
        check_quota(project_dir, content)


def test_check_quota_ignores_comments_and_blank_lines(project_dir):
    set_quota(project_dir, max_keys=2, max_bytes=10240)
    content = "# comment\n\nA=1\nB=2\n"
    check_quota(project_dir, content)  # 2 real keys — must not raise


# ---------------------------------------------------------------------------
# clear_quota
# ---------------------------------------------------------------------------

def test_clear_quota_removes_settings(project_dir):
    set_quota(project_dir)
    clear_quota(project_dir)
    assert get_quota(project_dir) is None


def test_clear_quota_noop_when_not_set(project_dir):
    clear_quota(project_dir)  # must not raise
