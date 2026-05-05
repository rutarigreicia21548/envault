"""Diff utilities for comparing local .env files against vault snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffResult:
    """Holds the result of comparing a local env against the vaulted version."""

    added: List[str] = field(default_factory=list)      # keys only in local
    removed: List[str] = field(default_factory=list)    # keys only in vault
    changed: List[str] = field(default_factory=list)    # keys whose values differ
    unchanged: List[str] = field(default_factory=list)  # keys that are identical

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key in sorted(self.added):
            lines.append(f"  + {key}")
        for key in sorted(self.removed):
            lines.append(f"  - {key}")
        for key in sorted(self.changed):
            lines.append(f"  ~ {key}")
        if not lines:
            return "  (no changes)"
        return "\n".join(lines)


def parse_env(text: str) -> Dict[str, str]:
    """Parse a .env-formatted string into a key/value dict.

    Skips blank lines and comments.  Values may be optionally quoted.
    """
    result: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip matching surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def diff_envs(local_text: str, vault_text: str) -> DiffResult:
    """Return a DiffResult comparing *local_text* against *vault_text*."""
    local = parse_env(local_text)
    vault = parse_env(vault_text)

    local_keys = set(local)
    vault_keys = set(vault)

    result = DiffResult()
    result.added = list(local_keys - vault_keys)
    result.removed = list(vault_keys - local_keys)

    for key in local_keys & vault_keys:
        if local[key] != vault[key]:
            result.changed.append(key)
        else:
            result.unchanged.append(key)

    return result
