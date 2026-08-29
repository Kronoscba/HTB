import json

import pytest

from crownspire.manifest import Manifest, Sigil


@pytest.fixture
def sample_manifest():
    return Manifest(
        name="dawn-rite",
        realm="crownspire",
        revision=3,
        sigils=[
            Sigil(id="ember", order=1, binding="oath"),
            Sigil(id="brine", order=2, binding="seal"),
        ],
    )


@pytest.fixture
def manifest_file(tmp_path, sample_manifest):
    data = {
        "name": sample_manifest.name,
        "realm": sample_manifest.realm,
        "revision": sample_manifest.revision,
        "sigils": [
            {"id": s.id, "order": s.order, "binding": s.binding}
            for s in sample_manifest.sigils
        ],
    }
    path = tmp_path / "dawn-rite.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def signing_key():
    return b"test-warden-key"
