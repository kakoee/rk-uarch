"""Private resolver-path controls; no installed selector or qualifying authority."""

import os
from pathlib import Path

import pytest
from uarch_contract.hashing import sha256

from rkuarch.engines.native.host import HostBindingError, _open, _read
from rkuarch.engines.native.records import FileBinding


@pytest.mark.parametrize("name", ["../x", "/tmp/x", "./x", "a//x", "a/../x", "a\\x"])
def test_host_path_refuses_escape(tmp_path: Path, name: str) -> None:
    with pytest.raises((HostBindingError, OSError)):
        with _open(tmp_path, name):
            pytest.fail("invalid path opened")


def test_hash_and_symlink_refusal(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"actual")
    binding = FileBinding(path="target", byte_hash=sha256(b"actual"))
    assert _read(tmp_path, binding) == b"actual"
    target.write_bytes(b"changed")
    with pytest.raises(HostBindingError, match="digest mismatch"):
        _read(tmp_path, binding)
    link = tmp_path / "alias"
    link.symlink_to(target)
    with pytest.raises(OSError):
        with _open(tmp_path, "alias"):
            pytest.fail("followed symlink")


def test_open_descriptor_does_not_follow_later_path_swap(tmp_path: Path) -> None:
    (tmp_path / "input").write_bytes(b"original")
    with _open(tmp_path, "input") as fd:
        (tmp_path / "input").rename(tmp_path / "old")
        (tmp_path / "input").write_bytes(b"replacement")
        assert os.read(fd, 100) == b"original"
