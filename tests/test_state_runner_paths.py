"""The State validation runner has two execution paths, and they must agree.

File summary
- Path: tests/test_state_runner_paths.py
- Purpose: pin the runner's execution contract: the same entry point with the same
  arguments, run in this interpreter when that interpreter is the configured State
  one, and in a subprocess when it is not.
- Core points: the fast path is an execution detail, never a weaker check -- it must
  reach the same verdict and still refuse a mismatched input basis by name. The
  fixture writes distinct content for the two paths because the adapter memoises an
  inspection by content identity, and a shared key would report the first answer
  instead of the second run.
- Interfaces: `StateCapabilityAdapter.runs_runner_in_process`, `StateAdapterConfig.runner_mode`
- Depends on: virtual_cell.state_adapter, tests/test_production_contract_gaps fixtures
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from virtual_cell import QuerySupport  # noqa: E402

from tools.shared.state_fixture import (  # noqa: E402
    DEFAULT_BASIS,
    adapter as _adapter,
    asset_sha256 as _sha256,
    joined as _joined,
    registration as _registration,
    request as _request,
    requires_asset_runtime as requires_runtime,
    write_asset as _write_asset,
)


def _registration_with_basis(directory: Path, asset: Path, names, *, features: int = 8) -> object:
    identity = directory / f"identity_{features}.json"
    identity.write_text(
        json.dumps(
            {
                "dataset_sha256": _sha256(asset),
                "feature_count": features,
                "names": list(names),
            }
        ),
        encoding="utf-8",
    )
    return replace(_registration("tiny", asset, features=features), feature_names_path=identity)


@requires_runtime
def test_the_in_process_runner_reaches_the_subprocess_verdict(tmp_path):
    """Same arguments, same checks, same verdict -- whichever way it is executed."""

    in_process_dir = tmp_path / "in_process"
    subprocess_dir = tmp_path / "subprocess"
    in_process_dir.mkdir()
    subprocess_dir.mkdir()

    # Different feature counts keep the two inspections distinct: the adapter memoises
    # by content identity, so identical content would return the first answer twice and
    # the second path would never run.
    first_asset = _write_asset(in_process_dir, features=8)
    second_asset = _write_asset(subprocess_dir, features=9)

    in_process = _adapter(
        in_process_dir,
        datasets={"tiny": _registration_with_basis(in_process_dir, first_asset, DEFAULT_BASIS)},
        runner_mode="in_process",
    )
    subprocess_adapter = _adapter(
        subprocess_dir,
        datasets={
            "tiny": _registration_with_basis(
                subprocess_dir, second_asset, tuple(f"g{i}" for i in range(9)), features=9
            )
        },
        input_dim=9,
        input_coordinate_names=tuple(f"g{i}" for i in range(9)),
        runner_mode="subprocess",
    )

    assert in_process.runs_runner_in_process() is True
    assert subprocess_adapter.runs_runner_in_process() is False

    fast = in_process.assess_query(_request())
    slow = subprocess_adapter.assess_query(_request())
    assert fast.support is QuerySupport.SUPPORTED, _joined(fast)
    assert slow.support is QuerySupport.SUPPORTED, _joined(slow)
    assert fast.limitations == slow.limitations


@requires_runtime
def test_the_in_process_runner_still_refuses_a_different_basis(tmp_path):
    """The fast path performs the same check, so a mismatched basis is still refused."""

    asset = _write_asset(tmp_path, features=8)
    other_basis = tuple(f"x{index}" for index in range(8))
    adapter = _adapter(
        tmp_path,
        datasets={"tiny": _registration_with_basis(tmp_path, asset, other_basis, features=8)},
        runner_mode="in_process",
    )
    assessment = adapter.assess_query(_request())
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert "input_basis_mismatch:tiny:8_of_8_coordinates_disagree" in _joined(assessment)
