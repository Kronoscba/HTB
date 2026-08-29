"""Assorted small helpers with no better home."""
from __future__ import annotations

import hashlib
import os
from typing import Iterator, Tuple


def iter_files(root: str) -> Iterator[str]:
    """Yield every file path under ``root`` (sorted, relative to root)."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, root)


def sha256_file(path: str, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def split_key(path: str) -> Tuple[str, str]:
    """Split a reliquary key into (prefix, name)."""
    prefix, _, name = path.rpartition("/")
    return prefix, name
