"""Access policy enforcement for envault projects."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

POLICY_FILENAME = "policy.json"


class PolicyError(Exception):
    """Raised when a policy violation or configuration error occurs."""


@dataclass
class Policy:
    """Defines access rules for a project's secrets."""

    allowed_keys: List[str] = field(default_factory=list)  # empty = allow all
    denied_keys: List[str] = field(default_factory=list)
    read_only: bool = False
    require_tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "allowed_keys": self.allowed_keys,
            "denied_keys": self.denied_keys,
            "read_only": self.read_only,
            "require_tags": self.require_tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Policy":
        return cls(
            allowed_keys=data.get("allowed_keys", []),
            denied_keys=data.get("denied_keys", []),
            read_only=data.get("read_only", False),
            require_tags=data.get("require_tags", {}),
        )


def _policy_path(project: str, storage_dir: Path) -> Path:
    return storage_dir / project / POLICY_FILENAME


def save_policy(project: str, policy: Policy, storage_dir: Path) -> None:
    path = _policy_path(project, storage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy.to_dict(), indent=2))


def load_policy(project: str, storage_dir: Path) -> Optional[Policy]:
    path = _policy_path(project, storage_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Policy.from_dict(data)


def enforce(policy: Policy, key: str, write: bool = False) -> None:
    """Raise PolicyError if *key* is not permitted under *policy*."""
    if key in policy.denied_keys:
        raise PolicyError(f"Key '{key}' is explicitly denied by policy.")
    if policy.allowed_keys and key not in policy.allowed_keys:
        raise PolicyError(f"Key '{key}' is not in the allowed-keys list.")
    if write and policy.read_only:
        raise PolicyError("Policy forbids write operations on this project.")


def check_env(policy: Policy, env: dict, write: bool = False) -> List[str]:
    """Return a list of violation messages for all keys in *env*."""
    violations: List[str] = []
    for key in env:
        try:
            enforce(policy, key, write=write)
        except PolicyError as exc:
            violations.append(str(exc))
    return violations
