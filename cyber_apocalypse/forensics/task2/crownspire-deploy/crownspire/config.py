"""Runtime configuration, loaded from the environment.

Credentials never live in the repo. In CI they arrive from the secret store
(see ``.github/workflows/deploy.yml``); locally they come from an untracked
``.env`` that mirrors ``.env.example``. This module is the single place that
reads them.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional

from .errors import ConfigError

REQUIRED_ENV = (
    "RELIQUARY_ENDPOINT",
    "RELIQUARY_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "WARDEN_SIGNING_KEY",
)


@dataclass
class Config:
    endpoint: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    signing_key: str

    @property
    def signing_key_bytes(self) -> bytes:
        return self.signing_key.encode("utf-8")

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "Config":
        env = os.environ if env is None else env
        missing = [k for k in REQUIRED_ENV if not env.get(k)]
        if missing:
            raise ConfigError(
                "missing required environment variables: " + ", ".join(missing)
            )
        return cls(
            endpoint=env["RELIQUARY_ENDPOINT"],
            bucket=env["RELIQUARY_BUCKET"],
            access_key_id=env["AWS_ACCESS_KEY_ID"],
            secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
            signing_key=env["WARDEN_SIGNING_KEY"],
        )
