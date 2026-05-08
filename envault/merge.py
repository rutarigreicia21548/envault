"""Merge utilities for combining .env files with conflict detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MergeConflict:
    key: str
    local_value: str
    remote_value: str

    def __str__(self) -> str:
        return (
            f"Conflict on '{self.key}': "
            f"local={self.local_value!r}, remote={self.remote_value!r}"
        )


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = [f"Merged {len(self.merged)} key(s)."]
        if self.conflicts:
            lines.append(f"{len(self.conflicts)} conflict(s):")
            for c in self.conflicts:
                lines.append(f"  {c}")
        return "\n".join(lines)


def parse_env(text: str) -> Dict[str, str]:
    """Parse .env text into a key/value dict, skipping comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def merge_envs(
    base: Dict[str, str],
    local: Dict[str, str],
    remote: Dict[str, str],
    strategy: str = "ours",
) -> MergeResult:
    """Three-way merge of env dicts.

    Keys only in local or remote are added unconditionally.
    Keys in both local and remote that differ from base are conflicts.
    strategy='ours'  -> local wins on conflict
    strategy='theirs' -> remote wins on conflict
    """
    if strategy not in ("ours", "theirs"):
        raise ValueError(f"Unknown merge strategy: {strategy!r}")

    merged: Dict[str, str] = dict(base)
    conflicts: List[MergeConflict] = []

    all_keys = set(local) | set(remote)
    for key in all_keys:
        in_local = key in local
        in_remote = key in remote
        base_val: Optional[str] = base.get(key)

        if in_local and not in_remote:
            merged[key] = local[key]
        elif in_remote and not in_local:
            merged[key] = remote[key]
        else:
            lval, rval = local[key], remote[key]
            if lval == rval:
                merged[key] = lval
            elif lval == base_val:
                # only remote changed
                merged[key] = rval
            elif rval == base_val:
                # only local changed
                merged[key] = lval
            else:
                # both changed — genuine conflict
                conflicts.append(MergeConflict(key, lval, rval))
                merged[key] = lval if strategy == "ours" else rval

    return MergeResult(merged=merged, conflicts=conflicts)
