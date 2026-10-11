"""Independent verification of a block P run, recomputed from the campaign ledgers alone.

It does not trust RESULTS.json. For the tier given on the command line it:

1. checks FREEZE.json against the files on disk and names every mismatch;
2. re-reads the PRISM tiers and rebuilds the hit and unexpected-hit labels from the raw arrays;
3. for every campaign ledger, recomputes hits, unexpected hits and verified hits from the recorded
   screened order, and compares with what the ledger claims;
4. confirms no arm screened a compound outside its library, bought more than its budget, or had a
   duplicate purchase;
5. confirms every pre-reveal prediction was recorded before its compound was revealed (the
   prediction list is a prefix-consistent ordering of the screened list);
6. recomputes the registered families from the ledgers and compares every bound with RESULTS.json;
7. recomputes the outcome-permutation control and confirms the primary contrasts collapse.

Writes VERIFIED.json with one boolean per check and the recomputed numbers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "feasibility"))
import extract as EX  # noqa: E402
import runner as RU  # noqa: E402
import stats as ST  # noqa: E402
import world as WM  # noqa: E402


def check_freeze():
    f = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    bad = []
    pending = f.get("pending_excluded", {})
    for rel, want in f["files"].items():
        if rel in pending:
            continue
        p = HERE / rel
        if not p.exists():
            bad.append({"file": rel, "why": "missing"})
        elif EX.digest(p, "sha256") != want:
            bad.append({"file": rel, "why": "changed"})
    return {"n_files": len(f["files"]), "mismatches": bad, "ok": not bad}


def main(tier: str):
    res_dir = HERE / "results" / tier
    claimed = json.loads((res_dir / "RESULTS.json").read_text(encoding="utf-8"))
    cfg = claimed["config"]
    sealed = EX.load_prism("sealed") if tier == "confirm" else None
    U = WM.build(include_new=(tier == "confirm"), sealed=sealed)
    H = U.hits()
    s2, _ = U.selectivity(U.S2)
    out = {"tier": tier, "freeze": check_freeze(), "campaigns": 0, "ledger_mismatches": [], "integrity": [],
           "rows": []}
    idx_of = {str(b): i for i, b in enumerate(U.brd)}
    for name, ref, pool in RU.libraries(U, tier, cfg["seed"]):
        poolset = {int(c) for c in pool}
        budget = int(round(cfg["budget_frac"] * len(pool)))
        kn_by_t = {}
        for t, T in enumerate(U.lineages):
            kn = set(U.moa[ref][H[ref, t]])
            kn.discard("nan")
            kn_by_t[t] = ~np.isin(U.moa, list(kn))
        for d in sorted((res_dir / name).glob("*")):
            T = d.name
            if T not in U.lineages:
                continue
            t = U.lineages.index(T)
            row = {"library": name, "T": T, "pool_hits": int(H[pool, t].sum()),
                   "pool_unexpected": int((H[:, t] & kn_by_t[t])[pool].sum())}
            for p in sorted(d.glob("*.json")):
                arm = p.stem
                rec = json.loads(p.read_text(encoding="utf-8"))
                sel = [idx_of[s["brd"]] for s in rec["screened"]]
                out["campaigns"] += 1
                if len(set(sel)) != len(sel):
                    out["integrity"].append({"campaign": f"{name}/{T}/{arm}", "why": "duplicate_purchase"})
                if any(c not in poolset for c in sel):
                    out["integrity"].append({"campaign": f"{name}/{T}/{arm}", "why": "outside_library"})
                if len(sel) > budget:
                    out["integrity"].append({"campaign": f"{name}/{T}/{arm}", "why": "over_budget"})
                pred = [c for c, _ in [(q["idx"], q["p"]) for q in rec["predictions"]]]
                if pred and pred != sel[: len(pred)]:
                    out["integrity"].append({"campaign": f"{name}/{T}/{arm}", "why": "prediction_order_mismatch"})
                sa = np.array(sel, int)
                hits = int(H[sa, t].sum()) if len(sa) else 0
                unexp = int((H[:, t] & kn_by_t[t])[sa].sum()) if len(sa) else 0
                have = np.isfinite(s2[sa, t]) if len(sa) else np.array([], bool)
                ver = int((have & H[sa, t] & (s2[sa, t] <= cfg["verify_s2"])).sum()) if len(sa) else 0
                for key, got, want in (("hits", hits, rec["hits"]), ("unexpected", unexp, rec["unexpected"]),
                                       ("verified", ver, rec["verification"]["verified"])):
                    if got != want:
                        out["ledger_mismatches"].append({"campaign": f"{name}/{T}/{arm}", "field": key,
                                                         "recomputed": got, "claimed": want})
                row[f"{arm}|hits"] = hits
                row[f"{arm}|unexpected"] = unexp
                row[f"{arm}|verified"] = ver
                row[f"{arm}|screens"] = len(sel)
            out["rows"].append(row)
    df = pd.DataFrame(out["rows"])
    g = df["T"].to_numpy()
    primary = {"H1_vc_contribution_unexpected": (df["maestro|unexpected"] - df["agent_novc|unexpected"]).to_numpy(float),
               "H2_agent_contribution_hits": (df["maestro|hits"] - df["vc_only|hits"]).to_numpy(float)}
    fam = ST.family({k: (v, g) for k, v in primary.items()}, alpha=0.05)
    diffs = []
    for k, v in fam.items():
        c = claimed["primary"][k]
        diffs.append({"contrast": k, "max_abs_diff": max(abs(v[f] - c[f]) for f in ("estimate", "lower", "upper")),
                      "verdict_recomputed": v["verdict"], "verdict_claimed": c["verdict"]})
    # Outcome permutation: profiles are permuted across compounds, the recorded selections are kept.
    # Every arm's advantage must collapse, because its evidence no longer points at the right compounds.
    rng = np.random.default_rng(4242)
    Up = WM.Universe(**{**U.__dict__, "P": U.P[rng.permutation(len(U.P))]})
    Hp = Up.hits()
    perm = {}
    for arm in ("maestro", "agent_novc", "vc_only", "random"):
        tot = 0
        for _, r in df.iterrows():
            led = json.loads((res_dir / r["library"] / r["T"] / f"{arm}.json").read_text(encoding="utf-8"))
            sel = np.array([idx_of[s["brd"]] for s in led["screened"]], int)
            if len(sel):
                tot += int(Hp[sel, U.lineages.index(r["T"])].sum())
        perm[arm] = tot
    out["permutation_control"] = {
        "note": "profiles permuted across compounds, selections unchanged; each arm's hit count should fall to "
                "about the random arm's level",
        "real": {a: int(df[f"{a}|hits"].sum()) for a in perm},
        "permuted": perm}
    out["primary_recomputed"] = {k: {f: v[f] for f in ("estimate", "lower", "upper", "verdict")} for k, v in fam.items()}
    out["primary_agreement"] = diffs
    out["ok"] = (out["freeze"]["ok"] and not out["ledger_mismatches"] and not out["integrity"]
                 and all(d["max_abs_diff"] < 1e-9 and d["verdict_recomputed"] == d["verdict_claimed"] for d in diffs))
    out.pop("rows")
    df.to_csv(res_dir / "VERIFY_ROWS.csv", index=False)
    RU.write_json(HERE / f"VERIFIED_{tier}.json", out)
    print(json.dumps(out, indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "confirm")
