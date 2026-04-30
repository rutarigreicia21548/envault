"""Tests for envault.audit module."""

import pytest
from unittest.mock import patch
from pathlib import Path
import tempfile

import envault.audit as audit


@pytest.fixture(autouse=True)
def isolated_audit_dir(tmp_path):
    """Redirect audit logs to a temporary directory for each test."""
    with patch.object(audit, "AUDIT_DIR", tmp_path / "audit"):
        yield


def test_record_creates_log_file():
    audit.record("myproject", "push")
    log = audit.get_log("myproject")
    assert len(log) == 1
    assert log[0]["action"] == "push"
    assert log[0]["project"] == "myproject"


def test_record_appends_multiple_entries():
    audit.record("proj", "push")
    audit.record("proj", "pull")
    audit.record("proj", "status")
    log = audit.get_log("proj")
    assert len(log) == 3
    assert [e["action"] for e in log] == ["push", "pull", "status"]


def test_record_stores_details():
    audit.record("proj", "push", details="pushed 3 keys")
    log = audit.get_log("proj")
    assert log[0]["details"] == "pushed 3 keys"


def test_record_timestamp_is_iso8601():
    audit.record("proj", "push")
    log = audit.get_log("proj")
    ts = log[0]["timestamp"]
    from datetime import datetime
    parsed = datetime.fromisoformat(ts)
    assert parsed is not None


def test_get_log_missing_project_returns_empty():
    result = audit.get_log("nonexistent")
    assert result == []


def test_clear_log_removes_file():
    audit.record("proj", "push")
    audit.clear_log("proj")
    assert audit.get_log("proj") == []


def test_clear_log_missing_project_does_not_raise():
    audit.clear_log("ghost_project")  # should not raise


def test_logs_are_isolated_per_project():
    audit.record("alpha", "push")
    audit.record("beta", "pull")
    assert len(audit.get_log("alpha")) == 1
    assert audit.get_log("alpha")[0]["action"] == "push"
    assert len(audit.get_log("beta")) == 1
    assert audit.get_log("beta")[0]["action"] == "pull"
