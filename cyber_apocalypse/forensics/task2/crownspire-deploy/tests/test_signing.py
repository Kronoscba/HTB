import pytest

from crownspire.errors import SigningError
from crownspire.signing import sign_manifest, verify_manifest, write_signature


def test_sign_is_deterministic(sample_manifest, signing_key):
    a = sign_manifest(sample_manifest, signing_key)
    b = sign_manifest(sample_manifest, signing_key)
    assert a == b
    assert len(a) == 64  # sha256 hex


def test_verify_roundtrip(sample_manifest, signing_key):
    sig = sign_manifest(sample_manifest, signing_key)
    assert verify_manifest(sample_manifest, signing_key, sig)


def test_verify_rejects_wrong_key(sample_manifest, signing_key):
    sig = sign_manifest(sample_manifest, signing_key)
    assert not verify_manifest(sample_manifest, b"other-key", sig)


def test_empty_key_raises(sample_manifest):
    with pytest.raises(SigningError):
        sign_manifest(sample_manifest, b"")


def test_write_signature(tmp_path, sample_manifest, signing_key):
    sig_path = tmp_path / "m.sig"
    written = write_signature(sample_manifest, signing_key, str(sig_path))
    assert sig_path.read_text().strip() == written
