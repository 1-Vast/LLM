"""Stage 4: per-group observed responses from extracted rows (no models, no printing of values).

Held-out contexts: every statistic comes from stored raw rows.
  treated group g on plate p: n, mean, per-gene variance, and the two hash halves' means;
  reference controls on p: the 'reference' half of DMSO rows (never STATE's basal input),
  with its own hash halves for split-half reliability.
Training contexts: treated summaries from extraction plus reference-half DMSO rows.
Only full-QC rows are used. Outputs are arrays keyed by (label, plate); the study's
analysis guard decides which contexts may be scored.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from remote import CACHE  # noqa: E402

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"


def _plan(file):
    return json.loads((CACHE / "extract" / "plans" / f"{file}.plan.json").read_text(encoding="utf-8"))


def _stats(x):
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    mean = x.mean(0) if n else np.full(2000, np.nan)
    var = x.var(0, ddof=1) if n > 1 else np.full(2000, np.nan)
    return n, mean, var


def build(file: str, role: str) -> Path:
    target = CACHE / "observations" / f"{file}.npz"
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    plan = _plan(file)
    rows = np.load(CACHE / "extract" / file / "rows.npy", mmap_mode="r")
    slots = np.load(CACHE / "extract" / file / "slots.npz")
    start = dict(zip(slots["group"].tolist(), slots["start"].tolist()))
    controls = {}
    for g in plan["groups"]:
        if not g["control"]:
            continue
        block = np.asarray(rows[start[g["group"]]:start[g["group"]] + len(g["rows"])], dtype=np.float64)
        full = np.asarray(g["full"], bool)
        ref = full & (np.asarray(g["control_role"]) == "reference")
        basal = full & (np.asarray(g["control_role"]) == "basal")
        half = np.asarray(g["half"])
        n, mean, var = _stats(block[ref])
        controls[g["plate"]] = {"n": n, "mean": mean, "var": var,
                                "meanA": block[ref & (half == "A")].mean(0), "nA": int((ref & (half == "A")).sum()),
                                "meanB": block[ref & (half == "B")].mean(0), "nB": int((ref & (half == "B")).sum()),
                                "basal_mean": block[basal].mean(0), "basal_n": int(basal.sum()),
                                "available_full": g["available_full_rows"]}
    treated = [g for g in plan["groups"] if not g["control"] and g["plate"] in controls]
    out = {"label": [], "plate": [], "n": [], "mean": [], "var": [], "meanA": [], "meanB": [], "nA": [], "nB": [],
           "available_full": []}
    if role == "heldout":
        for g in treated:
            block = np.asarray(rows[start[g["group"]]:start[g["group"]] + len(g["rows"])], dtype=np.float64)
            full = np.asarray(g["full"], bool)
            half = np.asarray(g["half"])
            n, mean, var = _stats(block[full])
            a, b = full & (half == "A"), full & (half == "B")
            out["meanA"].append(block[a].mean(0) if a.any() else np.full(2000, np.nan))
            out["meanB"].append(block[b].mean(0) if b.any() else np.full(2000, np.nan))
            out["nA"].append(int(a.sum())); out["nB"].append(int(b.sum()))
            out["label"].append(g["label"]); out["plate"].append(g["plate"]); out["n"].append(n)
            out["mean"].append(mean); out["var"].append(var); out["available_full"].append(g["available_full_rows"])
    else:
        summary = np.load(CACHE / "extract" / file / "treated_summaries.npz")
        index = {int(k): i for i, k in enumerate(summary["group"])}
        for g in treated:
            i = index[g["group"]]
            out["label"].append(g["label"]); out["plate"].append(g["plate"]); out["n"].append(int(summary["n"][i]))
            out["mean"].append(summary["mean"][i].astype(np.float64)); out["var"].append(summary["var"][i].astype(np.float64))
            out["meanA"].append(np.full(2000, np.nan)); out["meanB"].append(np.full(2000, np.nan))
            out["nA"].append(0); out["nB"].append(0); out["available_full"].append(g["available_full_rows"])
    plates = sorted(controls)
    np.savez(target, label=np.array(out["label"]), plate=np.array(out["plate"]), n=np.array(out["n"]),
             mean=np.array(out["mean"], dtype=np.float32), var=np.array(out["var"], dtype=np.float32),
             meanA=np.array(out["meanA"], dtype=np.float32), meanB=np.array(out["meanB"], dtype=np.float32),
             nA=np.array(out["nA"]), nB=np.array(out["nB"]), available_full=np.array(out["available_full"]),
             ctrl_plate=np.array(plates), ctrl_n=np.array([controls[p]["n"] for p in plates]),
             ctrl_mean=np.array([controls[p]["mean"] for p in plates], dtype=np.float32),
             ctrl_var=np.array([controls[p]["var"] for p in plates], dtype=np.float32),
             ctrl_meanA=np.array([controls[p]["meanA"] for p in plates], dtype=np.float32),
             ctrl_meanB=np.array([controls[p]["meanB"] for p in plates], dtype=np.float32),
             ctrl_nA=np.array([controls[p]["nA"] for p in plates]), ctrl_nB=np.array([controls[p]["nB"] for p in plates]),
             basal_mean=np.array([controls[p]["basal_mean"] for p in plates], dtype=np.float32),
             basal_n=np.array([controls[p]["basal_n"] for p in plates]),
             ctrl_available_full=np.array([controls[p]["available_full"] for p in plates]))
    receipt = {"file": file, "role": role, "groups": len(out["label"]), "plates": plates,
               "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "values_printed": False}
    (HERE / "observations").mkdir(exist_ok=True)
    (HERE / "observations" / f"{file}.receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return target


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--role", choices=["heldout", "train"], required=True)
    args = parser.parse_args()
    for f in args.files:
        print(build(f, args.role), flush=True)
