"""The input basis a checkpoint reads, and the failure that passes every other check.

File summary
- Path: tests/test_input_basis_identity.py
- Purpose: Pin the refusal that catches an asset stored in a different coordinate
  basis from the one the checkpoint was trained on, and record the pre-fix
  behaviour that made such an asset acceptable.
- Core points:
  - A dataset may declare the correct embedding key and the correct feature count
    and still be in another basis; those two facts cannot detect it.
  - The refusal is named: `input_basis_mismatch` when the identities disagree,
    `input_basis_unverified` when the asset declares no identity to compare.
  - The last test is the receipt for the silent path: with no declared model
    basis, the very same mismatched asset is accepted.
- Interfaces: pytest test functions
- Depends on: virtual_cell.state_adapter, tests/test_production_contract_gaps fixtures
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from virtual_cell import QuerySupport  # noqa: E402

from tools.shared.state_fixture import (  # noqa: E402
    adapter as _adapter,
    asset_sha256 as _sha256,
    joined as _joined,
    registration as _registration,
    request as _request,
    requires_asset_runtime as requires_runtime,
    write_asset as _write_asset,
)

MODEL_BASIS = tuple(f"g{index}" for index in range(8))
OTHER_BASIS = tuple(f"x{index}" for index in range(8))


def _identity(directory: Path, asset: Path, names) -> Path:
    path = directory / "identity.json"
    path.write_text(
        json.dumps({"dataset_sha256": _sha256(asset), "feature_count": 8, "names": list(names)}),
        encoding="utf-8",
    )
    return path


@requires_runtime
def test_an_asset_in_the_checkpoints_own_basis_stays_executable(tmp_path):
    """The positive path: identities agree coordinate by coordinate."""

    asset = _write_asset(tmp_path)
    registration = replace(
        _registration("tiny", asset), feature_names_path=_identity(tmp_path, asset, MODEL_BASIS)
    )
    assessment = _adapter(
        tmp_path, datasets={"tiny": registration}, input_coordinate_names=MODEL_BASIS
    ).assess_query(_request())
    assert assessment.support is QuerySupport.SUPPORTED, _joined(assessment)


@requires_runtime
def test_an_asset_in_a_different_basis_is_refused_by_name(tmp_path):
    """The defect: same embedding key, same feature count, different coordinates."""

    asset = _write_asset(tmp_path)
    registration = replace(
        _registration("tiny", asset), feature_names_path=_identity(tmp_path, asset, OTHER_BASIS)
    )
    assessment = _adapter(
        tmp_path, datasets={"tiny": registration}, input_coordinate_names=MODEL_BASIS
    ).assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "input_basis_mismatch:tiny:8_of_8_coordinates_disagree" in _joined(assessment)


@requires_runtime
def test_an_asset_that_declares_no_coordinate_identity_is_not_assumed_to_match(tmp_path):
    """An unverifiable basis is reported as unverified, not treated as agreement.

    The asset is registered here without an identity file. The shared fixture now
    binds one to its default asset, so relying on that default would test the
    agreeing path instead of this one.
    """

    asset = _write_asset(tmp_path)
    assessment = _adapter(
        tmp_path,
        datasets={"tiny": _registration("tiny", asset)},
        input_coordinate_names=MODEL_BASIS,
    ).assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "input_basis_unverified:tiny" in _joined(assessment)


@requires_runtime
def test_a_model_that_declares_no_basis_is_refused_rather_than_accepted(tmp_path):
    """Fail closed, where this test previously recorded the opposite as a receipt.

    Until 2026-09-19 the guard returned "no problem" when the model declared no input
    basis, so this very asset -- whose coordinates are a different gene selection --
    was **accepted**, and the superseded assertions were `support is SUPPORTED` with no
    `input_basis` string anywhere in the assessment. Every other registered fact agreed
    with it, which is what made the failure silent and is the whole reason the check
    exists. A guard that passes when nothing is declared is not a guard, so the
    undeclared case is now refused by name and the old behaviour survives only as this
    note.
    """

    asset = _write_asset(tmp_path)
    registration = replace(
        _registration("tiny", asset), feature_names_path=_identity(tmp_path, asset, OTHER_BASIS)
    )
    assessment = _adapter(
        tmp_path, datasets={"tiny": registration}, input_coordinate_names=()
    ).assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "input_basis_undeclared:tiny" in _joined(assessment)
