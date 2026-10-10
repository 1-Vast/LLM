"""One-time confirmatory evaluation (runs after FREEZE.json; hyperparameters come from GATE.json).

Domain M  MIX-Seq pool A, 48 unseen confirmation lines: does a 24 h measurement complement the
          DepMap-scale prior for 5-day PRISM sensitivity (M1), does the STATE forecast transport
          (M2, plus RNA-level transport, same-line cross-platform and cross-experiment ceilings),
          and what does each measure-or-predict policy select (M3)?
Domain T  MIX-Seq pool D trametinib time course (timecourse.py).
Domain K  Tahoe 24 h -> PRISM 5 day on the 16 confirmation lines (K1 ceiling, K2 potency, K3 sign).

``poison_seed`` replaces every sealed 5-day outcome with Gaussian noise; predictions and selections
must not change (verify.py).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ccle as C  # noqa: E402
import gate as G  # noqa: E402
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402
import timecourse as T  # noqa: E402

SEED = 20261010
NBOOT = 2000
r, z = G.r, G.z


def poison(late: dict, seed: int | None) -> dict:
    if seed is None:
        return late
    rng = np.random.default_rng(seed)
    out = dict(late)
    for k in ("primary_2p5", "secondary_2p5", "secondary_mean"):
        out[k] = np.where(np.isfinite(late[k]), rng.normal(0, 1, late[k].shape), np.nan)
    return out


def topk_util(score: np.ndarray, y: np.ndarray, k: int) -> tuple[float, np.ndarray]:
    """Select the k lines with the highest predicted sensitivity (score), among lines with an outcome."""
    ok = np.flatnonzero(np.isfinite(y) & np.isfinite(score))
    sel = ok[np.argsort(-score[ok], kind="stable")[:k]]
    return float(-np.mean(y[sel])), sel


def boot(fn, n: int, seed: int = SEED) -> list:
    rng = np.random.default_rng(seed)
    v = np.array([fn(rng.integers(0, n, n)) for _ in range(NBOOT)])
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


# --------------------------------------------------------------------------- domain M

def domain_m(cfg: dict, poison_seed: int | None, store: dict) -> dict:
    sp = MP.split()
    conf, dev = sp["pool_A_confirmation"], sp["pool_A_development"]
    drugs, sdrugs = G.MIX_DRUGS_LATE, G.STATE_DRUGS
    yk, k = cfg["mix_late_endpoint"], cfg["top_k"]
    ext = H.load_late("external_mix"); mdev = H.load_late("mix_development")
    seal = poison(H.load_late("mix_sealed"), poison_seed)
    srow = {d: i for i, d in enumerate(seal["files"])}
    ed, dd, sd = list(ext["drugs"]), list(mdev["drugs"]), list(seal["drugs"])
    mp = MP.pool_a_panel(conf, ["A_treated_sealed"], cfg["projection_variant"], drugs)
    st = MP.state_forecast("A", cfg["projection_variant"], conf, sdrugs)
    n = len(conf)
    Y, Bp, Rm, Sm = (np.full((n, len(drugs)), np.nan) for _ in range(4))
    for j, drug in enumerate(drugs):
        Y[:, j] = [seal[yk][srow[d], sd.index(drug)] for d in conf]
        refs = list(ext["depmap"]) + list(mdev["files"])
        yref = np.r_[ext[yk][:, ed.index(drug)], mdev[yk][:, dd.index(drug)]]
        Bp[:, j] = C.ridge(conf, refs, yref, cfg["mix_prior"]["n_pc"], cfg["mix_prior"]["alpha"])
        Rm[:, j] = [-np.linalg.norm(mp.obs[i, j]) if np.isfinite(mp.obs[i, j]).all() else np.nan for i in range(n)]
        if drug in sdrugs:
            Sm[:, j] = -np.linalg.norm(st["paired"][:, sdrugs.index(drug)], axis=1)
    zc = lambda X, b=None: np.column_stack([z(X[:, j] if b is None else X[b, j]) for j in range(X.shape[1])])  # noqa: E731
    store.update({"M_lines": np.array(conf), "M_B": Bp, "M_Rmag": Rm, "M_Smag": Sm})

    def inc(b, extra, js):
        Bb, Yb, Eb = Bp[b], Y[b], extra[b]
        return float(np.nanmean([r(z(Bb[:, j]) + z(Eb[:, j]), Yb[:, j]) - r(Bb[:, j], Yb[:, j]) for j in js]))

    alljs, sjs = range(len(drugs)), [drugs.index(d) for d in sdrugs]
    full = np.arange(n)
    m1 = {"per_drug": {d: {"B": r(Bp[:, j], Y[:, j]), "B_plus_Rmag": r(z(Bp[:, j]) + z(Rm[:, j]), Y[:, j]), "R_mag": r(Rm[:, j], Y[:, j])} for j, d in enumerate(drugs)},
          "mean_increment": inc(full, Rm, alljs), "ci95": boot(lambda b: inc(b, Rm, alljs), n)}
    m1["drugs_improved"] = int(sum(v["B_plus_Rmag"] > v["B"] for v in m1["per_drug"].values()))
    m1["pass"] = bool(m1["ci95"][0] > 0 and m1["drugs_improved"] >= 4)
    m2 = {"per_drug": {d: {"B": r(Bp[:, j], Y[:, j]), "B_plus_Smag": r(z(Bp[:, j]) + z(Sm[:, j]), Y[:, j]), "S_mag": r(Sm[:, j], Y[:, j])} for j, d in zip(sjs, sdrugs)},
          "mean_increment": inc(full, Sm, sjs), "ci95": boot(lambda b: inc(b, Sm, sjs), n)}
    m2["transport_refused"] = bool(m2["ci95"][1] < G.MUB)
    # M3 decisions
    # every policy is a predicted 5-day viability (low = sensitive); select the k lowest
    pol = {"P0_prior": Bp, "P1_prior_plus_state": np.where(np.isfinite(Sm), zc(Bp) + zc(Sm), np.nan),
           "P2_prior_plus_24h_measurement": zc(Bp) + zc(Rm), "P3_oracle_5day": Y}
    gate_decision = json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))["mix_24h_to_5d"]["decision"]
    m3 = {"per_drug": {}, "gate_decision": gate_decision,
          "policy_by_gate": {"MEASURE_EARLY": "P2_prior_plus_24h_measurement", "ADMIT_WORLD_MODEL": "P1_prior_plus_state"}.get(gate_decision, "P0_prior")}
    sels = {}
    for j, d in enumerate(drugs):
        rec = {"random_expectation": float(-np.nanmean(Y[:, j]))}
        for p, S in pol.items():
            if np.isfinite(S[:, j]).sum() == 0:
                continue
            u, sel = topk_util(-S[:, j], Y[:, j], k)
            rec[p] = u
            if p != "P3_oracle_5day":  # the oracle selects by outcome by definition; excluded from poisoning checks
                sels[f"{d}|{p}"] = [conf[i] for i in sel]
        m3["per_drug"][d] = rec

    def du(b, a, c, js):
        return float(np.mean([topk_util(-pol[a][b, j], Y[b, j], k)[0] - topk_util(-pol[c][b, j], Y[b, j], k)[0] for j in js]))

    m3["P2_minus_P0"] = {"mean": du(full, "P2_prior_plus_24h_measurement", "P0_prior", alljs),
                         "ci95": boot(lambda b: du(b, "P2_prior_plus_24h_measurement", "P0_prior", alljs), n),
                         "drugs_better": int(sum(m3["per_drug"][d]["P2_prior_plus_24h_measurement"] > m3["per_drug"][d]["P0_prior"] for d in drugs))}
    m3["P1_minus_P0"] = {"mean": du(full, "P1_prior_plus_state", "P0_prior", sjs),
                         "ci95": boot(lambda b: du(b, "P1_prior_plus_state", "P0_prior", sjs), n)}
    m3["pass"] = bool(m3["P2_minus_P0"]["ci95"][0] > 0 and m3["P2_minus_P0"]["drugs_better"] >= 4)
    m3["costs"] = {"P0_prior": {"wells": 0, "days": 0}, "P1_prior_plus_state": {"wells": 0, "days": 0, "gpu_forward_sets": 1209},
                   "P2_prior_plus_24h_measurement": {"wells_per_drug": 2, "shared_control_wells": 2, "days": 1},
                   "P3_oracle_5day": {"pooled_5day_screen": 1, "days": 5}}
    store["M3_selections"] = np.array(json.dumps(sels))
    return {"n_lines": n, "late_endpoint": yk, "M1_measurement_complements_prior": m1, "M2_state_forecast_transport": m2,
            "M2_rna": rna_transport(cfg, mp, st, conf, dev), "M2_cross_platform_same_line": cross_platform(cfg, sp),
            "M2_cross_experiment_replicate": replicate_c(cfg, sp), "M3_decisions": m3}


def rna_transport(cfg, mp, st, conf, dev) -> dict:
    """Context-deviation r per line on confirmation lines (panel = other confirmation lines)."""
    keep, info = H.A.qualified_reference()
    tp = H.A.attach_expression(H.A.phenotype_panel(keep, keep, info["table"], info["names"]))
    out = {}
    for j, drug in enumerate(G.STATE_DRUGS):
        O = mp.obs[:, j]
        ok = np.flatnonzero(np.isfinite(O).all(1))
        S = st["paired"][:, j][:, mp.present]
        lab = MP.MS.label(drug, MP.MIX_DRUGS[drug])
        Td = tp.delta[:, tp.labels.index(lab)][:, mp.present]
        tok = np.isfinite(Td).all(1)
        Tdev, tb = Td[tok] - Td[tok].mean(0), tp.basal[tok]
        rs = {"S": [], "S_perm": [], "B_mix": [], "B_tahoe": [], "ceiling": []}
        for ii, i in enumerate(ok):
            oth = np.array([t for t in ok if t != i])
            panel = O[oth].mean(0)
            od = O[i] - panel
            rs["S"].append(r(S[i] - S[oth].mean(0), od))
            rs["S_perm"].append(r(S[ok[(ii + 1) % len(ok)]] - S[oth].mean(0), od))
            rs["B_mix"].append(r(_kern(mp.basal[i], mp.basal[oth], O[oth] - panel), od))
            rs["B_tahoe"].append(r(_kern(mp.basal[i], tb, Tdev), od))
            h = mp.halves[i, j]
            rh = r(h[0] - panel, h[1] - panel)
            rs["ceiling"].append(2 * rh / (1 + rh) if np.isfinite(rh) and rh > -1 else np.nan)
        v = {kk: np.array(x) for kk, x in rs.items()}
        out[drug] = {kk: float(np.nanmean(x)) for kk, x in v.items()} | {
            "n_lines": int(len(ok)),
            "S_ci95": boot(lambda b: float(np.nanmean(v["S"][b])), len(ok)),
            "S_minus_B_tahoe_ci95": boot(lambda b: float(np.nanmean(v["S"][b] - v["B_tahoe"][b])), len(ok))}
    return out


def _kern(target, train, Y, tau=0.1, m=10):
    c = train.mean(0); a = target - c; Bm = train - c
    sim = (Bm @ a) / (np.linalg.norm(Bm, axis=1) * np.linalg.norm(a) + 1e-12)
    o = np.argsort(-sim)[:m]
    w = np.exp((sim[o] - sim[o].max()) / tau)
    return np.tensordot(w, Y[o], 1) / w.sum()


def cross_platform(cfg, sp) -> dict:
    """Same line, two platforms: Tahoe observed context deviation vs MIX-Seq observed context deviation
    (11 STATE-training lines in pool A); the ceiling for any Tahoe-trained context predictor."""
    lines = sp["pool_A_state_training"]
    allA = lines + sp["pool_A_confirmation"]
    mp = MP.pool_a_panel(allA, ["A_treated_sealed"], cfg["projection_variant"], G.STATE_DRUGS)
    keep, info = H.A.qualified_reference()
    tp = H.A.attach_expression(H.A.phenotype_panel(keep, keep, info["table"], info["names"]))
    st = MP.state_forecast("A", cfg["projection_variant"], allA, G.STATE_DRUGS)
    out = {}
    for j, drug in enumerate(G.STATE_DRUGS):
        lab = MP.MS.label(drug, MP.MIX_DRUGS[drug])
        Td = tp.delta[:, tp.labels.index(lab)][:, mp.present]
        tmean = np.nanmean(Td, 0)
        O = mp.obs[:, j]
        ok = np.isfinite(O).all(1)
        omean = O[ok].mean(0)
        S = st["paired"][:, j][:, mp.present]
        smean = S[ok].mean(0)
        rt, rs = [], []
        for i, d in enumerate(lines):
            f = sp["lines"][d]["tahoe_file"]
            if not ok[i] or f not in keep:
                continue
            t = Td[keep.index(f)]
            if not np.isfinite(t).all():
                continue
            rt.append(r(t - tmean, O[i] - omean))
            rs.append(r(S[i] - smean, O[i] - omean))
        out[drug] = {"tahoe_observed_vs_mixseq_r": float(np.nanmean(rt)) if rt else None,
                     "state_in_sample_vs_mixseq_r": float(np.nanmean(rs)) if rs else None, "n_lines": len(rt)}
    return out


def replicate_c(cfg, sp) -> dict:
    """Trametinib in pool A versus the independent pool-C experiment, same lines."""
    both = sorted(set(sp["pool_A"]) & set(sp["pool_C"]))
    cal = MP.MS.calibration(sp)
    a = MP.load_units(["A_control", "A_treated_sealed", "A_treated_dev"])
    c = MP.load_units(["C_control", "C_treated"])
    present = a["present"]
    OA, OC = [], []
    for d in both:
        def resp(u, treat, ctrl):
            tm, cm = (u["depmap"] == d) & treat, (u["depmap"] == d) & ctrl
            if tm.sum() < MP.MIN_TREATED or cm.sum() < MP.MIN_TREATED:
                return np.full(int(present.sum()), np.nan)
            return MP.MS.project(u["frac"][tm], cal, "v1")[:, present].mean(0) - MP.MS.project(u["frac"][cm], cal, "v1")[:, present].mean(0)
        OA.append(resp(a, a["perturbation"] == "Trametinib", a["perturbation"] == "control"))
        OC.append(resp(c, c["perturbation"] == "Trametinib", c["perturbation"] == "control"))
    OA, OC = np.array(OA), np.array(OC)
    ok = np.isfinite(OA).all(1) & np.isfinite(OC).all(1)
    ma, mc = OA[ok].mean(0), OC[ok].mean(0)
    rs = [r(OA[i] - ma, OC[i] - mc) for i in np.flatnonzero(ok)]
    return {"n_lines": int(ok.sum()), "context_deviation_r": float(np.nanmean(rs)), "generic_r": r(ma, mc)}


# --------------------------------------------------------------------------- domain T

def domain_t(cfg, poison_seed) -> dict:
    sp = MP.split()
    lines = sp["pool_D"]
    yk = cfg["mix_late_endpoint"]
    ext = H.load_late("external_mix"); mdev = H.load_late("mix_development")
    seal = poison(H.load_late("mix_sealed"), poison_seed)
    j = list(seal["drugs"]).index("Trametinib")
    srow = {d: i for i, d in enumerate(seal["files"])}; drow = {d: i for i, d in enumerate(mdev["files"])}
    jd = list(mdev["drugs"]).index("Trametinib")
    pdev = poison(mdev, poison_seed)
    late = np.array([seal[yk][srow[d], j] if d in srow else pdev[yk][drow[d], jd] if d in drow else np.nan for d in lines])
    dev = list(mdev["files"])
    ccle_pred = []
    for d in lines:
        refs = list(ext["depmap"]) + [x for x in dev if x != d]
        yref = np.r_[ext[yk][:, list(ext["drugs"]).index("Trametinib")], [mdev[yk][drow[x], jd] for x in dev if x != d]]
        ccle_pred.append(C.ridge([d], refs, yref, cfg["mix_prior"]["n_pc"], cfg["mix_prior"]["alpha"])[0])
    stz = np.load(MP.DATA / "mixseq_state" / "D_v1.npz", allow_pickle=True)
    li = {d: i for i, d in enumerate(stz["lines"])}
    lab = MP.MS.label("Trametinib", 0.05)
    sp_ = stz["paired_delta"][[li[d] for d in lines]][:, list(stz["labels"]).index(lab)]
    keep, info = H.A.qualified_reference()
    tp = H.A.attach_expression(H.A.phenotype_panel(keep, keep, info["table"], info["names"]))
    tg = np.nanmean(tp.delta[:, tp.labels.index(lab)], 0)
    # ccle_pred is a predicted 5-day viability, aligned with late and with -||O(t)||
    return T.analyse(lines, late, sp_, tg, np.array(ccle_pred))


# --------------------------------------------------------------------------- domain K

def domain_k(cfg, poison_seed, store) -> dict:
    split = H.split()
    conf, tdev = split["confirmation"], split["development"]
    keep, _ = H.A.qualified_reference()
    E = H.early_panel(keep)
    sel = lambda X: X - np.nanmean(X, 0, keepdims=True)  # noqa: E731
    yk = cfg["tahoe_late_endpoint"]
    ext = H.load_late("external_tahoe"); ldev = H.load_late("development")
    lc = poison(H.load_late("confirmation"), poison_seed)
    drugs = list(lc["drugs"])
    Ye, Yd, Yc = ext[yk], ldev[yk], lc[yk]
    mu = np.nanmean(Ye, 0)
    refs = list(ext["depmap"]) + [split["lines"][f]["depmap_id"] for f in tdev]
    Yref = np.vstack([Ye, Yd])
    ej = [E.drugs.index(d) if d in E.drugs else None for d in drugs]
    cs, p = cfg["tahoe_bridge_coef_s24_k24"], cfg["tahoe_prior"]
    n = len(conf)
    Bm, Rm = np.full((n, len(drugs)), np.nan), np.full((n, len(drugs)), np.nan)
    for i, f in enumerate(conf):
        d = split["lines"][f]["depmap_id"]
        Bm[i] = np.array([C.kernel(d, refs, Yref[:, jj], p["tau"], p["top_m"]) for jj in range(len(drugs))]) - mu
        e = keep.index(f)
        Rm[i] = [cs[0] * sel(E.s24)[e, kk] + cs[1] * sel(E.k24)[e, kk] if kk is not None else np.nan for kk in ej]
    Ys = Yc - mu
    store.update({"K_B": Bm, "K_Rdyn": Rm})

    def ceil(b):
        return float(np.nanmean([r(z(Bm[i]) + z(Rm[i]), Ys[i]) - r(Bm[i], Ys[i]) for i in b]))

    k1 = {"B_mean_r": float(np.nanmean([r(Bm[i], Ys[i]) for i in range(n)])), "R_dyn_mean_r": float(np.nanmean([r(Rm[i], Ys[i]) for i in range(n)])),
          "ceiling": ceil(range(n)), "ceiling_ci95": boot(ceil, n)}
    k1["refusal_confirmed"] = bool(k1["ceiling_ci95"][1] < G.MUB)
    # K2 potency: Tahoe panel-mean readouts vs mean PRISM over confirmation lines (units = drugs)
    common = [d for d in drugs if d in E.drugs]
    late_mean = np.nanmean(Yc[:, [drugs.index(d) for d in common]], 0)
    kp = np.nanmean(E.k24[:, [E.drugs.index(d) for d in common]], 0)
    spn = np.nanmean(E.s24[:, [E.drugs.index(d) for d in common]], 0)
    moa = pd.read_parquet(H.ROOT / "data/external/tahoe_phenotype_20261010/metadata/tahoe_drugs.parquet").set_index("drug")["moa-fine"].reindex(common).fillna("unclear").to_numpy()
    clusters = np.unique(moa)
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(NBOOT):
        cl = rng.choice(clusters, len(clusters))
        idx = np.concatenate([np.flatnonzero(moa == c) for c in cl])
        diffs.append(r(kp[idx], late_mean[idx]) - r(spn[idx], late_mean[idx]))
    k2 = {"r_k24": r(kp, late_mean), "r_s24": r(spn, late_mean), "difference": r(kp, late_mean) - r(spn, late_mean),
          "ci95_drug_cluster": [float(np.nanpercentile(diffs, 2.5)), float(np.nanpercentile(diffs, 97.5))], "n_drugs": len(common)}
    # K3 sign of G1 shift across confirmation lines for the development top-29 drugs
    top = json.loads((HERE / "development/dev_direction.json").read_text())["top_drugs"]
    rows = np.array([keep.index(f) for f in conf])
    G1 = np.array([[E.g24[rr, E.drugs.index(d)] for d in top] for rr in rows])
    YT = np.array([[Yc[i, drugs.index(d)] for d in top] for i in range(n)])
    k3fn = lambda b: float(np.nanmean([r(G1[b, j], YT[b, j]) for j in range(len(top))]))  # noqa: E731
    k3 = {"mean_r": k3fn(np.arange(n)), "ci95": boot(k3fn, n), "n_drugs": len(top)}
    return {"n_lines": n, "late_endpoint": yk, "K1_selectivity_ceiling": k1, "K2_potency_kinetic_vs_share": k2, "K3_g1_sign_top_drugs": k3}


def main(out_dir: Path = HERE, poison_seed: int | None = None) -> dict:
    if not (HERE / "FREEZE.json").exists():
        raise SystemExit("evaluate.py runs only after FREEZE.json exists")
    cfg = json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))["config"]
    store = {}
    res = {"protocol": "PROTOCOL.md", "freeze": json.loads((HERE / "FREEZE.json").read_text())["frozen_utc"], "poison_seed": poison_seed,
           "M": domain_m(cfg, poison_seed, store), "T": domain_t(cfg, poison_seed), "K": domain_k(cfg, poison_seed, store)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RESULTS.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    np.savez(out_dir / "PREDICTIONS.npz", **store)
    return res


if __name__ == "__main__":
    main()
