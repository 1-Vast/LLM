"""Audit of the action-substitution study (read-only on its records): entities, family definitions, evaluable coverage,
replicate independence, decision confusion at epsilon 0.03, refinement threshold arithmetic. Writes AUDIT.json (overwrites).
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AS = HERE.parent / "action_substitution_20261019"
sys.path.insert(0, str(AS))
import cas_data as D  # noqa: E402

EPS = 0.03


def main():
    census = json.loads((AS / "CENSUS.json").read_text(encoding="utf-8"))
    dr = census["drugs"]
    out = {}
    # 1. entities
    names = {i: d["name"] for i, d in dr.items()}
    out["entities"] = dict(
        n=len(names),
        composite=[n for n in names.values() if "|" in n],
        code_names=[n for n in names.values() if any(ch.isdigit() for ch in n) and "-" in n][:40],
        generic_label=[n for n in names.values() if "inhibitor" in n.lower()],
        note="Only 'Afatinib|Trametinib' is a multi-agent entry; 'Wee1 Inhibitor' is a generic label (GDSC compound), "
             "'Nutlin-3a (-)' a stereo-specified name. No salt/alias duplicates found by name.")
    # validation-screen spelling of the composite differs ('Afatinib | Trametinib')
    val = D.design("validation")
    out["entities"]["validation_composites"] = sorted({n for n in set(val.ANCHOR_NAME) | set(val.LIBRARY_NAME) if "|" in n})
    # 2. family definitions among non-composite drugs
    ids = [i for i in dr if "|" not in names[i]]
    ts = {i: D.target_set(dr[i]["target"]) for i in ids}
    primary = {i: (dr[i]["target"].split(",")[0].strip().upper() if isinstance(dr[i]["target"], str) else "") for i in ids}
    pw = {i: dr[i]["pathway"] for i in ids}
    defs = {"any_target_overlap": lambda a, b: bool(ts[a] & ts[b]),
            "exact_target_set": lambda a, b: bool(ts[a]) and ts[a] == ts[b],
            "same_primary_target": lambda a, b: bool(primary[a]) and primary[a] == primary[b],
            "jaccard_ge_0.5": lambda a, b: len(ts[a] | ts[b]) > 0 and len(ts[a] & ts[b]) / len(ts[a] | ts[b]) >= 0.5,
            "same_pathway": lambda a, b: pw[a] == pw[b]}
    fam = {}
    for k, f in defs.items():
        pairs = [(names[a], names[b]) for a, b in itertools.combinations(sorted(ids), 2) if f(a, b)]
        fam[k] = dict(n_pairs=len(pairs), pairs=pairs if len(pairs) <= 40 else pairs[:40])
    out["family_definitions"] = fam
    # 3. evaluable coverage of the 37 implementations (phase 2)
    lofo = json.loads((AS / "LOFO_SYNERGY_DELTA_AUC.json").read_text(encoding="utf-8"))
    folds = lofo["folds"]
    ev = {k: v["cells"] for k, v in folds.items()}
    out["coverage"] = dict(candidates=len(ev), evaluable=sum(1 for v in ev.values() if v > 0),
                           not_evaluable=sorted(k for k, v in ev.items() if v == 0),
                           reason="no sibling measured with the same partner (and concentration/rank) in the same line")
    tid = {names[i]: i for i in ids}
    out["coverage"]["not_evaluable_detail"] = {k: dict(target=dr[tid[k]]["target"], pathway=dr[tid[k]]["pathway"])
                                               for k in out["coverage"]["not_evaluable"] if k in tid}
    # 4. replicate independence
    p = pd.read_csv(AS / "cache/plates.csv")
    per_line = p.groupby("CELL_LINE_NAME").agg(dates=("DATE_CREATED", "nunique"), cell_ids=("CELL_ID", "nunique"),
                                               master=("MASTER_CELL_ID", "nunique"), projects=("RESEARCH_PROJECT", "nunique"))
    multi = per_line[per_line.dates > 1]
    out["replicates"] = dict(
        lines=int(len(per_line)), lines_multi_date=int(len(multi)),
        median_dates=float(multi.dates.median()), lines_with_one_cell_id=int((multi.cell_ids == 1).sum()),
        lines_with_two_projects=int((multi.projects == 2).sum()),
        cell_id_per_date=int(p.groupby(["CELL_LINE_NAME", "DATE_CREATED"]).CELL_ID.nunique().max()),
        interpretation="Different DATE_CREATED values are separate seeding/treatment events (scan about 4 days later), but "
                       "almost every line used a single CELL_ID stock across all dates; some lines span two campaigns "
                       "(e.g. GDSC_Breast vs GDSC_Breast-2). They are replicate assays from a shared cell stock, not "
                       "independent biological preparations, and not independent confirmation.")
    # 5. decision confusion at eps 0.03 (phase 2 unit tables)
    conf = {}
    for ep in ("SYNERGY_DELTA_AUC", "SYNERGY_OBS_AUC"):
        u = pd.read_csv(AS / f"lofo_units_{ep}.csv")
        fail = (u.obs.abs() > EPS).to_numpy()
        row = dict(n=int(len(u)), prevalence_fail=float(fail.mean()))
        for m in ("B0", "B1", "B2", "B4", "B5", "M"):
            pred = (u["d_" + m].abs() > EPS).to_numpy()
            tp, fp = int((pred & fail).sum()), int((pred & ~fail).sum())
            fn, tn = int((~pred & fail).sum()), int((~pred & ~fail).sum())
            row[m] = dict(tp=tp, fp=fp, fn=fn, tn=tn, sensitivity=tp / max(tp + fn, 1), specificity=tn / max(tn + fp, 1),
                          balanced_acc=0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)), acc=(tp + tn) / len(u))
        conf[ep] = row
    out["decision_confusion_eps0.03"] = conf
    # 6. refinement threshold arithmetic
    ref = json.loads((AS / "REFINE_SYNERGY_DELTA_AUC.json").read_text(encoding="utf-8"))
    w = np.array([v["w"] for v in ref["folds"].values()])
    out["refinement_threshold"] = dict(w_min=float(w.min()), w_median=float(np.median(w)), w_max=float(w.max()),
                                       probe_residual_needed_from_zero_prior=float(EPS / np.median(w)),
                                       cell_sd=float(np.sqrt(np.median([v["sigma_w2"] for v in ref["folds"].values()]))),
                                       partner_sd=float(np.sqrt(np.median([v["tau2"] for v in ref["folds"].values()]))))
    (HERE / "AUDIT.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "family_definitions"}, indent=1)[:6000])
    print({k: v["n_pairs"] for k, v in fam.items()})
    print("exact:", fam["exact_target_set"]["pairs"])
    print("primary:", fam["same_primary_target"]["pairs"])


if __name__ == "__main__":
    main()
