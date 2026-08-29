from crownspire.dotenv import load_dotenv, parse_env


def test_parse_basic():
    parsed = parse_env("A=1\nB=two\n")
    assert parsed == {"A": "1", "B": "two"}


def test_parse_ignores_comments_and_blanks():
    parsed = parse_env("# comment\n\nA=1\n   \n# another\nB=2\n")
    assert parsed == {"A": "1", "B": "2"}


def test_parse_strips_quotes_and_export():
    parsed = parse_env('export A="quoted"\nB=\'single\'\n')
    assert parsed == {"A": "quoted", "B": "single"}


def test_load_missing_file_is_noop(tmp_path):
    assert load_dotenv(str(tmp_path / "nope.env"), environ={}) == {}


def test_load_does_not_override_by_default(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=fromfile\n", encoding="utf-8")
    env = {"A": "existing"}
    load_dotenv(str(p), environ=env)
    assert env["A"] == "existing"


def test_load_override(tmp_path):
    p = tmp_path / ".env"
    p.write_text("A=fromfile\n", encoding="utf-8")
    env = {"A": "existing"}
    load_dotenv(str(p), environ=env, override=True)
    assert env["A"] == "fromfile"
