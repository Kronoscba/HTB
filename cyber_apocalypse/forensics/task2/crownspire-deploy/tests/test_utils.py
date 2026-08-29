import os

from crownspire.utils import iter_files, sha256_file, split_key


def test_iter_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")
    found = set(iter_files(str(tmp_path)))
    assert "a.txt" in found
    assert os.path.join("sub", "b.txt") in found


def test_sha256_file(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"hello")
    # sha256("hello")
    assert sha256_file(str(p)) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_split_key():
    assert split_key("manifests/dawn-rite.json") == ("manifests", "dawn-rite.json")
    assert split_key("top.json") == ("", "top.json")
