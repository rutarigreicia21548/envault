"""Export and import utilities for envault secrets.

Supports exporting decrypted .env contents to stdout or a file,
and importing from an existing .env file into the vault.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.vault import Vault


def export_env(vault: Vault, dest: Optional[Path] = None) -> str:
    """Pull secrets from vault and return as .env-formatted string.

    If *dest* is provided the content is also written to that path.

    Returns:
        The plaintext .env content as a string.

    Raises:
        KeyError: If no secrets exist for the project in remote storage.
    """
    secrets: dict[str, str] = vault.pull(write=False)

    lines = [f"{key}={value}" for key, value in sorted(secrets.items())]
    content = "\n".join(lines) + ("\n" if lines else "")

    if dest is not None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    return content


def import_env(vault: Vault, src: Path) -> dict[str, str]:
    """Read *src* .env file, push its contents into the vault.

    Returns:
        Parsed key/value mapping that was pushed.

    Raises:
        FileNotFoundError: If *src* does not exist.
        ValueError: If a line in *src* is malformed (not key=value).
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f".env file not found: {src}")

    secrets: dict[str, str] = {}
    for lineno, raw in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"Malformed line {lineno} in {src!r}: expected KEY=VALUE, got {raw!r}"
            )
        key, _, value = line.partition("=")
        secrets[key.strip()] = value.strip()

    vault.push(secrets)
    return secrets
