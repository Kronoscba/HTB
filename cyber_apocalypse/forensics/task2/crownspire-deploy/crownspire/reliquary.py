"""Thin client for the Crownspire reliquary (an S3-compatible object store).

We shell out to the ``aws`` CLI rather than pulling in boto3 -- the deploy box
already has it and it keeps our dependency surface tiny. The reliquary sits
behind a self-hosted gateway, so every call needs an explicit endpoint URL.
"""
from __future__ import annotations

import subprocess
from typing import List

from .config import Config
from .errors import ReliquaryError


class Reliquary:
    def __init__(self, config: Config, aws_bin: str = "aws"):
        self.config = config
        self.aws_bin = aws_bin

    def _base_args(self) -> List[str]:
        return [self.aws_bin, "--endpoint-url", self.config.endpoint]

    def _run(self, args: List[str]) -> str:
        cmd = self._base_args() + args
        try:
            proc = subprocess.run(
                cmd, check=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise ReliquaryError(f"aws binary not found: {self.aws_bin}") from exc
        except subprocess.CalledProcessError as exc:
            raise ReliquaryError(
                f"reliquary command failed ({exc.returncode}): {exc.stderr.strip()}"
            ) from exc
        return proc.stdout

    def put(self, local_path: str, key: str) -> None:
        """Upload a single object to ``s3://<bucket>/<key>``."""
        target = f"s3://{self.config.bucket}/{key}"
        self._run(["s3", "cp", local_path, target])

    def sync(self, local_dir: str, prefix: str = "") -> None:
        """Sync a directory tree into the reliquary under an optional prefix."""
        target = f"s3://{self.config.bucket}/{prefix}".rstrip("/") + "/"
        self._run(["s3", "sync", local_dir, target])

    def list(self, prefix: str = "") -> List[str]:
        out = self._run(["s3", "ls", f"s3://{self.config.bucket}/{prefix}"])
        keys = []
        for line in out.splitlines():
            parts = line.split()
            if parts:
                keys.append(parts[-1])
        return keys
