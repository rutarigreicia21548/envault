"""Tests for envault.cli_share — share CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_share import share_create, share_redeem
from envault.share import create_share_token

SECRETS = {"KEY": "value", "TOKEN": "abc123"}
PASSWORD = "testpass"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_vault():
    vault = MagicMock()
    vault.pull.return_value = SECRETS
    return vault


def test_share_create_outputs_token(runner, mock_vault):
    with patch("envault.cli_share._make_vault", return_value=mock_vault):
        result = runner.invoke(
            share_create,
            ["--project", "myapp", "--password", PASSWORD, "--ttl", "3600"],
        )
    assert result.exit_code == 0
    assert "fingerprint" in result.output


def test_share_create_with_label(runner, mock_vault):
    with patch("envault.cli_share._make_vault", return_value=mock_vault):
        result = runner.invoke(
            share_create,
            ["--project", "myapp", "--password", PASSWORD, "--label", "staging"],
        )
    assert result.exit_code == 0


def test_share_create_vault_error(runner):
    with patch("envault.cli_share._make_vault", side_effect=Exception("vault not found")):
        result = runner.invoke(
            share_create,
            ["--project", "missing", "--password", PASSWORD],
        )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_share_redeem_success(runner, mock_vault):
    token = create_share_token(SECRETS, PASSWORD)
    with patch("envault.cli_share._make_vault", return_value=mock_vault):
        result = runner.invoke(
            share_redeem,
            [token, "--password", PASSWORD, "--project", "myapp", "--vault-password", PASSWORD],
        )
    assert result.exit_code == 0
    assert "pushed" in result.output
    mock_vault.push.assert_called_once_with(SECRETS)


def test_share_redeem_wrong_password(runner, mock_vault):
    token = create_share_token(SECRETS, PASSWORD)
    with patch("envault.cli_share._make_vault", return_value=mock_vault):
        result = runner.invoke(
            share_redeem,
            [token, "--password", "badpass", "--project", "myapp", "--vault-password", PASSWORD],
        )
    assert result.exit_code == 1
    assert "Share error" in result.output


def test_share_redeem_expired_token(runner, mock_vault):
    token = create_share_token(SECRETS, PASSWORD, ttl=-1)
    with patch("envault.cli_share._make_vault", return_value=mock_vault):
        result = runner.invoke(
            share_redeem,
            [token, "--password", PASSWORD, "--project", "myapp", "--vault-password", PASSWORD],
        )
    assert result.exit_code == 1
    assert "expired" in result.output
