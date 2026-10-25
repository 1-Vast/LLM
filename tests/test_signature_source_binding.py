"""Parsed model/calibration values must come from the bytes their receipts bind."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from virtual_cell import signature_retrieval as signatures


def make_library(tmp_path):
    arrays = dict(profiles=np.array([[1., 2.]]), entry_compound=np.array([0]),
                  entry_line=np.array([0]), entry_dose=np.array([0]),
                  systematic=np.array([[[1., 2.]]]))
    np.savez(tmp_path / 'library.npz', **arrays)
    meta = dict(schema=signatures.LIBRARY_SCHEMA, genes=['A', 'B'], lines=['L'], doses=[1.],
                compounds=[{'name': 'C', 'smiles': 'C', 'skeleton': 'C'}],
                arrays_sha256=hashlib.sha256((tmp_path / 'library.npz').read_bytes()).hexdigest())
    (tmp_path / 'library.json').write_text(json.dumps(meta))
    return arrays, meta


def test_arrays_are_parsed_from_the_exact_bytes_already_verified(tmp_path, monkeypatch):
    arrays, meta = make_library(tmp_path)
    original_load = np.load

    def concurrent_replacement(target, *args, **kwargs):
        np.savez(tmp_path / 'library.npz', **{**arrays, 'profiles': np.array([[99., 100.]])})
        return original_load(target, *args, **kwargs)

    monkeypatch.setattr(signatures.np, 'load', concurrent_replacement)
    loaded = signatures.load_library(tmp_path)
    np.testing.assert_array_equal(loaded.profiles, arrays['profiles'])
    assert loaded.metadata['arrays_sha256'] == meta['arrays_sha256']


def test_changed_arrays_are_refused_before_parse(tmp_path):
    _, _ = make_library(tmp_path)
    (tmp_path / 'library.npz').write_bytes(b'changed')
    with pytest.raises(ValueError, match='digest_mismatch'):
        signatures.load_library(tmp_path)


def test_calibration_values_version_and_receipt_share_one_payload(tmp_path, monkeypatch):
    make_library(tmp_path)
    calibration_path = tmp_path / 'calibration.json'
    original = dict(level=0.8, quantiles={}, gene_sets={}, informative={}, coverage={}, acceptance={})
    original_bytes = json.dumps(original).encode()
    calibration_path.write_bytes(original_bytes)
    real_open = Path.open
    opens = []

    def concurrent_open(path, *args, **kwargs):
        if path == calibration_path:
            if opens:
                with real_open(path, 'wb') as stream:
                    stream.write(json.dumps({**original, 'level': 0.9}).encode())
            opens.append(path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', concurrent_open)
    monkeypatch.setattr(signatures, '_fingerprints', lambda values: np.ones((len(values), 1)))
    monkeypatch.setattr(signatures.SciPlexResponseRung, '_receipt', lambda self, name: None)
    rung = signatures.SciPlexResponseRung(signatures.ResponseRungConfig(tmp_path, calibration_path))
    assert rung.level == original['level']
    assert rung.calibration_sha256 == hashlib.sha256(original_bytes).hexdigest()
    assert len(opens) == 1
    digest = hashlib.sha256()
    digest.update(str(rung.library.metadata['arrays_sha256']).encode())
    digest.update(original_bytes)
    assert rung.model_version == 'sciplex3_reference_response_' + digest.hexdigest()[:16]
