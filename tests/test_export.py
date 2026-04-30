"""Tests for envault.export — export_env and import_env helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.export import export_env, import_env


@pytest.fixture()
def mock_vault(tmp_path):
    vault = MagicMock()
    vault.pull.return_value = {"DB_HOST": "localhost", "API_KEY": "secret"}
    vault.push.return_value = None
    return vault


# ---------------------------------------------------------------------------
# export_env
# ---------------------------------------------------------------------------

def test_export_env_returns_string(mock_vault):
    result = export_env(mock_vault)
    assert isinstance(result, str)


def test_export_env_contains_all_keys(mock_vault):
    result = export_env(mock_vault)
    assert "API_KEY=secret" in result
    assert "DB_HOST=localhost" in result


def test_export_env_ends_with_newline(mock_vault):
    result = export_env(mock_vault)
    assert result.endswith("\n")


def test_export_env_writes_file(mock_vault, tmp_path):
    dest = tmp_path / "exported.env"
    export_env(mock_vault, dest=dest)
    assert dest.exists()
    content = dest.read_text()
    assert "API_KEY=secret" in content


def test_export_env_empty_secrets(mock_vault):
    mock_vault.pull.return_value = {}
    result = export_env(mock_vault)
    assert result == ""


# ---------------------------------------------------------------------------
# import_env
# ---------------------------------------------------------------------------

def test_import_env_pushes_secrets(mock_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = import_env(mock_vault, src=env_file)
    assert result == {"FOO": "bar", "BAZ": "qux"}
    mock_vault.push.assert_called_once_with({"FOO": "bar", "BAZ": "qux"})


def test_import_env_skips_comments_and_blanks(mock_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nFOO=bar\n")
    result = import_env(mock_vault, src=env_file)
    assert "FOO" in result
    assert len(result) == 1


def test_import_env_missing_file_raises(mock_vault, tmp_path):
    with pytest.raises(FileNotFoundError):
        import_env(mock_vault, src=tmp_path / "nonexistent.env")


def test_import_env_malformed_line_raises(mock_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NODEQUALS\n")
    with pytest.raises(ValueError, match="Malformed line"):
        import_env(mock_vault, src=env_file)
