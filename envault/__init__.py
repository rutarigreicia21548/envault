"""envault — Lightweight secrets manager that syncs .env files with encrypted remote storage."""

__version__ = "0.1.0"
__author__ = "envault contributors"

from envault.crypto import encrypt, decrypt

__all__ = ["encrypt", "decrypt"]
