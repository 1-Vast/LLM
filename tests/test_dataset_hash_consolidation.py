"""Public dataset hash aliases preserve exact file identity with bounded reads."""
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.case_memory import sha256
from tools.datasets.benchmark import sha256_file
from tools.datasets.state_evidence_followup import sha256 as evidence_hash
from tools.datasets.state_identifiability import sha256 as identity_hash
from tools.datasets.state_search_acquire import digest


@pytest.mark.parametrize("payload", [b"", b"source bytes", bytes(range(256)) * 20000], ids=["empty", "small", "large"])
def test_all_public_aliases_stream_identical_bytes(tmp_path, payload):
    path = tmp_path / "source.bin"
    path.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    with patch.object(Path, "read_bytes", side_effect=AssertionError("Whole-file allocation forbidden")):
        assert all(function(path) == expected for function in (sha256_file, evidence_hash, identity_hash, digest))
    assert all(function is sha256 for function in (sha256_file, evidence_hash, identity_hash))


def test_hash_never_reuses_same_size_timestamp_content(tmp_path):
    import os
    path = tmp_path / "source.bin"
    path.write_bytes(b"first")
    before = digest(path)
    stat = path.stat()
    path.write_bytes(b"other")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert digest(path) != before
    path.unlink()
    with pytest.raises(FileNotFoundError):
        digest(path)


def test_source_acquisition_standalone_cli_remains_available(tmp_path):
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / "tools/datasets/state_search_acquire.py"
    result = subprocess.run([sys.executable, "-I", str(script), "--help"], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
