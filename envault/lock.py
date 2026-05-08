"""Lock mechanism to prevent concurrent vault operations on the same project."""

import os
import time
import tempfile
from pathlib import Path
from contextlib import contextmanager

DEFAULT_LOCK_DIR = Path(tempfile.gettempdir()) / "envault_locks"
LOCK_TIMEOUT = 30  # seconds


class LockError(Exception):
    """Raised when a vault lock cannot be acquired."""


def _lock_path(project: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> Path:
    safe = project.replace("/", "_").replace("\\", "_")
    return lock_dir / f"{safe}.lock"


def acquire(project: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> Path:
    """Acquire a lock for the given project. Returns the lock file path."""
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path(project, lock_dir)

    if path.exists():
        try:
            mtime = path.stat().st_mtime
            age = time.time() - mtime
            if age < LOCK_TIMEOUT:
                pid = path.read_text().strip()
                raise LockError(
                    f"Project '{project}' is locked by PID {pid} "
                    f"(age {age:.1f}s). Try again shortly."
                )
            # Stale lock — remove it
            path.unlink()
        except FileNotFoundError:
            pass  # Removed between check and stat

    path.write_text(str(os.getpid()))
    return path


def release(project: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> None:
    """Release the lock for the given project."""
    path = _lock_path(project, lock_dir)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def is_locked(project: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> bool:
    """Return True if the project is currently locked (and lock is not stale)."""
    path = _lock_path(project, lock_dir)
    if not path.exists():
        return False
    try:
        age = time.time() - path.stat().st_mtime
        return age < LOCK_TIMEOUT
    except FileNotFoundError:
        return False


@contextmanager
def locked(project: str, lock_dir: Path = DEFAULT_LOCK_DIR):
    """Context manager that acquires and releases a project lock."""
    acquire(project, lock_dir)
    try:
        yield
    finally:
        release(project, lock_dir)
