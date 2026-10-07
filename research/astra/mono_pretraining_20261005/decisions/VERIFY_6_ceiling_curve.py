"""Check 5b: own-mono ceiling as a function of the number of history lines, with measured P2 yield at full history.

Independent ridge on own GDSC2 mono (pair features and drug-specific slopes) trained on n history lines of the same tissue
(HD only; E masked at load), evaluated on every HD line: within-line Spearman gain over the contract S_both prior and
(full history) the registered P2 yield through the frozen engine. Run:
PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_6_ceiling_curve.py
Writes decisions/VERIFY_6_ceiling_curve.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L  # noqa: E402
from tools.datasets.combination_screens import open_vault  # noqa: E402
from research.astra.confirmation_campaign_20261004.design import campaign as c  # noqa: E402

OUT = L.HERE / "VERIFY_6_ceiling_curve.json"
MONO = L.STUDY / "results/mono_labels.csv.gz"


def sp(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return np.nan
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels for the own-mono learning curve", source=MONO, root=L.ROOT)
    mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
    tissues, report, sp_, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes for the own-mono learning curve and yield (E masked at load)")
    L.assert_e_masked(tissues, e_sidms)
    elig = mono[mono.eligible_primary_pretrain & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
    st = elig.groupby("jaaks_drug_id").y_rel.agg(["mean", "std"])
    own = mono[mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
    mval = {(r.sidm, r.jaaks_drug_id): (r.y_rel - st.loc[r.jaaks_drug_id, "mean"]) / st.loc[r.jaaks_drug_id, "std"]
            for r in own.itertuples() if r.jaaks_drug_id in st.index}
    ev = {s for t in sp_.values() for s in t["E"]}
    results = {}
    rng = np.random.default_rng(5)
    NS = (4, 8, 12, "all")
    gains = {(v, n): {} for v in ("pair_features", "drug_slopes") for n in NS}
    yields = {}
    for tissue, T in tissues.items():
        hd = sorted(sp_[tissue]["HD"])
        li = {s: T.lines.index(s) for s in T.lines}
        A = T.arrays["SV"]
        y = (A["y_s"] + A["y_v"]) / 2.0
        S_id = np.array([p[0] for p in T.pairs]); V_id = np.array([p[1] for p in T.pairs])
        ms = np.array([mval.get((T.lines[int(ci)], a), np.nan) for ci, a in zip(T.c, S_id)])
        mv = np.array([mval.get((T.lines[int(ci)], b), np.nan) for ci, b in zip(T.c, V_id)])
        drugs = sorted(set(S_id) | set(V_id)); dix = {d: i for i, d in enumerate(drugs)}
        X = np.zeros((len(y), len(drugs)))
        for r_i in range(len(y)):
            if np.isfinite(ms[r_i]):
                X[r_i, dix[S_id[r_i]]] += ms[r_i]
            if np.isfinite(mv[r_i]):
                X[r_i, dix[V_id[r_i]]] += mv[r_i]
        a0, b0 = np.nan_to_num(ms), np.nan_to_num(mv)
        Xp = np.column_stack([a0, b0, a0 * b0, np.abs(a0 - b0)])
        feats = {"pair_features": Xp, "drug_slopes": X}
        pid = T.pid
        size = int(pid.max()) + 1
        for target in hd:
            others = [s for s in hd if s != target]
            for n in NS:
                draws = [others] if n == "all" else [list(rng.choice(others, n, replace=False)) for _ in range(3)]
                per_draw = {v: [] for v in feats}
                for tr_lines in draws:
                    trm = np.isin(T.c, [li[s] for s in tr_lines])
                    ssum = np.bincount(pid[trm], weights=y[trm], minlength=size)
                    scnt = np.bincount(pid[trm], minlength=size).astype(float)
                    mu = y[trm].mean()
                    mu_lo = (y[trm].sum() - y) / (trm.sum() - 1)
                    prior = (ssum[pid] - y + 2.0 * mu_lo) / (scnt[pid] - 1 + 2.0)
                    resid = y - prior
                    for s in tr_lines:
                        m = T.c == li[s]; resid[m] -= resid[m].mean()
                    te = T.c == li[target]
                    base_t = (ssum[pid[te]] + 2.0 * mu) / (scnt[pid[te]] + 2.0)       # contract S_both on this history
                    tv = y[te]
                    for v, F in feats.items():
                        Ft = F[trm]
                        beta = np.linalg.solve(Ft.T @ Ft + 300.0 * np.eye(F.shape[1]), Ft.T @ resid[trm])
                        g = F[te] @ beta
                        per_draw[v].append(sp(base_t + g, tv) - sp(base_t, tv))
                        if n == "all":
                            rows = np.flatnonzero(te)
                            H = c.restrict(T, tr_lines)
                            ys = []
                            for role in c.ROLES:
                                tg = c.make_target(T, H, target, role, allowed_history=tr_lines, forbidden=sorted(ev | {target}))
                                truth = c.truth_of(T, tg)
                                tg.scores["base"] = (tg.q["S_both"], tg.q["S_both"])
                                tg.scores["alt"] = (tg.q["S_both"] + g, tg.q["S_both"])
                                assert np.allclose(tg.q["S_both"], base_t)
                                ys.append((c.run_p2(tg, truth, "base", 30)["confirmed"], c.run_p2(tg, truth, "alt", 30)["confirmed"]))
                            yields.setdefault(v, {})[(tissue, target)] = (np.mean([a for a, _ in ys]), np.mean([b for _, b in ys]))
                for v in feats:
                    gains[(v, n)][(tissue, target)] = float(np.nanmean(per_draw[v]))
    out = {"learning_curve_concordance_gain": {}}
    for (v, n), d in gains.items():
        b = L.line_bootstrap(d, {k: k[0] for k in d})
        out["learning_curve_concordance_gain"][f"{v}|n={n}"] = b
    out["yield_full_history"] = {}
    for v, d in yields.items():
        ks = sorted(d)
        base = {k: d[k][0] for k in ks}; alt = {k: d[k][1] for k in ks}
        b = L.line_bootstrap({k: alt[k] - base[k] for k in ks}, {k: k[0] for k in ks}, base_by_line=base)
        out["yield_full_history"][v] = dict(base_total=float(sum(base.values())), alt_total=float(sum(alt.values())),
                                            rel_gain=float(sum(alt.values()) / sum(base.values()) - 1), rel_ci=b["rel_ci"])
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
