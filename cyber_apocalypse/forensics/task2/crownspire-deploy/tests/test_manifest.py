import pytest

from crownspire.errors import ManifestError
from crownspire.manifest import Manifest, load_manifest


def test_load_valid_manifest(manifest_file):
    manifest = load_manifest(manifest_file)
    assert manifest.name == "dawn-rite"
    assert manifest.revision == 3
    assert len(manifest.sigils) == 2


def test_missing_file():
    with pytest.raises(ManifestError):
        load_manifest("does-not-exist.json")


def test_bad_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(str(path))


def test_missing_fields():
    with pytest.raises(ManifestError):
        Manifest.from_dict({"name": "x"})


def test_unknown_realm():
    with pytest.raises(ManifestError):
        Manifest.from_dict({
            "name": "x", "realm": "nowhere", "revision": 1, "sigils": [],
        })


def test_duplicate_order():
    with pytest.raises(ManifestError):
        Manifest.from_dict({
            "name": "x", "realm": "valyssar", "revision": 1,
            "sigils": [
                {"id": "a", "order": 1, "binding": "oath"},
                {"id": "b", "order": 1, "binding": "seal"},
            ],
        })


def test_canonical_bytes_is_order_independent(sample_manifest):
    reordered = Manifest(
        name=sample_manifest.name,
        realm=sample_manifest.realm,
        revision=sample_manifest.revision,
        sigils=list(reversed(sample_manifest.sigils)),
    )
    assert sample_manifest.canonical_bytes() == reordered.canonical_bytes()
