import json

from crownspire.altar import all_ok, verify_dir
from crownspire.signing import write_signature

KEY = b"test-warden-key"


def _write_manifest(path, name="dawn-rite"):
    data = {
        "name": name,
        "realm": "crownspire",
        "revision": 1,
        "sigils": [{"id": "ember", "order": 1, "binding": "oath"}],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_all_ok_when_signed(tmp_path, sample_manifest):
    m = tmp_path / "dawn-rite.json"
    _write_manifest(m)
    from crownspire.manifest import load_manifest
    write_signature(load_manifest(str(m)), KEY, str(m) + ".sig")

    results = verify_dir(str(tmp_path), KEY)
    assert all_ok(results)
    assert results[0].ok


def test_missing_signature_is_refused(tmp_path):
    m = tmp_path / "dawn-rite.json"
    _write_manifest(m)
    results = verify_dir(str(tmp_path), KEY)
    assert not all_ok(results)
    assert results[0].reason == "missing signature"


def test_tampered_manifest_is_refused(tmp_path):
    from crownspire.manifest import load_manifest
    m = tmp_path / "dawn-rite.json"
    _write_manifest(m)
    write_signature(load_manifest(str(m)), KEY, str(m) + ".sig")
    # tamper after signing
    _write_manifest(m, name="dusk-rite")

    results = verify_dir(str(tmp_path), KEY)
    assert not all_ok(results)
    assert results[0].reason == "signature mismatch"


def test_empty_dir_is_not_ok(tmp_path):
    assert not all_ok(verify_dir(str(tmp_path), KEY))
