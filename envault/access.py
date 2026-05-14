"""Access control: per-project read/write role enforcement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

VALID_ROLES = {"reader", "writer", "admin"}


class AccessError(Exception):
    """Raised when an access control operation fails."""


def _access_path(project_dir: Path) -> Path:
    return project_dir / ".envault" / "access.json"


def get_acl(project_dir: Path) -> dict:
    """Return the ACL dict for a project, or an empty dict if none exists."""
    path = _access_path(project_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def set_acl(project_dir: Path, acl: dict) -> None:
    """Persist an ACL dict for a project."""
    if not project_dir.exists():
        raise AccessError(f"Project directory not found: {project_dir}")
    path = _access_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(acl, fh, indent=2)


def grant(project_dir: Path, identity: str, role: str) -> None:
    """Grant *role* to *identity* for the project."""
    if role not in VALID_ROLES:
        raise AccessError(f"Invalid role '{role}'. Must be one of: {sorted(VALID_ROLES)}")
    acl = get_acl(project_dir)
    acl[identity] = role
    set_acl(project_dir, acl)


def revoke(project_dir: Path, identity: str) -> None:
    """Remove *identity* from the project ACL."""
    acl = get_acl(project_dir)
    if identity not in acl:
        raise AccessError(f"Identity '{identity}' not found in ACL.")
    del acl[identity]
    set_acl(project_dir, acl)


def get_role(project_dir: Path, identity: str) -> Optional[str]:
    """Return the role for *identity*, or None if not present."""
    return get_acl(project_dir).get(identity)


def check_permission(project_dir: Path, identity: str, required_role: str) -> None:
    """Raise AccessError if *identity* does not hold at least *required_role*."""
    hierarchy = ["reader", "writer", "admin"]
    if required_role not in hierarchy:
        raise AccessError(f"Unknown required role: {required_role}")
    role = get_role(project_dir, identity)
    if role is None:
        raise AccessError(f"Identity '{identity}' has no access to this project.")
    if hierarchy.index(role) < hierarchy.index(required_role):
        raise AccessError(
            f"Identity '{identity}' has role '{role}' but '{required_role}' is required."
        )


def list_identities(project_dir: Path) -> List[dict]:
    """Return a list of {identity, role} dicts sorted by identity."""
    acl = get_acl(project_dir)
    return [{"identity": k, "role": v} for k, v in sorted(acl.items())]
