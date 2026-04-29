"""Remote storage backend for encrypted .env files."""

import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_STORAGE_DIR = Path.home() / ".envault" / "store"


class LocalStorage:
    """File-system based storage backend (used for testing and local mode)."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project: str) -> Path:
        return self.storage_dir / f"{project}.enc"

    def save(self, project: str, encrypted_data: str, metadata: Optional[dict] = None) -> None:
        """Persist encrypted env data for a project."""
        payload = {
            "data": encrypted_data,
            "meta": metadata or {},
        }
        path = self._project_path(project)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def load(self, project: str) -> tuple[str, dict]:
        """Load encrypted env data for a project. Returns (data, metadata)."""
        path = self._project_path(project)
        if not path.exists():
            raise FileNotFoundError(f"No stored secrets found for project '{project}'")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload["data"], payload.get("meta", {})

    def delete(self, project: str) -> None:
        """Remove stored secrets for a project."""
        path = self._project_path(project)
        if not path.exists():
            raise FileNotFoundError(f"No stored secrets found for project '{project}'")
        path.unlink()

    def list_projects(self) -> list[str]:
        """Return all project names that have stored secrets."""
        return [
            p.stem for p in sorted(self.storage_dir.glob("*.enc"))
        ]

    def exists(self, project: str) -> bool:
        """Check whether secrets exist for a given project."""
        return self._project_path(project).exists()
