"""Public dataset hash aliases preserve exact file identity with bounded reads."""
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.case_memory import sha256, md5


@pytest.mark.parametrize("payload", [b"", b"source bytes", bytes(range(256)) * 20000], ids=["empty", "small", "large"])
def test_file_hashes_stream_identical_bytes(tmp_path, payload):
    path = tmp_path / "source.bin"
    path.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    with patch.object(Path, "read_bytes", side_effect=AssertionError("Whole-file allocation forbidden")):
        assert sha256(path) == expected
        assert md5(path) == hashlib.md5(payload).hexdigest()


def test_hash_never_reuses_same_size_timestamp_content(tmp_path):
    import os
    path = tmp_path / "source.bin"
    path.write_bytes(b"first")
    before = sha256(path)
    stat = path.stat()
    path.write_bytes(b"other")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert sha256(path) != before
    path.unlink()
    with pytest.raises(FileNotFoundError):
        sha256(path)
