"""Snapshot support: capture and restore point-in-time copies of a vault's secrets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envault.storage import LocalStorage


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    project: str
    label: str
    created_at: str
    secrets: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "label": self.label,
            "created_at": self.created_at,
            "secrets": self.secrets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            project=data["project"],
            label=data["label"],
            created_at=data["created_at"],
            secrets=data.get("secrets", {}),
        )


def _snapshot_key(label: str) -> str:
    return f"__snapshot__{label}"


def create_snapshot(storage: LocalStorage, project: str, secrets: Dict[str, str], label: Optional[str] = None) -> Snapshot:
    """Save a named snapshot of *secrets* for *project*."""
    if label is None:
        label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snap = Snapshot(
        project=project,
        label=label,
        created_at=datetime.now(timezone.utc).isoformat(),
        secrets=secrets,
    )
    storage.save(_snapshot_key(label), json.dumps(snap.to_dict()).encode())
    return snap


def list_snapshots(storage: LocalStorage) -> List[str]:
    """Return labels of all snapshots stored in *storage*."""
    prefix = "__snapshot__"
    return [
        key[len(prefix):]
        for key in storage.list()
        if key.startswith(prefix)
    ]


def load_snapshot(storage: LocalStorage, label: str) -> Snapshot:
    """Load and return the snapshot identified by *label*."""
    key = _snapshot_key(label)
    try:
        raw = storage.load(key)
    except KeyError:
        raise SnapshotError(f"Snapshot '{label}' not found.")
    return Snapshot.from_dict(json.loads(raw.decode()))


def delete_snapshot(storage: LocalStorage, label: str) -> None:
    """Delete the snapshot identified by *label*."""
    key = _snapshot_key(label)
    try:
        storage.delete(key)
    except KeyError:
        raise SnapshotError(f"Snapshot '{label}' not found.")
