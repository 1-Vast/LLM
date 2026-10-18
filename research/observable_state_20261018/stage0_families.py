"""Stage 0 (labels and fingerprints only): eligible MoA families with a within-family chemical split, and lineage groups.

File summary
- Path: research/observable_state_20261018/stage0_families.py
- Reads `family`, `fold`, `cores`, `fp` (ECFP4 bits), `lineage` from the cached tables. It never reads `Y`, events, missingness
  or any outcome; eligibility therefore cannot depend on how active a family is.
- Within-family split: compounds are linked when ECFP4 Tanimoto >= 0.5; connected components are assigned whole, by a salted
  hash, to `search` or `heldout` until the held-out side holds about 40% of the family. Every search-heldout pair is therefore
  below 0.5 by construction (verified and recorded).
- Eligible family: >= MIN_SEARCH search and >= MIN_HELD held-out compounds.
- Lineage groups: the 21 lineages are split by a salted hash into search lineages (14) and held-out lineages (7).
- Writes STAGE0.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "feedback_propagation_20261018"))
import bench  # noqa: E402

tc = bench.tc
SEP = 0.5
HELD_SHARE = 0.4
MIN_SEARCH, MIN_HELD = 4, 3
SALT = "obs-state-stage0"
N_HELD_LINEAGES = 7


def components(sim, thr):
    n = len(sim)
    seen = np.full(n, -1)
    c = 0
    for s in range(n):
        if seen[s] >= 0:
            continue
        stack = [s]
        seen[s] = c
        while stack:
            v = stack.pop()
            for w in np.where((sim[v] >= thr) & (seen < 0))[0]:
                seen[w] = c
                stack.append(w)
        c += 1
    return seen


def split_family(T, f):
    """(search_idx, heldout_idx) for family f under the Stage-0 rule, or None if the family is too small / unbalanced."""

    fam, fp, cores = T["family"], T["fp"], T["cores"]
    idx = np.where(fam == f)[0]
    n = len(idx)
    if n < MIN_SEARCH + MIN_HELD:
        return None
    sim = tc.tanimoto(fp[idx], fp[idx])
    comp = components(sim, SEP)
    order = sorted(set(comp.tolist()), key=lambda k: tc.h(min(str(c) for c in cores[idx[comp == k]]), SALT))
    target = int(np.ceil(HELD_SHARE * n))
    held_c, nh = [], 0
    for k in order:
        if nh >= target:
            break
        held_c.append(k)
        nh += int((comp == k).sum())
    held = np.isin(comp, held_c)
    if (~held).sum() < MIN_SEARCH or held.sum() < MIN_HELD:
        return None
    return idx[~held], idx[held]


def lineage_split(T):
    lin = sorted(set(map(str, T["lineage"])))
    held_l = sorted(sorted(lin, key=lambda l: tc.h(l, SALT + "-lineage"))[:N_HELD_LINEAGES])
    return held_l, np.isin(T["lineage"].astype(str), held_l)


def main() -> dict:
    T = bench.load_tables()
    fam, fp, cores, fold = T["family"], T["fp"], T["cores"], T["fold"]
    rows = []
    for f in sorted(set(fam.tolist())):
        idx = np.where(fam == f)[0]
        n = len(idx)
        if n < MIN_SEARCH + MIN_HELD:
            rows.append({"family": f, "n": n, "eligible": False, "reason": "too_small"})
            continue
        sim = tc.tanimoto(fp[idx], fp[idx])
        comp = components(sim, SEP)
        order = sorted(set(comp.tolist()), key=lambda k: tc.h(min(str(c) for c in cores[idx[comp == k]]), SALT))
        target = int(np.ceil(HELD_SHARE * n))
        held_c, nh = [], 0
        for k in order:
            if nh >= target:
                break
            held_c.append(k)
            nh += int((comp == k).sum())
        held = np.isin(comp, held_c)
        cross = float(sim[np.ix_(held, ~held)].max()) if held.any() and (~held).any() else 0.0
        ns, nhd = int((~held).sum()), int(held.sum())
        ok = ns >= MIN_SEARCH and nhd >= MIN_HELD
        rows.append({"family": f, "fold": int(fold[idx[0]]), "n": n, "components": int(len(order)), "n_search": ns, "n_heldout": nhd,
                     "max_cross_similarity": cross, "eligible": bool(ok), "reason": "" if ok else "split_too_unbalanced"})
    elig = [r for r in rows if r["eligible"]]
    assert all(r["max_cross_similarity"] < SEP for r in elig)
    lin = sorted(set(map(str, T["lineage"])))
    ordl = sorted(lin, key=lambda l: tc.h(l, SALT + "-lineage"))
    held_l = sorted(ordl[:N_HELD_LINEAGES])
    lines_per = {l: int((T["lineage"].astype(str) == l).sum()) for l in lin}
    out = {
        "scope": "labels and ECFP4 fingerprints only; no outcome, activity or missingness was read",
        "parameters": {"separation": SEP, "held_share": HELD_SHARE, "min_search": MIN_SEARCH, "min_heldout": MIN_HELD, "salt": SALT},
        "families_total": len(rows), "families_eligible": len(elig),
        "eligible_by_min_total_size": {str(m): sum(1 for r in elig if r["n"] >= m) for m in (7, 10, 15, 20)},
        "eligible_compounds": {"search": sum(r["n_search"] for r in elig), "heldout": sum(r["n_heldout"] for r in elig)},
        "eligible_by_fold": {str(k): sum(1 for r in elig if r["fold"] == k) for k in range(5)},
        "stop_rule_80_families": "PASS" if len(elig) >= 80 else "STOP",
        "lineages": {"search": sorted(set(lin) - set(held_l)), "heldout": held_l, "lines_per_lineage": lines_per,
                     "lines_search": int(sum(v for k, v in lines_per.items() if k not in held_l)),
                     "lines_heldout": int(sum(lines_per[k] for k in held_l))},
        "caveats": ["eligibility ignores activity by design; large families are mostly receptor classes whose cytotoxic content is unknown without outcomes",
                    "comparator family F' is every other-family compound in the same fold, NOT purged against the held-out compounds (to be fixed in the contract)",
                    "lineage group sizes are line counts, not independent biological units"],
        "families": rows,
    }
    (HERE / "STAGE0.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    print({k: v for k, v in o.items() if k not in ("families", "lineages")})
    print(o["lineages"]["heldout"], o["lineages"]["lines_search"], o["lineages"]["lines_heldout"])
