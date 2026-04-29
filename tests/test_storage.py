"""Tests for LocalStorage backend."""

import pytest
from pathlib import Path

from envault.storage import LocalStorage


@pytest.fixture
def store(tmp_path):
    return LocalStorage(storage_dir=tmp_path)


def test_save_and_load_roundtrip(store):
    store.save("myapp", "encrypted-blob", {"version": 1})
    data, meta = store.load("myapp")
    assert data == "encrypted-blob"
    assert meta["version"] == 1


def test_load_missing_project_raises(store):
    with pytest.raises(FileNotFoundError, match="myapp"):
        store.load("myapp")


def test_delete_removes_project(store):
    store.save("myapp", "blob")
    store.delete("myapp")
    assert not store.exists("myapp")


def test_delete_missing_project_raises(store):
    with pytest.raises(FileNotFoundError):
        store.delete("ghost")


def test_list_projects_empty(store):
    assert store.list_projects() == []


def test_list_projects_returns_names(store):
    store.save("alpha", "x")
    store.save("beta", "y")
    assert store.list_projects() == ["alpha", "beta"]


def test_exists_true_after_save(store):
    store.save("proj", "data")
    assert store.exists("proj")


def test_exists_false_before_save(store):
    assert not store.exists("proj")


def test_save_without_metadata(store):
    store.save("proj", "data")
    data, meta = store.load("proj")
    assert data == "data"
    assert meta == {}
