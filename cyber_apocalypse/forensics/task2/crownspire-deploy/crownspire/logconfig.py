"""Small logging helper so the CLI and tests share one format.

Kept separate from :mod:`crownspire.cli` so library users can call
:func:`setup_logging` without importing argparse machinery.
"""
from __future__ import annotations

import logging
import os

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup_logging(level: str | int | None = None) -> logging.Logger:
    if level is None:
        level = os.environ.get("CROWNSPIRE_LOG_LEVEL", "INFO")
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=level, format=_DEFAULT_FORMAT)
    return logging.getLogger("crownspire")
