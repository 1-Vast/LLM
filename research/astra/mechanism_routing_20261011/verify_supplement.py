"""Post-freeze supplementary verification (written after VERIFIED.json reported one failed check).

The frozen check ``recomputed_contrasts_match`` (verify.py) failed: it compares every field with
an absolute tolerance of 1e-9, including the descriptive share of drugs with a negative
difference. ROWS_killers.csv stores floats to about 16 significant digits. A drug whose two arms
differed only in the last bits in memory becomes an exact tie after the round trip, which moves
one drug in ``share_negative``.

This script reruns the same recomputation and reports two things:
1. Do the estimates, both intervals and every verdict and headline match RESULTS.json
   (tolerance 1e-12)?
2. Is every mismatching ``share_*`` field explained by pairs that tie in the CSV?

It does not replace VERIFIED.json, which stays as written. Output: VERIFIED_SUPPLEMENT.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as EV  # noqa: E402


def main() -> dict:
    R = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    K = pd.read_csv(HERE / "ROWS_killers.csv")
    T = pd.read_csv(HERE / "ROWS_trust.csv")
    P = EV.protocol()
    cons = json.loads(json.dumps(EV.contrasts(K, T, P, with_llm=True)))
    dec = json.loads(json.dumps(EV.decide(cons, P)))
    numeric, shares = {}, {}
    for cid, rec in cons.items():
        orig = R["contrasts"][cid]
        dev = max(abs(rec["estimate"] - orig["estimate"]),
                  *(abs(a - b) for key in ("ci95", "ci_family") for a, b in zip(rec[key], orig[key])))
        numeric[cid] = dev
        for key in ("share_positive", "share_negative"):
            if key in rec and rec[key] != orig[key]:
                c = next(x for x in P["contrasts"] if x["id"] == cid)
                ties = int((K[c["a"]] == K[c["b"]]).sum())
                shares[f"{cid}:{key}"] = {"recomputed": rec[key], "results": orig[key],
                                          "drugs_moved": round(abs(rec[key] - orig[key]) * rec["n"], 6),
                                          "exact_ties_in_csv": ties}
    verdicts_match = all(dec[k]["verdict"] == R["decisions"][k]["verdict"] for k in dec if k != "headline")
    out = {"post_freeze": True, "reason": "frozen check recomputed_contrasts_match failed on a descriptive share field",
           "max_abs_numeric_deviation": max(numeric.values()), "numeric_ok": max(numeric.values()) < 1e-12,
           "verdicts_match": verdicts_match, "headline_match": dec["headline"] == R["decisions"]["headline"],
           "share_mismatches": shares,
           "shares_explained_by_csv_ties": all(v["drugs_moved"] <= v["exact_ties_in_csv"] and
                                               float(v["drugs_moved"]).is_integer() for v in shares.values())}
    out["ok"] = out["numeric_ok"] and out["verdicts_match"] and out["headline_match"] and out["shares_explained_by_csv_ties"]
    (HERE / "VERIFIED_SUPPLEMENT.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
