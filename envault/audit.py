"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_DIR = Path.home() / ".envault" / "audit"


def _audit_path(project: str) -> Path:
    return AUDIT_DIR / f"{project}.log"


def record(project: str, action: str, details: Optional[str] = None) -> None:
    """Append an audit entry for the given project and action."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "action": action,
        "details": details,
    }
    with _audit_path(project).open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def get_log(project: str) -> List[dict]:
    """Return all audit entries for the given project."""
    path = _audit_path(project)
    if not path.exists():
        return []
    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def clear_log(project: str) -> None:
    """Remove the audit log for the given project."""
    path = _audit_path(project)
    if path.exists():
        path.unlink()
