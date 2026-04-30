"""Tests for the envault CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli import cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("SECRET=hello\nAPI_KEY=world\n")
    return f


def _mock_vault():
    vault = MagicMock()
    vault.status.return_value = "in_sync"
    return vault


def test_push_success(runner, env_file):
    with patch("envault.cli._make_vault", return_value=_mock_vault()) as mk:
        result = runner.invoke(
            cli,
            ["push", "myproject", "--env", str(env_file), "--password", "secret", "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "Pushed secrets for project 'myproject'" in result.output
        mk.return_value.push.assert_called_once()


def test_push_missing_env_file(runner, tmp_path):
    missing = tmp_path / "nonexistent.env"
    result = runner.invoke(
        cli,
        ["push", "myproject", "--env", str(missing), "--password", "secret", "--password", "secret"],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_pull_success(runner, env_file):
    with patch("envault.cli._make_vault", return_value=_mock_vault()):
        result = runner.invoke(
            cli,
            ["pull", "myproject", "--env", str(env_file), "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "Pulled secrets for project 'myproject'" in result.output


def test_pull_missing_project(runner, env_file):
    mock_vault = _mock_vault()
    mock_vault.pull.side_effect = KeyError("myproject")
    with patch("envault.cli._make_vault", return_value=mock_vault):
        result = runner.invoke(
            cli,
            ["pull", "myproject", "--env", str(env_file), "--password", "secret"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output


def test_status_command(runner, env_file):
    with patch("envault.cli._make_vault", return_value=_mock_vault()):
        result = runner.invoke(
            cli,
            ["status", "myproject", "--env", str(env_file), "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "in_sync" in result.output
