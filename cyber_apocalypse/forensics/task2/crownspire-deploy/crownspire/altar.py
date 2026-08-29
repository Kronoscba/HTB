"""Altar-side verification.

Before a rite may bind, the altar re-verifies every manifest in a published set
against its detached signature. This is the last gate the priesthood have: a
manifest whose signature does not verify -- or that arrives without one -- is
refused, and the rite does not proceed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from .manifest import load_manifest
from .signing import verify_manifest


@dataclass
class AltarResult:
    manifest: str
    ok: bool
    reason: str = ""


def verify_dir(build_dir: str, key: bytes) -> List[AltarResult]:
    """Verify every ``*.json`` manifest in ``build_dir`` against its ``.sig``."""
    results: List[AltarResult] = []
    for name in sorted(os.listdir(build_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(build_dir, name)
        sig_path = path + ".sig"
        if not os.path.exists(sig_path):
            results.append(AltarResult(name, False, "missing signature"))
            continue
        manifest = load_manifest(path)
        with open(sig_path, "r", encoding="utf-8") as fh:
            signature = fh.read()
        ok = verify_manifest(manifest, key, signature)
        results.append(AltarResult(name, ok, "" if ok else "signature mismatch"))
    return results


def all_ok(results: List[AltarResult]) -> bool:
    return bool(results) and all(r.ok for r in results)
