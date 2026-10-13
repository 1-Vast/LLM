"""Task C: target-hypothesis triage (TASK_C.md), run once after the S2 verdict permitted it.

File summary
- Path: research/orbit_contrast_20261013/taskc.py
- Purpose: for held-out annotated compounds (outer folds 1-4), nominate 10 knockdown genes per
  compound under seven arms (random, degree prior, chemical-neighbour transfer, raw connectivity,
  CMap-style z, orbit-contrast connectivity, OCEA-admitted) and count annotated targets among them.
- Core points:
  - Training degree, strata, centring, CMap references and the admission gate use training
    compounds (fold != k) only; test annotations are read only to score hits.
  - Refuses unless the main freeze authenticates, DEVIATIONS.json D5 records the current SHA-256
    of TASK_C.md and this file, and RESULTS_C.json does not exist.
- Command (study folder): `python taskc.py`; `python taskc.py --count` prints unit counts only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sources as S  # noqa: E402
from ocea import ALPHAS, Ridge, choose_alpha, paired, spearman  # noqa: E402
from routes import TaskA, permutation_from, rng_for, stratum_donors, tanimoto, unit  # noqa: E402

TOP = 10
M_PERM = 16
OUTER = (1, 2, 3, 4)
ARMS = ("Z0", "P", "H", "X", "Zc", "OC", "F")
DESC = ("n_lines", "log_universe", "active_fraction", "norm_over_vehicle", "oc_top1", "oc_top10_mean", "oc_sd", "oc_separation")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require_lock() -> None:
    import freeze
    freeze.require_freeze()
    dev = json.loads((HERE / "DEVIATIONS.json").read_text(encoding="utf-8"))
    d5 = [d for d in dev["deviations"] if d["id"] == "D5"]
    want = {"TASK_C.md": _sha(HERE / "TASK_C.md"), "taskc.py": _sha(HERE / "taskc.py")}
    if not d5 or d5[0].get("sha256") != want:
        raise SystemExit("TASKC_UNLOCKED: DEVIATIONS.json D5 must record the current TASK_C.md and taskc.py digests")


def build_a():
    z = S.load_phase1()
    store, ents, smiles = S.compound_store(z)
    ck = S.compile_compounds(store, ents)
    fps = S.morgan(smiles)
    A = TaskA(z, ck, fps, np.zeros(len(z["kd_gene"])))     # gene strata here use training degree only
    return z, ck, fps, A


def target_matrix(ck, kd_index: dict, n_kd: int) -> sparse.csr_matrix:
    rows, cols = [], []
    for i, s in enumerate(ck.signed):
        for g in s:
            if g in kd_index:
                rows.append(i)
                cols.append(kd_index[g])
    return sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(ck.signed), n_kd))


def nominate(score: np.ndarray, tie_order: np.ndarray) -> np.ndarray:
    """Top-10 columns per row; -inf excluded; ties broken by the fixed SHA-256 gene order."""
    s = score[:, tie_order]
    idx = np.argsort(-s, axis=1, kind="stable")[:, :TOP]
    return tie_order[idx]


def hits(top: np.ndarray, truth: np.ndarray) -> np.ndarray:
    return np.take_along_axis(truth, top, 1).sum(1)


def donor_matrix(keys: np.ndarray, members: np.ndarray, n: int) -> sparse.csr_matrix:
    donors = stratum_donors(keys, members, fallbacks=[(0, 1), (0,)])
    rows, cols, vals = [], [], []
    for i, d in donors.items():
        if len(d):
            rows.extend([i] * len(d))
            cols.extend(d.tolist())
            vals.extend([1.0 / len(d)] * len(d))
    return sparse.csr_matrix((vals, (rows, cols)), shape=(n, n))


def run(count_only: bool = False) -> dict:
    t0 = time.time()
    z, ck, fps, A = build_a()
    genes = [str(g) for g in z["kd_gene"]]
    n_kd, L = len(genes), A.L
    fold = np.array([S.fold_of(str(k)) for k in z["compound"]])
    thr = S.vehicle_thresholds(z)
    nrm = np.linalg.norm(np.nan_to_num(A.Y.astype(np.float64)), axis=2)
    act = A.has & (nrm > thr[None])
    Tm = target_matrix(ck, A.kd_index, n_kd)
    universe = (A.has.astype(np.int32) @ A.kd_has.T.astype(np.int32)) > 0          # n_cp x n_kd
    truth_all = Tm.toarray().astype(bool) & universe
    eligible = truth_all.any(1)
    lm = np.array([g in A.lm for g in genes], int)
    tie = np.array([int(hashlib.sha256(g.encode()).hexdigest()[:15], 16) for g in genes])
    tie_order = np.argsort(tie, kind="stable")
    units = {k: int((eligible & (fold == k)).sum()) for k in OUTER}
    if count_only:
        return {"units_by_fold": units, "units": int(sum(units.values())),
                "units_active": int((eligible & np.isin(fold, OUTER) & act.any(1)).sum())}

    out_rows = []
    gate_info = []
    for k in OUTER:
        tr = fold != k
        te_idx = np.flatnonzero(eligible & (fold == k))
        trn_idx = np.flatnonzero(eligible & tr)
        rows = np.concatenate([te_idx, trn_idx])
        pos = {int(c): i for i, c in enumerate(rows)}
        deg = np.asarray(Tm[np.flatnonzero(tr)].sum(0)).ravel()
        dbin = np.digitize(deg, [1, 2, 5])
        sumX = np.zeros((len(rows), n_kd))
        sumZ = np.zeros((len(rows), n_kd))
        sumO = np.zeros((len(rows), n_kd))
        cnt = np.zeros((len(rows), n_kd))
        for T in range(L):
            kdm = np.flatnonzero(A.kd_has[:, T])
            K = unit(A.KDc[kdm, T].astype(np.float64))
            ref = np.flatnonzero(tr & A.has[:, T])
            mu = A.Y[ref, T].astype(np.float64).mean(0)
            Cr = unit(A.Y[ref, T].astype(np.float64) - mu) @ K.T
            m_g, s_g = Cr.mean(0), np.maximum(Cr.std(0), 1e-6)
            q = rows[A.has[rows, T]]
            C = unit(A.Y[q, T].astype(np.float64) - mu) @ K.T
            kn = np.linalg.norm(A.KDc[kdm, T], axis=1)
            terc = np.digitize(kn, np.quantile(kn, [1 / 3, 2 / 3]))
            W = donor_matrix(np.stack([lm[kdm], dbin[kdm], terc], 1), np.arange(len(kdm)), len(kdm))
            OC = C - np.asarray((W @ C.T).T)
            qi = np.array([pos[int(c)] for c in q])
            sumX[np.ix_(qi, kdm)] += C
            sumZ[np.ix_(qi, kdm)] += (C - m_g) / s_g
            sumO[np.ix_(qi, kdm)] += OC
            cnt[np.ix_(qi, kdm)] += 1
        ok = cnt > 0
        with np.errstate(invalid="ignore", divide="ignore"):
            X = np.where(ok, sumX / cnt, -np.inf)
            Zc = np.where(ok, sumZ / cnt, -np.inf)
            OC = np.where(ok, sumO / cnt, -np.inf)
        truth = truth_all[rows]
        # admission gate: identity contrast of OC under within-stratum gene relabelling
        donors = stratum_donors(np.stack([lm, dbin], 1), np.arange(n_kd), fallbacks=[(0,)])
        h_real = hits(nominate(OC, tie_order), truth)
        h_perm = np.zeros(len(rows))
        for m in range(M_PERM):
            perm = permutation_from(donors, n_kd, rng_for("taskc-orbit", k, m))
            h_perm += hits(nominate(OC[:, perm], tie_order), truth)
        contrast = h_real - h_perm / M_PERM
        D = np.zeros((len(rows), len(DESC)))
        for i, c in enumerate(rows):
            v = OC[i][np.isfinite(OC[i])]
            srt = np.sort(v)[::-1]
            sd = max(float(v.std()), 1e-9)
            prof = A.has[c]
            D[i] = (prof.sum(), np.log(ok[i].sum()), act[c, prof].mean(), (nrm[c, prof] / thr[prof]).mean(),
                    srt[0], srt[:TOP].mean(), sd, (srt[0] - srt[TOP - 1]) / sd)
        nte = len(te_idx)
        ytr, Dtr = contrast[nte:], D[nte:]
        alpha = choose_alpha(Dtr, ytr, fold[trn_idx])
        chat = Ridge(alpha).fit(Dtr, ytr).predict(D[:nte])
        gate_info.append({"fold": k, "alpha": alpha, "train_units": int(len(trn_idx)), "test_units": int(nte)})
        # arms on test units
        sl = slice(0, nte)
        P = np.where(ok[sl], deg[None].astype(float), -np.inf)
        trn_ann = np.flatnonzero(tr & (np.asarray(Tm.sum(1)).ravel() > 0))
        sim = tanimoto(fps[te_idx], fps[trn_ann])
        kk = min(TOP, len(trn_ann))
        nb = np.argpartition(-sim, kk - 1, axis=1)[:, :kk]
        sv = np.take_along_axis(sim, nb, 1)
        w = np.where(sv >= 0.3, sv ** 2, 0.0)
        Hs = np.zeros((nte, n_kd))
        for j in range(kk):
            Hs += w[:, j:j + 1] * Tm[trn_ann[nb[:, j]]].toarray()
        H = np.where(ok[sl], Hs + 1e-6 * deg[None], -np.inf)
        rnd = np.zeros((nte, TOP), int)
        for i, c in enumerate(te_idx):
            cand = np.flatnonzero(ok[i])
            rnd[i] = rng_for("taskc-random", str(z["compound"][c])).choice(cand, TOP, replace=False)
        tops = {"Z0": rnd, "P": nominate(P, tie_order), "H": nominate(H, tie_order), "X": nominate(X[sl], tie_order),
                "Zc": nominate(Zc[sl], tie_order), "OC": nominate(OC[sl], tie_order)}
        admit = chat > 0
        tops["F"] = np.where(admit[:, None], tops["OC"], tops["P"])
        for i, c in enumerate(te_idx):
            row = {"compound": str(z["compound"][c]), "fold": k, "active": bool(act[c].any()),
                   "n_true": int(truth[i].sum()), "universe": int(ok[i].sum()), "chat": float(chat[i]),
                   "contrast": float(contrast[i]), "admitted": bool(admit[i])}
            row.update({f"hits_{a}": int(truth[i, tops[a][i]].sum()) for a in ARMS})
            out_rows.append(row)
        print(f"[Task C] fold {k} done {time.time() - t0:.0f}s ({nte} units)", flush=True)
    return {"rows": out_rows, "gate_info": gate_info, "seconds": round(time.time() - t0, 1)}


def summarise(res: dict) -> dict:
    rows = res["rows"]
    out = {}
    for pop, keep in (("primary_all", lambda r: True), ("active", lambda r: r["active"])):
        rr = [r for r in rows if keep(r)]
        h = {a: np.array([r[f"hits_{a}"] for r in rr], float) for a in ARMS}
        blk = {"units": len(rr), "mean_true_targets": float(np.mean([r["n_true"] for r in rr])),
               "hits_at_10": {a: float(h[a].mean()) for a in ARMS},
               "hits_per_assay": {a: float(h[a].mean() / TOP) for a in ARMS},
               "contrasts": {"C1 F-Zc": paired(h["F"] - h["Zc"]), "C2 OC-X": paired(h["OC"] - h["X"])}}
        for a in ARMS:
            for b in ("P", "H", "Z0"):
                if a != b:
                    blk["contrasts"][f"{a}-{b}"] = paired(h[a] - h[b])
        c = np.array([r["contrast"] for r in rr])
        ch = np.array([r["chat"] for r in rr])
        blk["gate"] = {"spearman_chat_contrast": spearman(ch, c), "admitted_fraction": float(np.mean([r["admitted"] for r in rr])),
                       "mean_contrast": float(c.mean())}
        out[pop] = blk
    p = out["primary_all"]["contrasts"]
    c1, c2 = p["C1 F-Zc"], p["C2 OC-X"]
    neg = lambda d: bool(d.get("ci95") and d["ci95"][1] < 0)  # noqa: E731
    supported = c1.get("difference", 0) > 0 and c1.get("p_greater", 1) < 0.025 and not neg(p["F-H"]) and not neg(p["F-P"])
    out["decision"] = {"task_c": "DECISION_UTILITY_SUPPORTED" if supported else "NOT_SUPPORTED",
                       "orbit_calibration_helps": bool(c2.get("difference", 0) > 0 and c2.get("p_greater", 1) < 0.025)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", action="store_true")
    args = ap.parse_args()
    if args.count:
        print(json.dumps(run(count_only=True)))
        return 0
    require_lock()
    target = HERE / "RESULTS_C.json"
    if target.exists():
        raise SystemExit("RESULTS_C_ALREADY_WRITTEN: Task C is write-once")
    res = run()
    out = {"stage": "Task C (TASK_C.md)", "alphas": list(ALPHAS), "gate_info": res["gate_info"], "seconds": res["seconds"],
           **summarise(res), "rows": res["rows"]}
    target.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["decision"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
