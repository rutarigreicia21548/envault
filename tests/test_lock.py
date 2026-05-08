"""Tests for envault.lock — concurrent operation lock mechanism."""

import os
import time
import pytest
from pathlib import Path

from envault.lock import acquire, release, is_locked, locked, LockError, LOCK_TIMEOUT


@pytest.fixture()
def lock_dir(tmp_path):
    return tmp_path / "locks"


def test_acquire_creates_lock_file(lock_dir):
    acquire("myproject", lock_dir)
    assert (lock_dir / "myproject.lock").exists()
    release("myproject", lock_dir)


def test_lock_file_contains_pid(lock_dir):
    acquire("myproject", lock_dir)
    content = (lock_dir / "myproject.lock").read_text().strip()
    assert content == str(os.getpid())
    release("myproject", lock_dir)


def test_release_removes_lock_file(lock_dir):
    acquire("myproject", lock_dir)
    release("myproject", lock_dir)
    assert not (lock_dir / "myproject.lock").exists()


def test_release_missing_lock_does_not_raise(lock_dir):
    release("nonexistent", lock_dir)  # should not raise


def test_is_locked_returns_true_when_locked(lock_dir):
    acquire("alpha", lock_dir)
    assert is_locked("alpha", lock_dir) is True
    release("alpha", lock_dir)


def test_is_locked_returns_false_when_not_locked(lock_dir):
    assert is_locked("alpha", lock_dir) is False


def test_acquire_raises_if_already_locked(lock_dir):
    acquire("beta", lock_dir)
    with pytest.raises(LockError, match="beta"):
        acquire("beta", lock_dir)
    release("beta", lock_dir)


def test_acquire_clears_stale_lock(lock_dir, monkeypatch):
    acquire("gamma", lock_dir)
    lock_file = lock_dir / "gamma.lock"
    # Backdate the lock file to simulate a stale lock
    stale_mtime = time.time() - LOCK_TIMEOUT - 5
    os.utime(lock_file, (stale_mtime, stale_mtime))
    # Should succeed without raising
    acquire("gamma", lock_dir)
    release("gamma", lock_dir)


def test_locked_context_manager_acquires_and_releases(lock_dir):
    with locked("delta", lock_dir):
        assert is_locked("delta", lock_dir)
    assert not is_locked("delta", lock_dir)


def test_locked_context_manager_releases_on_exception(lock_dir):
    with pytest.raises(RuntimeError):
        with locked("epsilon", lock_dir):
            assert is_locked("epsilon", lock_dir)
            raise RuntimeError("boom")
    assert not is_locked("epsilon", lock_dir)


def test_project_name_with_slashes_is_safe(lock_dir):
    acquire("org/project", lock_dir)
    assert (lock_dir / "org_project.lock").exists()
    assert is_locked("org/project", lock_dir)
    release("org/project", lock_dir)
