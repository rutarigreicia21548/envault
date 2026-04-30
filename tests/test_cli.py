"""Tests for envault CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from pathlib import Path

from envault.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDEBUG=true\n")
    return p


def _mock_vault(push_result=None, pull_result=None, status_result=None, history_result=None):
    vault = MagicMock()
    vault.push.return_value = push_result or {"keys": 2}
    vault.pull.return_value = pull_result or {"keys": 2}
    vault.status.return_value = status_result or {"local": True, "remote": True, "in_sync": True}
    vault.history.return_value = history_result or []
    return vault


def test_push_success(runner, env_file):
    mock = _mock_vault()
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["push", "--project", "proj", "--password", "pw", "--env-file", str(env_file)],
        )
    assert result.exit_code == 0
    assert "2 key(s)" in result.output


def test_push_missing_env_file(runner, tmp_path):
    missing = tmp_path / "missing.env"
    mock = MagicMock()
    mock.push.side_effect = FileNotFoundError("missing.env not found")
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["push", "--project", "proj", "--password", "pw", "--env-file", str(missing)],
        )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_pull_success(runner, env_file):
    mock = _mock_vault()
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["pull", "--project", "proj", "--password", "pw", "--env-file", str(env_file)],
        )
    assert result.exit_code == 0
    assert "2 key(s)" in result.output


def test_status_in_sync(runner, env_file):
    mock = _mock_vault(status_result={"local": True, "remote": True, "in_sync": True})
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["status", "--project", "proj", "--password", "pw", "--env-file", str(env_file)],
        )
    assert result.exit_code == 0
    assert "In sync: yes" in result.output


def test_history_no_entries(runner, env_file):
    mock = _mock_vault(history_result=[])
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["history", "--project", "proj", "--password", "pw", "--env-file", str(env_file)],
        )
    assert result.exit_code == 0
    assert "No history" in result.output


def test_history_with_entries(runner, env_file):
    entries = [
        {"timestamp": "2024-01-01T00:00:00+00:00", "action": "push", "details": "pushed 2 keys"},
        {"timestamp": "2024-01-02T00:00:00+00:00", "action": "pull", "details": None},
    ]
    mock = _mock_vault(history_result=entries)
    with patch("envault.cli._make_vault", return_value=mock):
        result = runner.invoke(
            cli,
            ["history", "--project", "proj", "--password", "pw", "--env-file", str(env_file)],
        )
    assert result.exit_code == 0
    assert "push" in result.output
    assert "pushed 2 keys" in result.output
    assert "pull" in result.output
