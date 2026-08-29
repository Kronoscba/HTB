import subprocess

import pytest

from crownspire.config import Config
from crownspire.errors import ReliquaryError
from crownspire.reliquary import Reliquary

CONFIG = Config(
    endpoint="https://reliquary.crownspire.valyssar:9000",
    bucket="crownspire-reliquary-prod",
    access_key_id="AKIATEST",
    secret_access_key="shhh",
    signing_key="sigil-key",
)


class FakeCompleted:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_sync_builds_expected_command(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return FakeCompleted(stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    Reliquary(CONFIG).sync("build", prefix="manifests")

    assert captured["cmd"][0] == "aws"
    assert "--endpoint-url" in captured["cmd"]
    assert captured["cmd"][-1] == "s3://crownspire-reliquary-prod/manifests/"


def test_list_parses_keys(monkeypatch):
    sample = (
        "2026-05-20 10:00:00        128 dawn-rite.json\n"
        "2026-05-20 10:00:01         64 dawn-rite.json.sig\n"
    )
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: FakeCompleted(stdout=sample))
    keys = Reliquary(CONFIG).list()
    assert keys == ["dawn-rite.json", "dawn-rite.json.sig"]


def test_missing_aws_binary(monkeypatch):
    def boom(cmd, **kwargs):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(ReliquaryError):
        Reliquary(CONFIG).put("x", "y")


def test_failed_command_raises(monkeypatch):
    def fail(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="403 Forbidden")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(ReliquaryError) as exc:
        Reliquary(CONFIG).sync("build")
    assert "403" in str(exc.value)
