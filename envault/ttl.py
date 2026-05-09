"""TTL (time-to-live) support for vault secrets — mark a project's secrets
with an expiry time and query whether they have expired."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TTL_FILENAME = ".ttl.json"


class TTLError(Exception)"""Raised when a TTL operation fails."""


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _ttl_path(storage_dir: Path, project: str) -> Path:
    return storage_dir / project / TTL_FILENAME


def set_ttl(storage_dir: Path, project: str, expires_at: datetime) -> None:
    """Persist an expiry timestamp for *project*.

    *expires_at* should be timezone-aware; naive datetimes are treated as UTC.
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    ttl_file = _ttl_path(storage_dir, project)
    if not ttl_file.parent.exists():
        raise TTLError(f"Project '{project}' does not exist in storage.")

    ttl_file.write_text(
        json.dumps({"expires_at": expires_at.isoformat()}), encoding="utf-8"
    )


def get_ttl(storage_dir: Path, project: str) -> Optional[datetime]:
    """Return the expiry datetime for *project*, or ``None`` if no TTL is set."""
    ttl_file = _ttl_path(storage_dir, project)
    if not ttl_file.exists():
        return None

    data = json.loads(ttl_file.read_text(encoding="utf-8"))
    return datetime.fromisoformat(data["expires_at"])


def is_expired(storage_dir: Path, project: str) -> bool:
    """Return ``True`` if the project's TTL has passed, ``False`` otherwise.

    Projects with no TTL are never considered expired.
    """
    expiry = get_ttl(storage_dir, project)
    if expiry is None:
        return False
    now = datetime.now(tz=timezone.utc)
    return now >= expiry


def clear_ttl(storage_dir: Path, project: str) -> None:
    """Remove the TTL for *project*.  No-op if no TTL is set."""
    ttl_file = _ttl_path(storage_dir, project)
    if ttl_file.exists():
        ttl_file.unlink()
