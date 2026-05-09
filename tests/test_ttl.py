"""Tests for envault.ttl"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from envault.ttl import (
    TTLError,
    clear_ttl,
    get_ttl,
    is_expired,
    set_ttl,
)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    """Create a fake project directory inside a storage root."""
    proj = tmp_path / "myproject"
    proj.mkdir()
    return tmp_path  # return storage root


FUTURE = datetime.now(tz=timezone.utc) + timedelta(hours=1)
PAST = datetime.now(tz=timezone.utc) - timedelta(hours=1)


# ---------------------------------------------------------------------------
# set_ttl / get_ttl
# ---------------------------------------------------------------------------

def test_set_and_get_ttl_roundtrip(project_dir: Path) -> None:
    set_ttl(project_dir, "myproject", FUTURE)
    result = get_ttl(project_dir, "myproject")
    assert result is not None
    # Timestamps should be equal within a second after ISO round-trip
    assert abs((result - FUTURE).total_seconds()) < 1


def test_get_ttl_returns_none_when_not_set(project_dir: Path) -> None:
    assert get_ttl(project_dir, "myproject") is None


def test_set_ttl_naive_datetime_treated_as_utc(project_dir: Path) -> None:
    naive = datetime.utcnow() + timedelta(hours=2)
    set_ttl(project_dir, "myproject", naive)
    result = get_ttl(project_dir, "myproject")
    assert result is not None
    assert result.tzinfo is not None


def test_set_ttl_missing_project_raises(tmp_path: Path) -> None:
    with pytest.raises(TTLError, match="does not exist"):
        set_ttl(tmp_path, "ghost", FUTURE)


# ---------------------------------------------------------------------------
# is_expired
# ---------------------------------------------------------------------------

def test_is_expired_false_for_future_ttl(project_dir: Path) -> None:
    set_ttl(project_dir, "myproject", FUTURE)
    assert is_expired(project_dir, "myproject") is False


def test_is_expired_true_for_past_ttl(project_dir: Path) -> None:
    set_ttl(project_dir, "myproject", PAST)
    assert is_expired(project_dir, "myproject") is True


def test_is_expired_false_when_no_ttl_set(project_dir: Path) -> None:
    assert is_expired(project_dir, "myproject") is False


# ---------------------------------------------------------------------------
# clear_ttl
# ---------------------------------------------------------------------------

def test_clear_ttl_removes_expiry(project_dir: Path) -> None:
    set_ttl(project_dir, "myproject", FUTURE)
    clear_ttl(project_dir, "myproject")
    assert get_ttl(project_dir, "myproject") is None


def test_clear_ttl_noop_when_not_set(project_dir: Path) -> None:
    # Should not raise
    clear_ttl(project_dir, "myproject")
