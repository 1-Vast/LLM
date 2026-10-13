"""Post hoc analyses, computed after the one-shot opening: no confirmatory claim (see DEVIATIONS.json).

File summary
- Path: research/selective_hit_triage_20261013/posthoc.py
- Purpose: answer three questions the registered analyses left open, on the registered endpoint
  (evaluate_registered.registered_outcomes).
  1. Strong non-agentic learners versus the MAESTRO arms. The success criterion compares against
     strong non-agentic workflows, but the registered primaries used the deterministic D3. Learner
     arms buy no secondary, so cost is reported alongside hits.
  2. Why test transfer is weaker than development. Per split:
     - per-compound PRISM-to-CTRP Spearman correlation;
     - validated rate among screen-selective pairs;
     - share of validated pairs in the largest MoA family.
  3. Compound identity: CTRP compound names versus census names. A mismatch counts as a synonym only
     when the census matched the pair by Broad core id or InChIKey connectivity.
- Core points:
  - Contrasts use the frozen `evaluate.contrast` (compound sign-flip, bootstrap CI).
  - Write-once: POSTHOC.json; a rerun must reproduce it.
- Interfaces: `main`.
"""
from __future__ import annotations

import io
import json
import re
import zipfile

import numpy as np
from scipy.stats import spearmanr

from arms import load_table
from census import CTRP_ZIP, HERE
from dev import labels
from evaluate import Truth, contrast, flat
from evaluate_registered import registered_outcomes
from outcomes import qualified_outcomes, require_freeze
from test_choose import load_choices

TARGET = HERE / "POSTHOC.json"
LEARNERS = ("ML", "VC", "ML+context")
ENGINES = ("MAESTRO", "MAESTRO_LOOP")


def learners_vs_engines(truth: Truth, choices: dict) -> dict:
    out = {}
    for b, arms in choices["arms"].items():
        for a in LEARNERS:
            for e in ENGINES:
                c = contrast(truth, flat(arms[a]), flat(arms[e]))
                c["secondaries_bought"] = {a: sum(len(x.get("bought", [])) for x in arms[a]["campaigns"]),
                                           e: sum(len(x.get("bought", [])) for x in arms[e]["campaigns"])}
                out[f"{b}:{a}-{e}"] = c
    return out


def split_transfer(t: dict, test_outcomes: dict) -> dict:
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    out = {}
    for role, outcomes in (("development", qualified_outcomes("development")), ("test", test_outcomes)):
        rows = np.flatnonzero(t["role"] == role)
        y, ev, _ = labels(t, rows, outcomes)
        zr, core = t["z_r"][rows], t["core"][rows]
        rhos = []
        for c in sorted(set(core)):
            lines = outcomes[c]["lines"]
            pairs = [(zr[k], lines[t["line"][rows][k]]["auc_z"]) for k in np.flatnonzero(core == c) if t["line"][rows][k] in lines]
            a, b = np.array(pairs).T
            rhos.append(float(spearmanr(a, b).statistic))
        rate = {}
        for thr in (-2.0, -3.0, -4.0):
            m = ev & (zr <= thr)
            rate[str(thr)] = {"pairs": int(m.sum()), "validated_rate": float(y[m].mean()), "compounds": len(set(core[m]))}
        m = ev & (zr <= -3.0) & y
        fams: dict = {}
        for c in core[m]:
            fams[split["family"][c]] = fams.get(split["family"][c], 0) + 1
        top = max(fams.items(), key=lambda x: x[1]) if fams else (None, 0)
        out[role] = {"compounds": len(rhos), "median_spearman_zr_vs_ctrp_auc_z": float(np.median(rhos)),
                     "fraction_spearman_above_0.1": float(np.mean(np.array(rhos) > 0.1)),
                     "fraction_spearman_below_-0.1": float(np.mean(np.array(rhos) < -0.1)),
                     "validated_rate_by_screen_z": rate,
                     "largest_family_share_of_validated_z_le_-3": {"family": top[0], "validated": top[1],
                                                                   "of": int(m.sum()), "share": top[1] / max(1, int(m.sum())),
                                                                   "family_members": sum(1 for v in split["family"].values() if v == top[0])}}
    return out


def identity_audit() -> dict:
    import pandas as pd
    z = zipfile.ZipFile(CTRP_ZIP)
    meta = pd.read_csv(io.BytesIO(z.read("v20.meta.per_compound.txt")), sep="\t", encoding="latin-1")
    name = dict(zip(meta["master_cpd_id"].astype(int), meta["cpd_name"]))
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    role = {c: r for r in ("development", "test") for c in split[r]}
    census = [r for r in json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))["compounds"] if r["core"] in role]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())  # noqa: E731
    differ = [{"role": role[r["core"]], "census": r["name"], "ctrp": name[int(r["ctrp_master_cpd_id"])], "match": r["match"]}
              for r in census if norm(r["name"]) != norm(name[int(r["ctrp_master_cpd_id"])])]
    ids = [int(r["ctrp_master_cpd_id"]) for r in census]
    return {"compounds": len(census), "match_rule": {m: sum(r["match"] == m for r in census) for m in sorted({r["match"] for r in census})},
            "name_differs": differ, "name_differs_count": len(differ),
            "structure_matched": all(d["match"] in ("broad_core", "inchikey_connectivity") for d in differ),
            "duplicate_ctrp_ids": len(ids) - len(set(ids)),
            "stereo_caveat": [d for d in differ if d["match"] == "inchikey_connectivity" and "iso" in norm(d["ctrp"]) + norm(d["census"])]}


def main() -> None:
    require_freeze()
    choices = load_choices()
    t = load_table()
    outcomes, _ = registered_outcomes("test")
    truth = Truth(t, outcomes)
    res = {"label": "POST HOC (after the one-shot opening; registered endpoint; no confirmatory claim)",
           "learners_vs_engines": learners_vs_engines(truth, choices),
           "split_transfer": split_transfer(t, outcomes),
           "identity_audit": identity_audit()}
    text = json.dumps(res, indent=1) + "\n"
    if TARGET.exists():
        if TARGET.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            raise SystemExit("RESULTS_MISMATCH: recomputed results differ from POSTHOC.json")
        print("REPRODUCED POSTHOC.json")
    else:
        TARGET.write_bytes(text.encode())
        print("WROTE POSTHOC.json")


if __name__ == "__main__":
    main()
