from crownspire.cli import main


def test_validate_ok(manifest_file, capsys):
    rc = main(["validate", manifest_file])
    out = capsys.readouterr().out
    assert rc == 0
    assert "dawn-rite" in out


def test_validate_bad_file(capsys):
    rc = main(["validate", "nope.json"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "error:" in err


def test_sign_and_verify(manifest_file, monkeypatch, tmp_path, capsys):
    env = {
        "RELIQUARY_ENDPOINT": "https://x:9000",
        "RELIQUARY_BUCKET": "b",
        "AWS_ACCESS_KEY_ID": "k",
        "AWS_SECRET_ACCESS_KEY": "s",
        "WARDEN_SIGNING_KEY": "sigil-key",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    sig_path = str(tmp_path / "m.sig")
    assert main(["sign", manifest_file, "-o", sig_path]) == 0
    assert main(["verify", manifest_file, sig_path]) == 0
