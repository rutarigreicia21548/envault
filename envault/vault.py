"""Vault: high-level API for push/pull/status of .env files."""

from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt
from envault.storage import LocalStorage
import envault.audit as audit


class Vault:
    def __init__(
        self,
        project: str,
        password: str,
        env_path: Path,
        storage: Optional[LocalStorage] = None,
    ) -> None:
        self.project = project
        self.password = password
        self.env_path = Path(env_path)
        self.storage = storage or LocalStorage()

    def push(self) -> Dict[str, int]:
        """Encrypt and upload the local .env file to storage."""
        if not self.env_path.exists():
            raise FileNotFoundError(f"{self.env_path} not found")
        plaintext = self.env_path.read_text()
        ciphertext = encrypt(plaintext, self.password)
        self.storage.save(self.project, ciphertext)
        key_count = sum(
            1
            for line in plaintext.splitlines()
            if line.strip() and not line.strip().startswith("#") and "=" in line
        )
        audit.record(self.project, "push", details=f"pushed {key_count} keys")
        return {"keys": key_count}

    def pull(self) -> Dict[str, int]:
        """Download and decrypt the remote .env file to disk."""
        ciphertext = self.storage.load(self.project)
        plaintext = decrypt(ciphertext, self.password)
        self.env_path.write_text(plaintext)
        key_count = sum(
            1
            for line in plaintext.splitlines()
            if line.strip() and not line.strip().startswith("#") and "=" in line
        )
        audit.record(self.project, "pull", details=f"pulled {key_count} keys")
        return {"keys": key_count}

    def status(self) -> Dict[str, object]:
        """Return sync status comparing local and remote state."""
        local_exists = self.env_path.exists()
        remote_exists = self.storage.exists(self.project)
        audit.record(self.project, "status")
        return {
            "local": local_exists,
            "remote": remote_exists,
            "in_sync": local_exists and remote_exists,
        }

    def history(self) -> list:
        """Return the audit log for this project."""
        return audit.get_log(self.project)
