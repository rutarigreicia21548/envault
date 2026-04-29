"""Tests for the high-level Vault API."""

import pytest
from pathlib import Path

from envault.storage import LocalStorage
from envault.vault import Vault


ENV_CONTENT = "DB_HOST=localhost\nDB_PASS=secret\nDEBUG=true\n"
PASSWORD = "correct-horse-battery-staple"
PROJECT = "test-project"


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(storage_dir=tmp_path)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT, encoding="utf-8")
    return p


@pytest.fixture
def vault(storage):
    return Vault(PROJECT, PASSWORD, storage=storage)


def test_push_stores_encrypted_data(vault, env_file, storage):
    vault.push(env_file)
    assert storage.exists(PROJECT)


def test_pull_restores_env_file(vault, env_file, tmp_path):
    vault.push(env_file)
    out = tmp_path / ".env.out"
    vault.pull(out, overwrite=True)
    assert out.read_text(encoding="utf-8") == ENV_CONTENT


def test_pull_raises_if_file_exists_and_no_overwrite(vault, env_file, tmp_path):
    vault.push(env_file)
    existing = tmp_path / "existing.env"
    existing.write_text("OLD=1", encoding="utf-8")
    with pytest.raises(FileExistsError):
        vault.pull(existing)


def test_pull_with_wrong_password_raises(vault, env_file, tmp_path, storage):
    vault.push(env_file)
    wrong_vault = Vault(PROJECT, "wrong-password", storage=storage)
    out = tmp_path / ".env.out"
    with pytest.raises(Exception):
        wrong_vault.pull(out, overwrite=True)


def test_push_missing_env_file_raises(vault, tmp_path):
    with pytest.raises(FileNotFoundError):
        vault.push(tmp_path / "nonexistent.env")


def test_status_not_stored(vault):
    result = vault.status()
    assert result["stored"] is False
    assert result["project"] == PROJECT


def test_status_after_push(vault, env_file):
    vault.push(env_file)
    result = vault.status()
    assert result["stored"] is True
    assert "pushed_at" in result


def test_delete_removes_project(vault, env_file, storage):
    vault.push(env_file)
    vault.delete()
    assert not storage.exists(PROJECT)


def test_vault_empty_project_raises(storage):
    with pytest.raises(ValueError, match="Project"):
        Vault("", PASSWORD, storage=storage)


def test_vault_empty_password_raises(storage):
    with pytest.raises(ValueError, match="Password"):
        Vault(PROJECT, "", storage=storage)
