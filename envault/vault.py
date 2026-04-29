"""High-level Vault API: push/pull .env files to/from encrypted storage."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.crypto import encrypt, decrypt
from envault.storage import LocalStorage


class Vault:
    """Manages encryption and storage of .env files for a project."""

    def __init__(self, project: str, password: str, storage: Optional[LocalStorage] = None):
        if not project:
            raise ValueError("Project name must not be empty")
        if not password:
            raise ValueError("Password must not be empty")
        self.project = project
        self.password = password
        self.storage = storage or LocalStorage()

    def push(self, env_path: str | Path = ".env") -> None:
        """Encrypt and upload a local .env file to storage."""
        env_path = Path(env_path)
        if not env_path.exists():
            raise FileNotFoundError(f".env file not found: {env_path}")
        plaintext = env_path.read_text(encoding="utf-8")
        encrypted = encrypt(plaintext, self.password)
        metadata = {
            "pushed_at": datetime.now(timezone.utc).isoformat(),
            "source": str(env_path.resolve()),
        }
        self.storage.save(self.project, encrypted, metadata)

    def pull(self, env_path: str | Path = ".env", overwrite: bool = False) -> None:
        """Download and decrypt secrets, writing them to a local .env file."""
        env_path = Path(env_path)
        if env_path.exists() and not overwrite:
            raise FileExistsError(
                f"{env_path} already exists. Use overwrite=True to replace it."
            )
        encrypted, _ = self.storage.load(self.project)
        plaintext = decrypt(encrypted, self.password)
        env_path.write_text(plaintext, encoding="utf-8")

    def status(self) -> dict:
        """Return metadata about the stored secrets for this project."""
        if not self.storage.exists(self.project):
            return {"project": self.project, "stored": False}
        _, metadata = self.storage.load(self.project)
        return {"project": self.project, "stored": True, **metadata}

    def delete(self) -> None:
        """Remove stored secrets for this project."""
        self.storage.delete(self.project)
