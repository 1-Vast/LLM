"""Frozen restoration must reproduce original bytes and fail before partial writes."""
import json

import pytest

from research.astra.reproducibility_audit import digest, restore_pack


def _cache(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    raw = b'{\r\n "original": true\r\n}\r\n'
    arrays = b"binary fixture\x00\x01"
    (cache / "pack.json").write_bytes(raw.replace(b"\r\n", b"\n"))
    (cache / "pack_arrays.npz").write_bytes(arrays)
    (cache / "pack_manifest.json").write_text(json.dumps({"outputs": {
        "pack.json": digest(raw), "pack_arrays.npz": digest(arrays)}}))
    return cache, raw, arrays


def test_restore_requires_exact_frozen_bytes_and_preserves_original_manifest(tmp_path):
    cache, raw, arrays = _cache(tmp_path)
    destination = tmp_path / "restored"
    receipt = restore_pack(cache, destination)
    assert (destination / "pack.json").read_bytes() == raw
    assert (destination / "pack_arrays.npz").read_bytes() == arrays
    assert (destination / "pack_manifest.json").read_bytes() == (cache / "pack_manifest.json").read_bytes()
    assert receipt["pack.json"]["method"] == "verified_CRLF_reconstruction"
    with pytest.raises(FileExistsError):
        restore_pack(cache, destination)


@pytest.mark.parametrize("name", ["pack.json", "pack_arrays.npz"])
def test_corrupt_assets_fail_before_any_restoration(tmp_path, name):
    cache, _, _ = _cache(tmp_path)
    (cache / name).write_bytes(b"corrupted")
    destination = tmp_path / "restored"
    with pytest.raises(ValueError, match="frozen_asset_hash_mismatch"):
        restore_pack(cache, destination)
    assert not destination.exists()
