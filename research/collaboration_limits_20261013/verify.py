"""Offline verification: freeze, replays of every recorded result, and parity of the promoted decoder.

File summary
- Path: research/collaboration_limits_20261013/verify.py
- Purpose: show that every JSON result in this folder is reproduced from code and data, and that the
  promoted `maestro.endpoint_decision` makes the frozen research decoder's decisions.
- Core points:
  - The freeze is checked with the study's own rule (CRLF normalised to LF; DEVIATIONS.json unhashed).
  - Each replay runs into a temporary folder by pointing the frozen module's ``OUT`` there, so the
    one-shot guards stay intact and nothing in this folder is rewritten.
  - The fresh evaluation is replayed from the saved choices and predictions; choices are replayed from
    references and anchors only. Compressed archives carry timestamps, so arrays are compared, not bytes.
  - Floats match to a relative 1e-9 (BLAS thread order); everything else matches exactly.
- Commands:
  - default (maestro env, Python 3.11): freeze, GCP replays and decoder parity;
  - ``--l1000`` (C:/Python314/python, scikit-learn 1.8 for the Block Q certifier pickle): replays of
    rkt_ceiling.json, rkt_learning_curve.json and rkt_memory.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))


def same(a, b, path: str = "$", tol: float = 1e-9) -> list[str]:
    """Differences between two JSON values; floats within a relative ``tol``."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{path}: keys {sorted(set(a) ^ set(b))}"] if set(a) != set(b) else []
        return out + [d for k in sorted(set(a) & set(b)) for d in same(a[k], b[k], f"{path}.{k}", tol)]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [d for k, (x, y) in enumerate(zip(a, b)) for d in same(x, y, f"{path}[{k}]", tol)]
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return [f"{path}: {a!r} != {b!r}"]
        return [] if abs(a - b) <= tol * max(1.0, abs(a), abs(b)) else [f"{path}: {a!r} != {b!r}"]
    return [] if a == b and type(a) is type(b) else [f"{path}: {a!r} != {b!r}"]


def check(label: str, recorded: Path, replayed: Path, skip: tuple[str, ...] = ()) -> None:
    a = json.loads(recorded.read_text(encoding="utf-8"))
    b = json.loads(replayed.read_text(encoding="utf-8"))
    for key in skip:
        a.pop(key, None), b.pop(key, None)
    diffs = same(a, b)
    assert not diffs, f"{label} differs:\n" + "\n".join(diffs[:20])
    print(f"REPRODUCED {label}")


def gcp_checks() -> None:
    assert not os.environ.get("GCP_DRYRUN"), "unset GCP_DRYRUN: verification replays the real fresh tier"
    import gcp
    gcp._require_freeze()
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    assert freeze["not_hashed"] == ["DEVIATIONS.json"] and "research/collaboration_limits_20261013/DEVIATIONS.json" not in freeze["sha256"]
    print("FREEZE", len(freeze["sha256"]), "files match")

    prep = json.loads((HERE / "FRESH_PREPARATION.json").read_text(encoding="utf-8"))
    for name, digest in prep["files"].items():
        assert hashlib.sha256((gcp.FRESH_CACHE / (name + ".npz")).read_bytes()).hexdigest() == digest, name
    for plate in prep["plates"]:
        path = gcp.ET.CACHE / "matrices" / plate["url"].rsplit("/", 1)[1]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == plate["sha256"], plate["url"]
    record = json.loads((HERE / "FRESH_CHOICES.json").read_text(encoding="utf-8"))
    assert record["freeze_sha256"] == hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest()
    assert record["predictions_sha256"] == hashlib.sha256((HERE / "fresh_predictions.npz").read_bytes()).hexdigest()
    print("INPUTS", len(prep["plates"]), "LVL3 plates, 3 normalised tensors, choices bound to the freeze")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        gcp.OUT = work
        gcp.fresh_metadata()
        check("FRESH_METADATA.json", HERE / "FRESH_METADATA.json", work / "FRESH_METADATA.json")
        gcp.fresh_choose()
        check("FRESH_CHOICES.json", HERE / "FRESH_CHOICES.json", work / "FRESH_CHOICES.json", skip=("predictions_sha256",))
        with np.load(HERE / "fresh_predictions.npz") as a, np.load(work / "fresh_predictions.npz") as b:
            assert sorted(a.files) == sorted(b.files)
            for k in a.files:
                assert np.allclose(a[k], b[k], rtol=1e-9, atol=1e-12), k
        print("REPRODUCED fresh_predictions.npz arrays")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in ("FRESH_METADATA.json", "FRESH_CHOICES.json", "fresh_predictions.npz"):
            shutil.copyfile(HERE / name, work / name)
        gcp.OUT = work
        gcp.fresh_evaluate()
        check("FRESH_RESULTS.json", HERE / "FRESH_RESULTS.json", work / "FRESH_RESULTS.json")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        gcp.OUT = work
        gcp.development_decoder()
        check("development_decoder.json", HERE / "development_decoder.json", work / "development_decoder.json")
        gcp.diagnose()
        check("diagnostics_gcp.json", HERE / "diagnostics_gcp.json", work / "diagnostics_gcp.json")
        gcp.donor_information()
        check("donor_information.json", HERE / "donor_information.json", work / "donor_information.json")
    gcp.OUT = HERE
    decoder_parity(gcp, record)


