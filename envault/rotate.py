"""Key rotation support for envault.

Provides functionality to re-encrypt stored secrets with a new password,
allowing users to rotate their encryption keys without losing data.
"""

from __future__ import annotations

from typing import Optional

from envault.audit import record
from envault.crypto import decrypt, encrypt
from envault.storage import LocalStorage


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    project: str,
    old_password: str,
    new_password: str,
    storage: Optional[LocalStorage] = None,
) -> None:
    """Re-encrypt a project's secrets with a new password.

    Decrypts all stored environment variables using *old_password*, then
    re-encrypts them with *new_password* and writes the result back to
    storage atomically (load → decrypt → re-encrypt → save).

    Args:
        project:      The project name whose secrets should be rotated.
        old_password: The current encryption password.
        new_password: The replacement encryption password.
        storage:      Optional storage backend; defaults to LocalStorage().

    Raises:
        RotationError: If decryption with the old password fails, or if
                       the project does not exist in storage.
    """
    if storage is None:
        storage = LocalStorage()

    # Load the currently stored (encrypted) secrets.
    try:
        encrypted_data: dict[str, str] = storage.load(project)
    except FileNotFoundError as exc:
        raise RotationError(
            f"Project '{project}' not found in storage."
        ) from exc

    # Decrypt every value with the old password.
    try:
        plaintext_data: dict[str, str] = {
            key: decrypt(value, old_password)
            for key, value in encrypted_data.items()
        }
    except Exception as exc:
        raise RotationError(
            "Failed to decrypt secrets with the provided old password. "
            "Ensure the password is correct."
        ) from exc

    # Re-encrypt every value with the new password.
    rotated_data: dict[str, str] = {
        key: encrypt(value, new_password)
        for key, value in plaintext_data.items()
    }

    # Persist the re-encrypted data.
    storage.save(project, rotated_data)

    record(
        project,
        "rotate_key",
        {"keys_rotated": list(rotated_data.keys()), "key_count": len(rotated_data)},
    )


def rotate_key_for_all(
    old_password: str,
    new_password: str,
    storage: Optional[LocalStorage] = None,
) -> list[str]:
    """Rotate the encryption key for every project in storage.

    Iterates over all projects returned by ``storage.list_projects()`` and
    calls :func:`rotate_key` for each one.

    Args:
        old_password: The current encryption password shared by all projects.
        new_password: The replacement encryption password.
        storage:      Optional storage backend; defaults to LocalStorage().

    Returns:
        A list of project names that were successfully rotated.

    Raises:
        RotationError: If any individual project rotation fails.  Projects
                       processed before the failure are already re-encrypted.
    """
    if storage is None:
        storage = LocalStorage()

    projects = storage.list_projects()
    rotated: list[str] = []

    for project in projects:
        rotate_key(project, old_password, new_password, storage=storage)
        rotated.append(project)

    return rotated
