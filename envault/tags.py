"""Tag management for envault projects.

Allows users to attach arbitrary string tags to projects for
organisation, filtering, and search.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(storage_dir: str | Path, project: str) -> Path:
    return Path(storage_dir) / project / "tags.json"


def get_tags(storage_dir: str | Path, project: str) -> List[str]:
    """Return the list of tags for *project*, or an empty list."""
    path = _tags_path(storage_dir, project)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            raise TagError(f"Corrupt tags file for project '{project}'")
        return [str(t) for t in data]
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file for project '{project}': {exc}") from exc


def set_tags(storage_dir: str | Path, project: str, tags: List[str]) -> None:
    """Overwrite the tag list for *project*."""
    path = _tags_path(storage_dir, project)
    if not path.parent.exists():
        raise TagError(f"Project '{project}' does not exist")
    cleaned = sorted({t.strip() for t in tags if t.strip()})
    path.write_text(json.dumps(cleaned, indent=2))


def add_tag(storage_dir: str | Path, project: str, tag: str) -> List[str]:
    """Add *tag* to *project*; returns the updated tag list."""
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must not be empty")
    current = get_tags(storage_dir, project)
    if tag not in current:
        current.append(tag)
        set_tags(storage_dir, project, current)
    return get_tags(storage_dir, project)


def remove_tag(storage_dir: str | Path, project: str, tag: str) -> List[str]:
    """Remove *tag* from *project*; returns the updated tag list."""
    tag = tag.strip()
    current = get_tags(storage_dir, project)
    if tag not in current:
        raise TagError(f"Tag '{tag}' not found on project '{project}'")
    current.remove(tag)
    set_tags(storage_dir, project, current)
    return get_tags(storage_dir, project)


def find_projects_by_tag(storage_dir: str | Path, tag: str) -> List[str]:
    """Return all project names that carry *tag*."""
    base = Path(storage_dir)
    if not base.exists():
        return []
    return [
        p.name
        for p in sorted(base.iterdir())
        if p.is_dir() and tag in get_tags(storage_dir, p.name)
    ]
