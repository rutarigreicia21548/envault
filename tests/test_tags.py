"""Tests for envault.tags."""
import pytest
from pathlib import Path

from envault.tags import (
    TagError,
    add_tag,
    find_projects_by_tag,
    get_tags,
    remove_tag,
    set_tags,
)


@pytest.fixture()
def store_dir(tmp_path: Path) -> Path:
    """A temporary storage directory with one pre-created project."""
    (tmp_path / "my-project").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# get_tags
# ---------------------------------------------------------------------------

def test_get_tags_returns_empty_list_when_no_file(store_dir):
    assert get_tags(store_dir, "my-project") == []


def test_get_tags_returns_saved_tags(store_dir):
    set_tags(store_dir, "my-project", ["prod", "backend"])
    assert set(get_tags(store_dir, "my-project")) == {"prod", "backend"}


# ---------------------------------------------------------------------------
# set_tags
# ---------------------------------------------------------------------------

def test_set_tags_deduplicates(store_dir):
    set_tags(store_dir, "my-project", ["a", "a", "b"])
    assert get_tags(store_dir, "my-project") == ["a", "b"]


def test_set_tags_missing_project_raises(store_dir):
    with pytest.raises(TagError, match="does not exist"):
        set_tags(store_dir, "ghost", ["x"])


def test_set_tags_strips_whitespace(store_dir):
    set_tags(store_dir, "my-project", ["  staging  ", " prod"])
    tags = get_tags(store_dir, "my-project")
    assert "staging" in tags
    assert "prod" in tags


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

def test_add_tag_appends(store_dir):
    add_tag(store_dir, "my-project", "v1")
    assert "v1" in get_tags(store_dir, "my-project")


def test_add_tag_idempotent(store_dir):
    add_tag(store_dir, "my-project", "v1")
    add_tag(store_dir, "my-project", "v1")
    assert get_tags(store_dir, "my-project").count("v1") == 1


def test_add_tag_empty_raises(store_dir):
    with pytest.raises(TagError, match="empty"):
        add_tag(store_dir, "my-project", "   ")


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

def test_remove_tag_removes(store_dir):
    add_tag(store_dir, "my-project", "old")
    remove_tag(store_dir, "my-project", "old")
    assert "old" not in get_tags(store_dir, "my-project")


def test_remove_tag_missing_raises(store_dir):
    with pytest.raises(TagError, match="not found"):
        remove_tag(store_dir, "my-project", "nonexistent")


# ---------------------------------------------------------------------------
# find_projects_by_tag
# ---------------------------------------------------------------------------

def test_find_projects_by_tag(store_dir):
    (store_dir / "alpha").mkdir()
    (store_dir / "beta").mkdir()
    add_tag(store_dir, "alpha", "prod")
    add_tag(store_dir, "beta", "staging")
    add_tag(store_dir, "my-project", "prod")
    result = find_projects_by_tag(store_dir, "prod")
    assert set(result) == {"alpha", "my-project"}


def test_find_projects_by_tag_empty_store(tmp_path):
    assert find_projects_by_tag(tmp_path / "nonexistent", "x") == []
