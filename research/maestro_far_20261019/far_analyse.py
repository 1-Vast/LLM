"""Family-cluster bootstrap contrasts on records_<stage>.npz. Usage: python far_analyse.py <stage> [metric=U|hits]. Prints and writes CONTRASTS_<stage>.json."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
DRAWS, SEED = 4000, 20261019


def load(stage, metric):
    z = np.load(HERE / f"records_{stage}.npz")
    folds = sorted({int(k.split("|")[0]) for k in z.files})
    suffix = "|hits" if metric == "hits" else ""
    cond = sorted({tuple(k.split("|")[1:3]) for k in z.files if len(k.split("|")) >= 3 and k.split("|")[1] != "fam"})
    return z, folds, suffix, cond


def stat(z, folds, a, suffix, fam_w):
    """mean over folds of sum_q w_family(q) * contrib_q (w = bootstrap multiplicity)."""
    return np.mean([(fam_w[f] * z[f"{f}|{a[0]}|{a[1]}{suffix}"]).sum() for f in folds])


def contrast(stage, A, B, metric="U"):
    z, folds, suffix, _ = load(stage, metric)
    fams = {f: z[f"{f}|fam"] for f in folds}
    rng = np.random.default_rng(SEED)
    ones = {f: np.ones(len(fams[f])) for f in folds}
    obs = stat(z, folds, A, suffix, ones) - stat(z, folds, B, suffix, ones)
    d = []
    uf = {f: np.unique(fams[f]) for f in folds}
    for _ in range(DRAWS):
        w = {}
        for f in folds:
            m = dict(zip(*np.unique(rng.choice(uf[f], len(uf[f])), return_counts=True)))
            w[f] = np.array([m.get(x, 0) for x in fams[f]], float)
        d.append(stat(z, folds, A, suffix, w) - stat(z, folds, B, suffix, w))
    d = np.array(d)
    return {"diff": float(obs), "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))], "lcb95_one_sided": float(np.percentile(d, 5))}


if __name__ == "__main__":
    stage = sys.argv[1]; metric = sys.argv[2] if len(sys.argv) > 2 else "U"
    z, folds, suffix, cond = load(stage, metric)
    ones = {f: np.ones(len(z[f"{f}|fam"])) for f in folds}
    levels = {f"{p}|{r}": round(float(stat(z, folds, (p, r), suffix, ones)), 4) for p, r in cond}
    print("levels", json.dumps(levels, indent=0))
    R = "fuse" if stage == "search" else "gate"
    P = lambda p, r=R: (p, r)
    pairs = [(P("far"), P("random")), (P("far"), P("exploit")), (P("far"), P("coverage")), (P("far"), P("poh")), (P("far2"), P("random")), (P("far2"), P("exploit")),
             (P("far2"), P("poh")), (P("poh"), P("random")), (P("exploit"), P("none")), (P("random"), P("none")), (P("all"), P("random")), (P("oracle_split"), P("random")),
             (P("far"), ("far", "none")), (P("far"), ("far", "fuse")), (("far", "resid"), P("far")), (("far", "abstain"), P("far"))]
    pairs = [(A, B) for A, B in pairs if all(f"{folds[0]}|{x[0]}|{x[1]}" in z.files for x in (A, B))]
    out = {"metric": metric, "levels": levels, "contrasts": {}}
    for A, B in pairs:
        r = contrast(stage, A, B, metric); out["contrasts"][f"{A[0]}.{A[1]}-{B[0]}.{B[1]}"] = r
        print(f"{A[0]}.{A[1]} - {B[0]}.{B[1]}: {r['diff']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]")
    (HERE / f"CONTRASTS_{stage}_{metric}.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
