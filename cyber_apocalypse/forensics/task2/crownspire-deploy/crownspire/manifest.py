"""Sigil manifest model, loading, and validation.

A *sigil manifest* is the little JSON document the Cinderbound publish to the
reliquary before a binding rite. It lists the sigils that make up a rite along
with the realm and a monotonic revision number. We keep the schema deliberately
small -- the priesthood edit these by hand.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .errors import ManifestError

REQUIRED_FIELDS = ("name", "realm", "revision", "sigils")
KNOWN_REALMS = ("valyssar", "crownspire", "ashmarch")


@dataclass
class Sigil:
    """A single sigil entry inside a manifest."""

    id: str
    order: int
    binding: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sigil":
        try:
            return cls(id=str(data["id"]), order=int(data["order"]),
                       binding=str(data["binding"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestError(f"bad sigil entry: {data!r} ({exc})") from exc


@dataclass
class Manifest:
    """An in-memory sigil manifest."""

    name: str
    realm: str
    revision: int
    sigils: List[Sigil] = field(default_factory=list)

    def canonical_bytes(self) -> bytes:
        """Return the stable byte representation used for signing.

        Keys are sorted and separators fixed so the same manifest always signs
        to the same digest regardless of how the JSON happened to be formatted
        on disk.
        """
        payload = {
            "name": self.name,
            "realm": self.realm,
            "revision": self.revision,
            "sigils": [
                {"id": s.id, "order": s.order, "binding": s.binding}
                for s in sorted(self.sigils, key=lambda s: s.order)
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Manifest":
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            raise ManifestError(f"manifest missing fields: {', '.join(missing)}")
        sigils = [Sigil.from_dict(s) for s in data["sigils"]]
        manifest = cls(
            name=str(data["name"]),
            realm=str(data["realm"]),
            revision=int(data["revision"]),
            sigils=sigils,
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        if self.realm not in KNOWN_REALMS:
            raise ManifestError(
                f"unknown realm {self.realm!r}; expected one of {KNOWN_REALMS}")
        if self.revision < 1:
            raise ManifestError("revision must be >= 1")
        orders = [s.order for s in self.sigils]
        if len(set(orders)) != len(orders):
            raise ManifestError("sigil order values must be unique")


def load_manifest(path: str) -> Manifest:
    """Load and validate a manifest from a JSON file on disk."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise ManifestError(f"no such manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest is not valid JSON: {exc}") from exc
    return Manifest.from_dict(data)
