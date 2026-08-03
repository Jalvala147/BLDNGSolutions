"""Password helpers compatible with Werkzeug 3 and legacy sha256$ hashes."""
from __future__ import annotations

import hashlib
import hmac

from werkzeug.security import (
    check_password_hash as _wz_check_password_hash,
    generate_password_hash as _wz_generate_password_hash,
)

# New hashes use pbkdf2:sha256 (supported by Werkzeug 3).
HASH_METHOD = "pbkdf2:sha256"


def generate_password_hash(password: str) -> str:
    return _wz_generate_password_hash(password, method=HASH_METHOD)


def _check_legacy_sha256(pwhash: str, password: str) -> bool:
    """Verify hashes created with Werkzeug < 3 method='sha256'."""
    try:
        method, salt, hashval = pwhash.split("$", 2)
    except ValueError:
        return False

    if method != "sha256":
        return False

    digest = hashlib.sha256()
    digest.update(salt.encode("utf-8"))
    digest.update(password.encode("utf-8"))
    return hmac.compare_digest(digest.hexdigest(), hashval)


def check_password_hash(pwhash: str, password: str) -> bool:
    """Check modern Werkzeug hashes, with fallback for legacy sha256$ hashes."""
    if not pwhash or not password:
        return False

    try:
        if _wz_check_password_hash(pwhash, password):
            return True
    except ValueError:
        # Werkzeug 3 raises on unsupported methods such as plain sha256
        pass

    return _check_legacy_sha256(pwhash, password)
