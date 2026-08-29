"""A tiny .env loader.

We do not want a third-party dependency just to read five keys out of a file,
so this parses the small subset of the dotenv format we actually use: blank
lines, ``# comments``, ``KEY=VALUE`` pairs, optional surrounding quotes, and a
leading ``export``. Anything fancier is out of scope on purpose.
"""
from __future__ import annotations

import os
from typing import Dict, Mapping, Optional


def parse_env(text: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load_dotenv(path: str = ".env",
                environ: Optional[Mapping[str, str]] = None,
                override: bool = False) -> Dict[str, str]:
    """Load ``path`` into ``os.environ`` (unless it already holds the key).

    Returns the parsed mapping. Missing files are silently ignored -- in CI the
    values come from the secret store, so there is no ``.env`` on disk.
    """
    target = os.environ if environ is None else environ
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        parsed = parse_env(fh.read())
    for key, value in parsed.items():
        if override or key not in target:
            target[key] = value
    return parsed