def decoder_parity(gcp, record: dict) -> None:
    """The promoted decoder, fitted from the same reference leave-one-out, makes the frozen decisions."""
    from maestro.endpoint_decision import choose, fit_endpoint_model, signed_hits
    _, refs, queries, ry, rrep, anchors, design, _ = gcp._fresh_inputs()
    base = gcp.deterministic(ry, ry[:, 0])
    cols = np.flatnonzero(base["keep"])
    loo = gcp.reference_loo(ry)["no_agent_model"][:, :, cols]
    truth = ry[:, 1:, cols]
    hits = np.zeros(truth.shape, dtype=int)
    for (i, t), reps in rrep.items():
        if t >= 1:
            hits[i, t - 1] = signed_hits(reps[:, cols], gcp.THRESHOLD)
    assert np.array_equal(hits, gcp.qualifying(ry, rrep, base["keep"])), "hit definitions differ"
    tau = gcp.replicate_sd(rrep, len(refs), cols)
    model = fit_endpoint_model(loo, truth, hits, tau, gcp.replicate_counts(rrep, len(refs)),
                               threshold=gcp.THRESHOLD, draws=gcp.DRAWS, seed=gcp.SEED)
    assert abs(model.shrink - record["b"]) < 1e-12, (model.shrink, record["b"])
    with np.load(HERE / "fresh_predictions.npz") as z:
        assert np.allclose(model.sigma, z["sigma"], rtol=1e-12) and np.allclose(model.tau, z["tau"], rtol=1e-12)
        forecast = z["no_agent_model"]
    platt_gap = float(np.max(np.abs(np.array(model.platt) - np.array(record["platt"]))))
    assert platt_gap < 1e-3, platt_gap                       # Newton here, BFGS in the frozen module
    frozen = record["choices"]["no_agent_model"]["phit"]
    lines = choose(model, forecast, design, per="line")
    assert [[d.target, d.feature, d.sign] for d in lines] == frozen["per_line"]
    assert np.array_equal([d.p_hit for d in lines], frozen["per_line_p"])
    q_gap = float(np.max(np.abs(np.array([d.calibrated for d in lines]) - np.array(frozen["per_line_q"]))))
    assert q_gap < 1e-3, q_gap
    flips = sum((a.calibrated >= .5) != (b >= .5) for a, b in zip(lines, frozen["per_line_q"]))
    assert flips == 0, flips
    best = choose(model, forecast, design, per="query")
    assert [[d.target, d.feature, d.sign] for d in best] == frozen["across_line"]
    print(f"PARITY maestro.endpoint_decision: {len(lines)} per-line and {len(best)} per-query decisions identical, "
          f"P(hit) bit-identical, Platt max gap {platt_gap:.1e}, calibrated max gap {q_gap:.1e}, abstention flips 0")


def l1000_checks() -> None:
    import rkt_limits
    with tempfile.TemporaryDirectory() as tmp:
        rkt_limits.STUDY = Path(tmp)
        for command, name in (("ceiling", "rkt_ceiling.json"), ("curve", "rkt_learning_curve.json"),
                              ("memory", "rkt_memory.json")):
            getattr(rkt_limits, command)()
            check(name, HERE / name, Path(tmp) / name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l1000", action="store_true", help="replay the exploratory L1000 analyses (Python 3.14 env)")
    args = parser.parse_args()
    if args.l1000:
        l1000_checks()
    else:
        gcp_checks()
    print("VERIFIED")


if __name__ == "__main__":
    main()
