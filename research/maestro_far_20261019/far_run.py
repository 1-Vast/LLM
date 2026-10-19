"""Run a FAR stage: search | select | test. Writes records_<stage>.npz and ATLAS_<stage>.json. Usage: python far_run.py <stage> [--seed N]

search : folds 0,1. Builds the failure atlas, fits the failure model (logistic on pre-assay signatures) and tau (median top-similarity), prints policy scales.
select : fold 2. Uses MODEL.json / tau from search. Gate decisions are read from these outcomes, nothing else is tuned afterwards.
test   : folds 3,4. Refuses unless FREEZE.json exists and matches the hashes of the code, MODEL.json and the gate file.
The historical reused-vault writer is far_vault.py. Use verify.py or audit_20261019/audit.py for existing results.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import far_core as fc  # noqa: E402
import far_data  # noqa: E402

POLICIES = ["none", "random", "coverage", "exploit", "poh", "far", "far2", "all", "oracle_split", "oracle"]
REPAIRS = ["none", "fuse", "gate", "resid", "abstain"]
SEED = 20261019


def sha(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def pairs(c, rng, n_lines=60):
    """Candidate pairs (base top 30% of the line) with pre-assay signatures and the failure label (truth in the bottom half)."""
    lines = rng.choice(c.lines, min(n_lines, len(c.lines)), replace=False)
    X, y, fam = [], [], []
    for j in lines:
        b = c.base[:, j]; u = c.u[:, j]
        ok = np.isfinite(u)
        if ok.sum() < 20:
            continue
        rb = np.argsort(np.argsort(b)) / len(b)                 # low = predicted strong killer
        ut = np.full(len(u), np.nan); ut[ok] = (np.argsort(np.argsort(-u[ok])) + 0.5) / ok.sum()  # low = truly strong killer
        cand = (rb <= 0.30) & ok
        F = fc.false_prog_features(c, j)
        X.append(F[cand]); y.append((ut[cand] > 0.5).astype(int)); fam.append(c.famid[cand])
    return np.vstack(X), np.concatenate(y), np.concatenate(fam)


def auroc(s, y):
    from scipy.stats import rankdata
    n1, n0 = y.sum(), (1 - y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    return (rankdata(s)[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_auc(s, y, fam, draws=600, seed=SEED):
    rng = np.random.default_rng(seed)
    uf = np.unique(fam)
    idx = {f: np.where(fam == f)[0] for f in uf}
    out = []
    for _ in range(draws):
        pick = np.concatenate([idx[f] for f in rng.choice(uf, len(uf))])
        out.append(auroc(s[pick], y[pick]))
    out = np.array(out)
    return float(auroc(s, y)), float(np.nanpercentile(out, 5)), float(np.nanpercentile(out, 95))


def build(stage):
    D = far_data.load("dev")
    fam_ids = {f: i for i, f in enumerate(np.unique(D["family"]))}
    D["famid"] = np.array([fam_ids[f] for f in D["family"]])
    return D, fc.REFS[stage]


def main():
    stage = sys.argv[1]
    if stage not in fc.REFS:
        raise SystemExit("stage must be search, select or test; vault uses far_vault.py")
    out = HERE / f"records_{stage}.npz"
    if out.exists():
        raise SystemExit("write-once: records exist")
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else SEED
    if stage == "test":
        fz = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        for f, h in fz["hashes"].items():
            if sha(HERE / f) != h:
                raise SystemExit(f"FREEZE_MISMATCH {f}")
    D, folds = build(stage)
    model_path, rng = HERE / "MODEL.json", np.random.default_rng(seed)
    rec = {}
    camps = {}
    for fold, refs in folds.items():
        t0 = time.time()
        c = fc.Campaign(D, fold, refs)
        c.famid = D["famid"][c.q]
        camps[fold] = c
        print(f"fold {fold}: |Q|={len(c.q)} |R|={len(c.r)} lines={len(c.lines)} sig={c.has_sig.mean():.2f} t={time.time()-t0:.1f}s", flush=True)
    Xs, ys, fs = zip(*[pairs(c, rng) for c in camps.values()])
    X, y, fam = np.vstack(Xs), np.concatenate(ys), np.concatenate(fs)
    atlas = {"n_pairs": int(len(y)), "failure_rate": float(y.mean()), "signatures": {}}
    for k, nme in enumerate(["domain_distance", "neighbour_dispersion", "model_disagreement"]):
        a, lo, hi = boot_auc(X[:, k], y, fam)
        atlas["signatures"][nme] = {"auroc": a, "lcb90": lo, "ucb90": hi}
    if stage == "search":
        lr = LogisticRegression(C=1.0).fit(X, y)
        atlas["model_auroc_insample"] = float(auroc(lr.decision_function(X), y))
        tau = float(np.median(np.concatenate([c.trust[c.has_sig] for c in camps.values()])))
        model = {"coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]), "tau": tau, "fit_on": "search folds 0,1"}
        model_path.write_text(json.dumps(model, indent=1) + "\n", encoding="utf-8")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    beta, b0, tau = np.array(model["coef"]), model["intercept"], model["tau"]
    fmodel = lambda c, j: 1 / (1 + np.exp(-(fc.false_prog_features(c, j) @ beta + b0)))
    if stage in ("select", "test"):
        sc = X @ beta + b0
        a, lo, hi = boot_auc(sc, y, fam)
        atlas["frozen_model"] = {"auroc": a, "lcb90": lo, "ucb90": hi}
    import pickle
    vm = pickle.load(open(HERE / "VALUE_MODEL.pkl", "rb"))
    vmodel = lambda c, j: np.clip(vm.predict(fc.value_features(c, j)), 0, None)
    PRIMARY = "fuse" if stage == "search" else "gate"
    runs = [(p, PRIMARY) for p in POLICIES] + [(p, r) for p in ("exploit", "far") for r in REPAIRS if r != PRIMARY]
    for fold, c in camps.items():
        for p, r in runs:
            t0 = time.time()
            contrib, hits, frac = fc.run_policy(c, p, r, tau, vmodel if p == "far2" else fmodel, seed + fold)
            rec[f"{fold}|{p}|{r}"] = contrib
            rec[f"{fold}|{p}|{r}|hits"] = hits
            print(f"  fold {fold} {p:8s} {r:8s} U={contrib.sum():.4f} hits={hits.sum():.4f} measured={frac:.2f} {time.time()-t0:.0f}s", flush=True)
        rec[f"{fold}|fam"] = c.famid
    np.savez(out, **rec)
    (HERE / f"ATLAS_{stage}.json").write_text(json.dumps(atlas, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(atlas, indent=1))


if __name__ == "__main__":
    main()
