import pytest

from crownspire.config import Config
from crownspire.errors import ConfigError

FULL_ENV = {
    "RELIQUARY_ENDPOINT": "https://reliquary.crownspire.valyssar:9000",
    "RELIQUARY_BUCKET": "crownspire-reliquary-prod",
    "AWS_ACCESS_KEY_ID": "AKIATEST",
    "AWS_SECRET_ACCESS_KEY": "shhh",
    "WARDEN_SIGNING_KEY": "sigil-key",
}


def test_from_env_ok():
    config = Config.from_env(FULL_ENV)
    assert config.bucket == "crownspire-reliquary-prod"
    assert config.signing_key_bytes == b"sigil-key"


def test_missing_one_var():
    env = dict(FULL_ENV)
    del env["WARDEN_SIGNING_KEY"]
    with pytest.raises(ConfigError) as exc:
        Config.from_env(env)
    assert "WARDEN_SIGNING_KEY" in str(exc.value)


def test_empty_var_counts_as_missing():
    env = dict(FULL_ENV, AWS_SECRET_ACCESS_KEY="")
    with pytest.raises(ConfigError):
        Config.from_env(env)
