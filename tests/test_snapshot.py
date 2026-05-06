"""Tests for envault.snapshot."""

import json
import pytest

from unittest.mock import MagicMock
from envault.snapshot import (
    Snapshot,
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    _snapshot_key,
)


SECRETS = {"DB_URL": "postgres://localhost/mydb", "SECRET_KEY": "s3cr3t"}
PROJECT = "myapp"


@pytest.fixture
def mock_storage():
    store: dict = {}

    storage = MagicMock()
    storage.save.side_effect = lambda k, v: store.update({k: v})
    storage.load.side_effect = lambda k: store[k] if k in store else (_ for _ in ()).throw(KeyError(k))
    storage.delete.side_effect = lambda k: store.pop(k) if k in store else (_ for _ in ()).throw(KeyError(k))
    storage.list.side_effect = lambda: list(store.keys())
    return storage


def test_create_snapshot_returns_snapshot(mock_storage):
    snap = create_snapshot(mock_storage, PROJECT, SECRETS, label="v1")
    assert isinstance(snap, Snapshot)
    assert snap.label == "v1"
    assert snap.project == PROJECT
    assert snap.secrets == SECRETS


def test_create_snapshot_persists_data(mock_storage):
    create_snapshot(mock_storage, PROJECT, SECRETS, label="v1")
    mock_storage.save.assert_called_once()
    key, raw = mock_storage.save.call_args[0]
    assert key == _snapshot_key("v1")
    data = json.loads(raw.decode())
    assert data["secrets"] == SECRETS


def test_create_snapshot_auto_label(mock_storage):
    snap = create_snapshot(mock_storage, PROJECT, SECRETS)
    assert snap.label  # non-empty
    assert "T" in snap.label  # ISO-like timestamp


def test_list_snapshots_empty(mock_storage):
    assert list_snapshots(mock_storage) == []


def test_list_snapshots_returns_labels(mock_storage):
    create_snapshot(mock_storage, PROJECT, SECRETS, label="alpha")
    create_snapshot(mock_storage, PROJECT, SECRETS, label="beta")
    labels = list_snapshots(mock_storage)
    assert set(labels) == {"alpha", "beta"}


def test_load_snapshot_roundtrip(mock_storage):
    create_snapshot(mock_storage, PROJECT, SECRETS, label="v2")
    snap = load_snapshot(mock_storage, "v2")
    assert snap.secrets == SECRETS
    assert snap.label == "v2"


def test_load_snapshot_missing_raises(mock_storage):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(mock_storage, "ghost")


def test_delete_snapshot_removes_label(mock_storage):
    create_snapshot(mock_storage, PROJECT, SECRETS, label="tmp")
    delete_snapshot(mock_storage, "tmp")
    assert "tmp" not in list_snapshots(mock_storage)


def test_delete_snapshot_missing_raises(mock_storage):
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(mock_storage, "nonexistent")


def test_snapshot_created_at_is_iso8601(mock_storage):
    from datetime import datetime
    snap = create_snapshot(mock_storage, PROJECT, SECRETS, label="ts")
    # Should parse without error
    datetime.fromisoformat(snap.created_at)
