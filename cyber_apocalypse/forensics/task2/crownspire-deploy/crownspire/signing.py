"""HMAC signing of sigil manifests.

The wardens hold a shared signing key. A manifest's signature is
``HMAC-SHA256(key, manifest.canonical_bytes())`` rendered as hex. The altar
verifies the signature before a rite is allowed to bind.
"""
from __future__ import annotations

import hashlib
import hmac

from .errors import SigningError
from .manifest import Manifest


def sign_bytes(payload: bytes, key: bytes) -> str:
    if not key:
        raise SigningError("empty signing key")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def sign_manifest(manifest: Manifest, key: bytes) -> str:
    """Return the hex signature for a manifest."""
    return sign_bytes(manifest.canonical_bytes(), key)


def verify_manifest(manifest: Manifest, key: bytes, signature: str) -> bool:
    """Constant-time check of a manifest signature."""
    expected = sign_manifest(manifest, key)
    return hmac.compare_digest(expected, signature.strip())


def write_signature(manifest: Manifest, key: bytes, sig_path: str) -> str:
    signature = sign_manifest(manifest, key)
    with open(sig_path, "w", encoding="utf-8") as fh:
        fh.write(signature + "\n")
    return signature
