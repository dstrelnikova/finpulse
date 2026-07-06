from __future__ import annotations

import hashlib
import hmac
import os

_PBKDF2_PREFIX = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith(f"{_PBKDF2_PREFIX}$"):
        return _verify_pbkdf2(password, stored_hash)

    # Backward compatibility for existing MVP users created with legacy SHA-256 hashes.
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def _verify_pbkdf2(password: str, stored_hash: str) -> bool:
    try:
        _, iterations_raw, salt, expected = stored_hash.split("$", 3)
        iterations = int(iterations_raw)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
        return hmac.compare_digest(digest.hex(), expected)
    except (TypeError, ValueError):
        return False
