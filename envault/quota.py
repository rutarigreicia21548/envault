"""Quota management — enforce per-project secret count and total size limits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

DEFAULT_MAX_KEYS = 100
DEFAULT_MAX_BYTES = 1024 * 1024  # 1 MiB


class QuotaError(Exception):
    """Raised when a quota limit is exceeded or quota data is invalid."""


def _quota_path(project_dir: Path) -> Path:
    return project_dir / ".quota.json"


def set_quota(
    project_dir: Path,
    max_keys: int = DEFAULT_MAX_KEYS,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> None:
    """Persist quota settings for *project_dir*."""
    if not project_dir.exists():
        raise QuotaError(f"Project directory does not exist: {project_dir}")
    if max_keys < 1:
        raise QuotaError("max_keys must be at least 1")
    if max_bytes < 1:
        raise QuotaError("max_bytes must be at least 1")
    _quota_path(project_dir).write_text(
        json.dumps({"max_keys": max_keys, "max_bytes": max_bytes})
    )


def get_quota(project_dir: Path) -> Optional[dict]:
    """Return quota settings or *None* if none have been configured."""
    path = _quota_path(project_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def check_quota(project_dir: Path, env_content: str) -> None:
    """Raise :class:`QuotaError` if *env_content* would exceed configured limits.

    If no quota has been set the check is a no-op.
    """
    quota = get_quota(project_dir)
    if quota is None:
        return

    lines = [
        line
        for line in env_content.splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    ]
    key_count = len(lines)
    byte_size = len(env_content.encode())

    if key_count > quota["max_keys"]:
        raise QuotaError(
            f"Secret count {key_count} exceeds quota limit of {quota['max_keys']} keys"
        )
    if byte_size > quota["max_bytes"]:
        raise QuotaError(
            f"Payload size {byte_size} B exceeds quota limit of {quota['max_bytes']} B"
        )


def clear_quota(project_dir: Path) -> None:
    """Remove quota settings for *project_dir* (no-op if not set)."""
    path = _quota_path(project_dir)
    if path.exists():
        path.unlink()
