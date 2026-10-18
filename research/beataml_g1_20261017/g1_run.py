"""Run gate G1 once: per-sample totals for every arm, the inner choice of k, and the parity record.

File summary
- Path: research/beataml_g1_20261017/g1_run.py
- Purpose: write ``records/records.json`` (write-once) from the frozen arms. The run refuses to start unless
  FREEZE.json matches, and stops with PARITY_FAILED, writing nothing, if the low-rank arms do not reproduce
  the attribution study's records or `strong_state`'s S_ridge probabilities (PROTOCOL.md section 7).
- Interfaces: ``python g1_run.py`` (full run), ``python g1_run.py --reference`` (copy the parity reference
  once, before the freeze), ``python g1_run.py --parity-fold N`` (compare only the arms the attribution
  study already computed on fold N; it prints no G1 contrast).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1_arms as A  # noqa: E402
import seal  # noqa: E402
from common import CACHE, DOMAIN_CACHE, load_domain, outer_folds, sha256, write_json  # noqa: E402

REF = HERE / "records" / "parity_reference.json"
OUT = HERE / "records" / "records.json"
PRIMARY = CACHE / "records_primary.json"
PROBES_VC = CACHE / "records_probes_vc.json"
N_FOLDS = 5


def build_reference() -> None:
    if REF.exists():
        raise SystemExit("parity_reference.json exists; write-once")
    prim = {r["context"]: r for r in json.loads(PRIMARY.read_text(encoding="utf-8"))}
    pvc = {r["context"]: r for r in json.loads(PROBES_VC.read_text(encoding="utf-8"))}
    rows = [{"context": c, "fold": prim[c]["fold"], "t_vc0_coh": prim[c]["t_vc0_coh"], "t_x4_coh": prim[c]["t_x4_coh"],
             "t_x8_coh": prim[c]["t_x8_coh"], "E_total": pvc[c]["probe_hits"] + pvc[c]["h_D"]} for c in prim]
    write_json(REF, {"source": "research/feedback_attribution_20261017 caches (tmp/, git-ignored)",
                     "records_primary_sha256": sha256(PRIMARY), "records_probes_vc_sha256": sha256(PROBES_VC),
                     "rows": rows})
    print("written", REF.name, len(rows), "rows")


def compare(recs: list[dict]) -> dict:
    ref = {r["context"]: r for r in json.loads(REF.read_text(encoding="utf-8"))["rows"]}
    pairs = {"C0": "t_vc0_coh", "C_4": "t_x4_coh", "C_8": "t_x8_coh", "E": "E_total"}
    bad = {a: [r["context"] for r in recs if r["t_" + a] != ref[r["context"]][col]] for a, col in pairs.items()}
    return {"samples": len(recs), "mismatches": {a: v[:5] for a, v in bad.items() if v}, "all_match": not any(bad.values())}


def ridge_probability_parity(d: dict, src: np.ndarray, tgt: np.ndarray) -> bool:
    from attribution import strong_state
    from virtual_cell.bridged_transfer import BridgedTransferModel
    model = BridgedTransferModel(rank=A.RANK, abs_gate=None, min_measured=A.MIN_MEASURED,
                                 impute_iters=A.IMPUTE).fit(d["Y"][src], d["X"][src])
    mine = A.ridge_parts(d, src, tgt, model)["prob"]
    return bool(np.array_equal(mine, strong_state(d, src, tgt, model, gbm=False)["S_ridge"]))


def parity_fold(fold: int) -> None:
    d = load_domain()
    fid = outer_folds(d["groups"])
    src, tgt = np.flatnonzero(fid != fold), np.flatnonzero(fid == fold)
    res = compare(A.evaluate(d, src, tgt, arms="parity"))
    res["S_ridge_probabilities_equal_strong_state"] = ridge_probability_parity(d, src, tgt)
    print(json.dumps({"fold": fold, **res}))


def main() -> None:
    seal.check()
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; the G1 run is write-once")
    t0 = time.time()
    d = load_domain()
    fid = outer_folds(d["groups"])
    recs, choices, ridge_ok = [], {}, {}
    for k in range(N_FOLDS):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        choice = A.choose_k(d, src, k)
        if choice["inner_patient_overlap"]:
            raise SystemExit("INNER_FOLDS_NOT_PATIENT_DISJOINT")
        choices[k] = choice
        recs += A.assemble(d, k, src, tgt, choice)
        ridge_ok[k] = ridge_probability_parity(d, src, tgt)
        print(f"fold {k}: {len(tgt)} targets, k_cand {choice['k_candidate']}, k_rf {choice['k_ridge_feedback']}, "
              f"ridge parity {ridge_ok[k]}, {time.time() - t0:.0f} s", flush=True)
    parity = compare(recs)
    parity["S_ridge_probabilities_equal_strong_state"] = ridge_ok
    if not parity["all_match"] or not all(ridge_ok.values()):
        raise SystemExit(f"PARITY_FAILED: {json.dumps(parity)}")
    seal.record_access()
    write_json(OUT, {"meta": {"freeze_sha256": seal.lf_digest(HERE / "FREEZE.json"), "domain_cache_sha256": sha256(DOMAIN_CACHE),
                              "constants": {"budget": A.BUDGET, "ks": list(A.KS), "rank": A.RANK, "inner_folds": A.INNER_FOLDS,
                                            "lambda_rf": A.LAMBDA_RF, "lambda_alt": A.LAMBDA_ALT},
                              "choices": choices, "parity": parity, "seconds": time.time() - t0},
                     "records": recs})
    print("written", OUT.name, len(recs), "samples,", f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    if sys.argv[1:] == ["--reference"]:
        build_reference()
    elif sys.argv[1:2] == ["--parity-fold"]:
        parity_fold(int(sys.argv[2]))
    else:
        main()
