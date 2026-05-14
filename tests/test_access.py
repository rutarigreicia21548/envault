"""Tests for envault.access module."""

import pytest
from pathlib import Path

from envault.access import (
    AccessError,
    grant,
    revoke,
    get_role,
    check_permission,
    list_identities,
    get_acl,
)


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "myproject"
    project.mkdir()
    return project


def test_get_acl_returns_empty_when_no_file(project_dir):
    assert get_acl(project_dir) == {}


def test_grant_creates_acl_entry(project_dir):
    grant(project_dir, "alice", "writer")
    assert get_role(project_dir, "alice") == "writer"


def test_grant_invalid_role_raises(project_dir):
    with pytest.raises(AccessError, match="Invalid role"):
        grant(project_dir, "alice", "superuser")


def test_grant_missing_project_raises(tmp_path):
    missing = tmp_path / "ghost"
    with pytest.raises(AccessError, match="Project directory not found"):
        grant(missing, "alice", "reader")


def test_grant_overwrites_existing_role(project_dir):
    grant(project_dir, "bob", "reader")
    grant(project_dir, "bob", "admin")
    assert get_role(project_dir, "bob") == "admin"


def test_revoke_removes_identity(project_dir):
    grant(project_dir, "carol", "reader")
    revoke(project_dir, "carol")
    assert get_role(project_dir, "carol") is None


def test_revoke_missing_identity_raises(project_dir):
    with pytest.raises(AccessError, match="not found in ACL"):
        revoke(project_dir, "nobody")


def test_get_role_returns_none_for_unknown_identity(project_dir):
    assert get_role(project_dir, "stranger") is None


def test_check_permission_passes_exact_role(project_dir):
    grant(project_dir, "dave", "writer")
    check_permission(project_dir, "dave", "writer")  # should not raise


def test_check_permission_passes_higher_role(project_dir):
    grant(project_dir, "eve", "admin")
    check_permission(project_dir, "eve", "reader")  # admin >= reader


def test_check_permission_fails_insufficient_role(project_dir):
    grant(project_dir, "frank", "reader")
    with pytest.raises(AccessError, match="'writer' is required"):
        check_permission(project_dir, "frank", "writer")


def test_check_permission_fails_no_access(project_dir):
    with pytest.raises(AccessError, match="has no access"):
        check_permission(project_dir, "ghost", "reader")


def test_list_identities_sorted(project_dir):
    grant(project_dir, "zara", "reader")
    grant(project_dir, "alice", "admin")
    grant(project_dir, "mike", "writer")
    result = list_identities(project_dir)
    assert [e["identity"] for e in result] == ["alice", "mike", "zara"]
    assert result[0]["role"] == "admin"


def test_list_identities_empty(project_dir):
    assert list_identities(project_dir) == []
