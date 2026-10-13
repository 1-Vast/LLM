"""Confirmatory stage on sealed PRISM Repurposing 24Q2 (REP.1M): predict and lock first, evaluate after authorisation.

File summary
- Path: research/knowledge_reality_20261013/confirm.py
- Purpose: run PROTOCOL.md stage 2 in two steps that cannot be swapped.
  - `predict` needs no 24Q2 response value.
    - It fits every arm once on all PRISM 19Q4 compounds, with the frozen code and
      hyperparameters.
    - It predicts each eligible sealed compound's selective profile, for both knowledge snapshots
      and for 20 seeds of each knowledge control.
    - It writes the predictions to tmp/ and their digest to PREDICTION_LOCK.json, write-once.
  - `evaluate` reads the 24Q2 response matrix, only after the owner authorises the download.
    - It refuses unless the file's MD5 matches the Figshare record, the freeze matches
      (`FREEZE.json`) and the predictions match their lock.
    - It then scores H1 (drug-specific prediction) and H2 (discovery utility), plus the strata,
      the context shift, the batch replication ceiling and calibration.
    - It writes RESULTS.json, write-once.
- Snapshots:
  - `hub2020` (primary, time-matched): Repurposing Hub targets and MoA from the 2020-03-24 file,
    four years before the outcome release. The training graph uses the same source class (PRISM
    19Q4 Hub columns).
  - `all_t0` (sensitivity): adds MAP-KG 2026 curated, aggregate-binding and biochemical edges.
    The snapshot postdates the outcomes.
- Gate: `predict` refuses (GATE_NOT_PASSED) unless DEVELOPMENT.json's gate reads PASS. The owner may
  override with `--despite-gate`; the lock records it and it must be disclosed as a deviation.
- Interfaces: `python confirm.py predict [--despite-gate]`, `python confirm.py evaluate --outcomes <path>`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import replace

import numpy as np
import pandas as pd

import develop as D
import models as M
from freeze import require_freeze
from sources import (CACHE, EDGE_TIER, HERE, OUTCOME_PROXIMAL, ROOT, load_ccle, mapkg_edges, mapkg_identity, sha256,
                     write_json)

SEALED = CACHE / "sealed"
LOCK = HERE / "PREDICTION_LOCK.json"
RESULTS = HERE / "RESULTS.json"
SNAPSHOTS = ("hub2020", "all_t0")
PRIMARY_SNAPSHOT = "hub2020"
ARMS = ("chem_full", "annot_full", "rkt_full", "know_full", "know_only", "density_full")
CONTROL_ARMS = ("know_full", "know_only")
CAMPAIGN = 64           # compounds per simulated T0 campaign
BUDGET = 32             # (compound, line) nominations per campaign, one confirmation well each
OUTCOME_MD5 = "042b15d3ebcc138a80a571b9286451ae"
ALPHA = 0.025           # one-sided, per hypothesis (H1, H2): Bonferroni over the two
MIN_LINES = 100         # a sealed compound is measured if it has at least this many panel lines
MIN_ID_MATCH = 0.9      # refuse to score if fewer requested compounds are found in the outcome matrix
MIN_ACTIVE = (json.loads((HERE / "POWER.json").read_text(encoding="utf-8"))["min_active"]   # power.py, before the freeze
              if (HERE / "POWER.json").is_file() else None)


def md5(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as s:
        for b in iter(lambda: s.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- tables for 19Q4 (train) + sealed (query)

def combined_tables() -> tuple[dict, dict]:
    T = dict(np.load(CACHE / "tables.npz", allow_pickle=False))
    census = json.loads((HERE / "SEALED_CENSUS.json").read_text(encoding="utf-8"))
    sc = pd.read_csv(HERE / "sealed_compounds.csv", keep_default_na=False)
    n19, ns = len(T["cores"]), len(sc)
    lines = list(T["lines"])
    panel = [l for l in census["panel_lines"] if l in set(lines)]
    newctx = census["new_context_lines"]

    # Knowledge edges of sealed compounds.
    rows = []
    for i, r in sc.iterrows():
        for g in [x.strip() for x in str(r["hub2020_target"]).split(",") if x.strip()]:
            rows.append((n19 + i, g, r["hub2020_relation"], "curated_hub"))
    comp = sc.set_index("core")[["name", "smiles"]]
    mapping, how = mapkg_identity(comp)
    mk = mapkg_edges(mapping)
    mk = mk[(mk["relation"] != "metabolic") & ~mk["provenance"].isin(OUTCOME_PROXIMAL) & (mk["provenance"].map(EDGE_TIER) == "T0")]
    pos = {c: n19 + i for i, c in enumerate(sc["core"])}
    rows += [(pos[c], g, rel, prov) for c, g, rel, prov in zip(mk["core"], mk["gene"], mk["relation"], mk["provenance"])]
    sealed_edges = pd.DataFrame(rows, columns=["drug", "gene", "relation", "provenance"]).drop_duplicates()

    # Gene universe: development genes plus sealed target genes with CCLE expression.
    genes = list(T["genes"])
    extra = sorted(set(sealed_edges["gene"]) - set(genes))
    ccle_extra = load_ccle(lines + newctx, set(extra)) if extra else None
    if ccle_extra is not None:
        extra = [g for g in extra if g in ccle_extra["expression"].columns]
    all_genes = genes + extra
    gi = {g: j for j, g in enumerate(all_genes)}
    sealed_edges = sealed_edges[sealed_edges["gene"].isin(gi)]

    def context(line_list: list[str], ccle_new) -> dict:
        """Context arrays over `line_list`, z-scored with the development lines' mean and SD."""

        ccle = load_ccle(line_list, set(all_genes))
        E = ccle["expression"].reindex(index=line_list, columns=all_genes)
        dev = load_ccle(lines, set(all_genes))["expression"].reindex(index=lines, columns=all_genes)
        mu, sd = dev.mean(0).to_numpy(), dev.std(0, ddof=0).to_numpy()
        Ev = E.to_numpy(np.float32)
        Z = np.where(sd > 1e-6, (Ev - mu) / np.maximum(sd, 1e-6), 0.0)
        Z = np.nan_to_num(Z).astype(np.float32)
        li = {l: k for k, l in enumerate(line_list)}
        hot = np.zeros((len(line_list), len(all_genes)), np.uint8)
        dele = np.zeros_like(hot)
        for g, l in ccle["mutations"]["hotspot"]:
            if g in gi and l in li:
                hot[li[l], gi[g]] = 1
        for g, l in ccle["mutations"]["deleterious"]:
            if g in gi and l in li:
                dele[li[l], gi[g]] = 1
        return {"expr_z": Z, "expressed": (np.nan_to_num(Ev) >= 1.0).astype(np.uint8), "hotspot": hot, "deleterious": dele,
                "expr_sd": sd.astype(np.float32), "lines": np.array(line_list)}

    ctx_dev = context(lines, None)
    ctx_new = context(newctx, None)            # the census kept only new lines with CCLE 19Q4 expression

    from build import fingerprints
    fp_s = fingerprints(list(sc["smiles"]))
    moa_names = list(T["moa_names"])
    mi = {m: j for j, m in enumerate(moa_names)}
    moa_rows = []
    for i, r in sc.iterrows():
        for m in [x.strip() for x in str(r["hub2020_moa"]).split(",") if x.strip()]:
            if m not in mi:
                mi[m] = len(moa_names)
                moa_names.append(m)
            moa_rows.append((n19 + i, mi[m]))
    prov_group = {"curated_hub": 0, "curated_mechanism": 0, "binding_aggregate": 1, "assay_biochemical": 1}
    src_index = D.SOURCE_INDEX
    rel_index = {"inh": 0, "act": 1, "bind": 2}
    TA = {
        "cores": np.concatenate([T["cores"], sc["core"].to_numpy(dtype=T["cores"].dtype)]),
        "lines": T["lines"], "genes": np.array(all_genes),
        "Y": np.vstack([T["Y"], np.full((ns, len(lines)), np.nan, np.float32)]),
        "fp": np.vstack([T["fp"], fp_s]),
        "edge_drug": np.concatenate([T["edge_drug"], sealed_edges["drug"].to_numpy(np.int32)]),
        "edge_gene": np.concatenate([T["edge_gene"], sealed_edges["gene"].map(gi).to_numpy(np.int32)]),
        "edge_rel": np.concatenate([T["edge_rel"], sealed_edges["relation"].map(rel_index).to_numpy(np.int8)]),
        "edge_prov": np.concatenate([T["edge_prov"], sealed_edges["provenance"].map(prov_group).to_numpy(np.int8)]),
        "edge_source": np.concatenate([T["edge_source"], sealed_edges["provenance"].to_numpy(dtype=T["edge_source"].dtype)]),
        "moa_names": np.array(moa_names), "moa_pairs": np.vstack([T["moa_pairs"], np.array(moa_rows, np.int32).reshape(-1, 2)]),
        "fold": np.concatenate([T["fold"], np.full(ns, 5, np.int8)]),
        "family": np.concatenate([T["family"], np.array([f"S:{c}" for c in sc["conn"]])]),
        "expr_z": ctx_dev["expr_z"], "expressed": ctx_dev["expressed"], "hotspot": ctx_dev["hotspot"],
        "deleterious": ctx_dev["deleterious"], "expr_sd": ctx_dev["expr_sd"],
    }
    meta = {"n19": n19, "ns": ns, "panel": panel, "ctx_new": ctx_new, "mapkg_match": how,
            "sealed_edges_by_provenance": {k: int(v) for k, v in sealed_edges["provenance"].value_counts().items()},
            "extra_genes": len(extra)}
    _ = src_index
    return TA, meta


def snapshot_edges(TA: dict, snapshot: str) -> D.Edges:
    E = D.t0_only(D.true_edges(TA))
    if snapshot == "hub2020":
        m = E.src == D.HUB
        E = replace(E, drug=E.drug[m], gene=E.gene[m], rel=E.rel[m], prov=E.prov[m], src=E.src[m])
    return E


def setup(TA: dict, n19: int) -> dict:
    train = np.arange(n19)
    test = np.arange(n19, len(TA["cores"]))
    Y = TA["Y"].astype(np.float64)
    G = np.nanmedian(Y[train], axis=0)
    S = M.residualise(Y, G)
    inner = np.array([D.h(TA["family"][i], "inner_confirm") % D.INNER for i in train])
    return {"f": 5, "train": train, "test": test, "G": G, "S": S, "inner": inner}


def chem_only(TA: dict, fs: dict) -> dict:
    K = M.tanimoto(TA["fp"], TA["fp"])
    train, test, S, inner = fs["train"], fs["test"], fs["S"], fs["inner"]
    iv = {"chem_knn": np.full((len(train), S.shape[1]), np.nan, np.float32)}
    ridge = {a: np.full((len(train), S.shape[1]), np.nan, np.float32) for a in M.RIDGE_ALPHAS}
    for k in range(D.INNER):
        q, r = train[inner == k], train[inner != k]
        iv["chem_knn"][inner == k] = M.knn_predict(K[np.ix_(q, r)], S[r], *M.CHEM_PARAMS)
        for a, p in M.KernelRidge(K[np.ix_(r, r)], S[r]).predict_many(K[np.ix_(q, r)], M.RIDGE_ALPHAS).items():
            ridge[a][inner == k] = p
    St = S[train]
    mse = {a: float(np.nanmean((St - p) ** 2)) for a, p in ridge.items()}
    alpha = min(mse, key=mse.get)
    iv["chem_ridge"] = ridge[alpha]
    te = {"chem_knn": M.knn_predict(K[np.ix_(test, train)], S[train], *M.CHEM_PARAMS).astype(np.float32),
          "chem_ridge": M.KernelRidge(K[np.ix_(train, train)], S[train]).predict(K[np.ix_(test, train)], alpha)}
    return {"inner": iv, "test": te, "alpha": alpha}


def calibrators(fs: dict, TA: dict, preds_inner: dict) -> dict:
    from sklearn.linear_model import LogisticRegression
    tr = fs["train"]
    event = (D.robust_z(fs["S"][tr]) <= -3) & (TA["Y"][tr] <= -1)
    m = np.isfinite(fs["S"][tr])
    rng = np.random.default_rng(D.SEED)
    out = {}
    for arm, P in preds_inner.items():
        xs, ys = -P[m], event[m]
        pick = rng.choice(len(xs), min(300_000, len(xs)), replace=False)
        cal = LogisticRegression(C=1.0).fit(xs[pick, None], ys[pick])
        out[arm] = [float(cal.intercept_[0]), float(cal.coef_[0, 0])]
    return out


def tc_new_context(TA: dict, kn: D.Knowledge, fs: dict, ctx_new: dict, n19: int, E: D.Edges) -> np.ndarray:
    """Target-context predictions for sealed compounds in lines outside the 19Q4 panel (raw, not residualised)."""

    model = M.TargetContext().fit(kn.F_tc, fs["S"], fs["G"], fs["train"][kn.has_tc[fs["train"]]])
    F, has = M.tc_features(E.drug, E.gene, E.rel, E.prov, len(TA["cores"]), ctx_new["expr_z"], ctx_new["expressed"],
                           ctx_new["hotspot"], ctx_new["deleterious"], typed=True, groups=(0, 1))
    q = fs["test"]
    out = np.full((len(q), F.shape[1]), np.nan, np.float32)
    ok = has[q]
    if ok.any():
        out[ok] = np.einsum("dlf,f->dl", F[q[ok]].astype(np.float64), model.beta / model.scale)
    return out


def gate_verdict() -> str:
    return json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))["gate"]["verdict"]


def predict(despite_gate: bool = False) -> None:
    if LOCK.is_file():
        raise SystemExit("PREDICTIONS_ALREADY_LOCKED: predictions are write-once")
    require_freeze()
    gate = gate_verdict()
    if gate != "PASS" and not despite_gate:
        raise SystemExit("GATE_NOT_PASSED: the development gate failed; stage 2 needs --despite-gate and a disclosed deviation")
    t0 = time.time()
    TA, meta = combined_tables()
    n19 = meta["n19"]
    fs = setup(TA, n19)
    chem = chem_only(TA, fs)
    SEALED.mkdir(parents=True, exist_ok=True)
    store, cal, weights, refusals = {}, {}, {}, {}
    for snap in SNAPSHOTS:
        E = snapshot_edges(TA, snap)
        kn = D.knowledge(E, TA, ablations=False)
        know = D.knowledge_routes(TA, [fs], kn, ablations=False)[0]
        inner_stacks = {}
        for arm in ARMS:
            Pt, Pi, w = D.stacked(fs, chem, know, arm, None)
            store[f"{snap}:{arm}"] = Pt.astype(np.float32)
            inner_stacks[arm] = Pi
            weights[f"{snap}:{arm}"] = w.tolist()
        cal[snap] = calibrators(fs, TA, inner_stacks)
        refusals[snap] = {"no_t0_target": int((~kn.has_tc[fs["test"]]).sum()),
                          "kn_typed_no_neighbour": int((~np.isfinite(know["test"]["kn_typed"]).any(1)).sum())}
        store[f"{snap}:tc_new_context"] = tc_new_context(TA, kn, fs, meta["ctx_new"], n19, E)
        # Prediction-time strata: annotated, no target gene shared with 19Q4, MoA never seen in 19Q4.
        old = E.drug < n19
        old_genes = set(E.gene[old].tolist())
        store[f"{snap}:has_target"] = kn.has_tc[fs["test"]]
        new_gene = np.ones(len(TA["cores"]), bool)
        for d, g in zip(E.drug[~old], E.gene[~old]):
            if g in old_genes:
                new_gene[d] = False
        store[f"{snap}:strict_new_target"] = kn.has_tc[fs["test"]] & new_gene[fs["test"]]
        old_moa = set(E.moa[E.moa[:, 0] < n19, 1].tolist())
        seen = np.zeros(len(TA["cores"]), bool)
        for d, mo in E.moa[E.moa[:, 0] >= n19]:
            if mo in old_moa:
                seen[d] = True
        store[f"{snap}:moa_seen"] = seen[fs["test"]]
        if snap == PRIMARY_SNAPSHOT:
            for kind in D.CONTROLS:
                for seed in range(D.CONTROL_SEEDS):
                    Ec = D.control_edges(E, kind, seed, TA)
                    knc = D.knowledge(Ec, TA, ablations=False)
                    kr = D.knowledge_routes(TA, [fs], knc, ablations=False)[0]
                    for arm in CONTROL_ARMS:
                        store[f"{snap}:{kind}:{seed}:{arm}"] = D.stacked(fs, chem, kr, arm, None)[0].astype(np.float16)
                    store[f"{snap}:{kind}:{seed}:tc_new_context"] = tc_new_context(TA, knc, fs, meta["ctx_new"], n19, Ec).astype(np.float16)
                    print(f"  control {kind}:{seed} ({round(time.time() - t0)} s)", flush=True)
    path = SEALED / "predictions.npz"
    np.savez_compressed(path, cores=TA["cores"][fs["test"]], lines=TA["lines"], ctx_lines=meta["ctx_new"]["lines"],
                        G19=fs["G"].astype(np.float64), **{
        k.replace(":", "__"): v for k, v in store.items()})
    lock = {"predictions": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path),
            "freeze_sha256": sha256(HERE / "FREEZE.json"), "chem_ridge_alpha": chem["alpha"], "stack_weights": weights,
            "calibrators": cal, "refusals": refusals, "meta": {k: v for k, v in meta.items() if k != "ctx_new"},
            "context_lines": int(len(meta["ctx_new"]["lines"])), "runtime_seconds": round(time.time() - t0),
            "outcome_file_md5_required": OUTCOME_MD5, "development_gate": gate, "run_despite_gate": gate != "PASS"}
    write_json(LOCK, lock)
    print("locked", lock["sha256"], flush=True)


# ---------------------------------------------------------------- evaluation (after authorised download)

def read_outcomes(path, cores: np.ndarray, lines: list[str]) -> np.ndarray:
    """REP.1M rows of the extended matrix (one 2.5 uM row per Broad core), on the given lines."""

    cl = pd.read_csv(ROOT / "tmp/knowledge_reality_20261013/sealed_metadata/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv")
    cl = cl[cl["screen"] == "REP.1M"].copy()
    cl["core"] = cl["IDs"].str.replace("BRD:", "", regex=False).str[:13]
    m = pd.read_csv(path, index_col=0)
    m = m.loc[m.index.intersection(cl["IDs"])]
    core_of = cl.set_index("IDs")["core"]
    by_core = m.groupby(core_of.reindex(m.index).values).mean()
    found = np.isin(np.asarray(cores), by_core.index).mean()
    if found < MIN_ID_MATCH:
        raise SystemExit(f"OUTCOME_ID_MISMATCH: {found:.2f} of requested compounds found; nothing written")
    return by_core.reindex(index=list(cores), columns=lines).to_numpy(np.float64)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def clusters_of(sc: pd.DataFrame) -> np.ndarray:
    """Sign-flip clusters: the first MoA string (the development family rule); unannotated compounds stand alone."""

    first = sc["hub2020_moa"].map(lambda s: sorted(x.strip() for x in s.split(","))[0] if s else "")
    return np.where(first == "", "none:" + sc.index.to_series().to_numpy(), first.to_numpy())


def replication_ceiling(outcomes: str, panel: list[str]) -> dict:
    """Selective-profile r of compounds screened in both releases (19Q4 primary and 24Q2 REP.1M)."""

    ov = pd.read_csv(HERE / "sealed_overlap.csv")
    T = np.load(CACHE / "tables.npz", allow_pickle=False)
    cores19 = list(T["cores"])
    lines19 = list(T["lines"])
    li19 = [lines19.index(l) for l in panel]
    Y19 = T["Y"].astype(np.float64)[:, li19]
    G19 = np.nanmedian(Y19, axis=0)
    S19 = M.residualise(Y19, G19)
    pairs = [(r.core, next(c for c in r.cores_19q4.split(";") if c in cores19)) for r in ov.itertuples()
             if any(c in cores19 for c in r.cores_19q4.split(";"))]
    if not pairs:
        return {"pairs": 0}
    Y24 = read_outcomes_any(outcomes, [p[0] for p in pairs], panel)
    sealed = pd.read_csv(HERE / "sealed_compounds.csv", keep_default_na=False)["core"]
    G24 = np.nanmedian(read_outcomes_any(outcomes, list(sealed), panel), axis=0)
    S24 = M.residualise(Y24, G24)
    i19 = np.array([cores19.index(p[1]) for p in pairs])
    r = D.drug_r(S19[i19], S24, G24)
    act = (((D.robust_z(S24) <= -3) & (Y24 <= -1)).sum(1) >= 5) | (((D.robust_z(S19[i19]) <= -3) & (Y19[i19] <= -1)).sum(1) >= 5)
    return {"pairs": len(pairs), "mean_r_all": float(r.mean()), "active_either": int(act.sum()),
            "mean_r_active_either": float(r[act].mean()) if act.any() else None, "r_by_pair": {p[0]: float(x) for p, x in zip(pairs, r)}}


def read_outcomes_any(path, cores: list[str], lines: list[str]) -> np.ndarray:
    """Like `read_outcomes` without the match guard (overlap compounds are a handful)."""

    cl = pd.read_csv(ROOT / "tmp/knowledge_reality_20261013/sealed_metadata/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv")
    cl = cl[cl["screen"] == "REP.1M"].copy()
    cl["core"] = cl["IDs"].str.replace("BRD:", "", regex=False).str[:13]
    m = pd.read_csv(path, index_col=0)
    m = m.loc[m.index.intersection(cl["IDs"])]
    by_core = m.groupby(cl.set_index("IDs")["core"].reindex(m.index).values).mean()
    return by_core.reindex(index=cores, columns=lines).to_numpy(np.float64)


def evaluate(outcomes: str) -> None:
    if RESULTS.is_file():
        raise SystemExit("RESULTS_ALREADY_WRITTEN: results are write-once")
    if md5(outcomes) != OUTCOME_MD5:
        raise SystemExit("OUTCOME_DIGEST_MISMATCH")
    require_freeze()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if sha256(HERE / "FREEZE.json") != lock["freeze_sha256"]:
        raise SystemExit("FREEZE_CHANGED_AFTER_LOCK")
    path = ROOT / lock["predictions"]
    if sha256(path) != lock["sha256"]:
        raise SystemExit("PREDICTIONS_CHANGED_AFTER_LOCK")
    P = dict(np.load(path, allow_pickle=False))
    cores, lines = P["cores"], list(P["lines"])
    census = json.loads((HERE / "SEALED_CENSUS.json").read_text(encoding="utf-8"))
    panel = [l for l in census["panel_lines"] if l in set(lines)]
    li = np.array([lines.index(l) for l in panel])
    Y = read_outcomes(outcomes, cores, panel)
    G = np.nanmedian(Y, axis=0)                               # target definition: the sealed batch's generic profile
    S = M.residualise(Y, G)
    event = (D.robust_z(S) <= -3) & (Y <= -1)
    measured = np.isfinite(Y).sum(1) >= MIN_LINES
    active = measured & (event.sum(1) >= 5)
    sc = pd.read_csv(HERE / "sealed_compounds.csv", keep_default_na=False).set_index("core").loc[cores]
    families = clusters_of(sc)
    prim = PRIMARY_SNAPSHOT
    a = active
    r = {f"{snap}:{arm}": D.drug_r(P[f"{snap}__{arm}"][:, li].astype(np.float64), S, G) for snap in SNAPSHOTS for arm in ARMS}

    # H1: drug-specific prediction on active compounds, primary snapshot, against chemistry and every null graph.
    h1 = D.paired(r[f"{prim}:know_full"][a], r[f"{prim}:chem_full"][a], families[a])
    ctrl = {}
    for kind in D.CONTROLS:
        gains = []
        for seed in range(D.CONTROL_SEEDS):
            rc = D.drug_r(P[f"{prim}__{kind}__{seed}__know_full"][:, li].astype(np.float64), S, G)
            gains.append(float((rc[a] - r[f"{prim}:chem_full"][a]).mean()))
        g = np.array(gains)
        ctrl[kind] = {"true_gain": h1["difference"], "null_mean": float(g.mean()), "null_p95": float(np.quantile(g, 0.95)),
                      "empirical_p": float((1 + (g >= h1["difference"]).sum()) / (1 + len(g)))}
    powered = int(a.sum()) >= MIN_ACTIVE
    h1_pass = h1["difference"] > 0 and h1["p_greater"] < ALPHA and all(c["true_gain"] > c["null_p95"] for c in ctrl.values())
    h1_verdict = "CONFIRMED" if h1_pass else ("NOT_CONFIRMED" if powered else "INCONCLUSIVE_UNDERPOWERED")

    # Secondary, descriptive: strata, the later snapshot, other baselines, specificity.
    strata = {"has_target": P[f"{prim}__has_target"], "strict_new_target": P[f"{prim}__strict_new_target"],
              "moa_unseen": ~P[f"{prim}__moa_seen"] & (sc["hub2020_moa"] != "").to_numpy(),
              "no_annotation": ~P[f"{prim}__has_target"] & (sc["hub2020_moa"] == "").to_numpy()}
    secondary = {}
    for name, m in strata.items():
        mm = a & m
        secondary[f"know_full-chem_full:{name}"] = (D.paired(r[f"{prim}:know_full"][mm], r[f"{prim}:chem_full"][mm], families[mm])
                                                   if mm.sum() >= 5 else {"units": int(mm.sum())})
    for x, y in (("know_full", "rkt_full"), ("know_full", "annot_full"), ("know_full", "density_full"), ("rkt_full", "chem_full"),
                 ("know_only", "chem_full")):
        secondary[f"{x}-{y}:active"] = D.paired(r[f"{prim}:{x}"][a], r[f"{prim}:{y}"][a], families[a])
    secondary["all_t0:know_full-chem_full:active"] = D.paired(r["all_t0:know_full"][a], r["all_t0:chem_full"][a], families[a])
    sp = {arm: D.specificity(P[f"{prim}__{arm}"][a][:, li].astype(np.float64), S[a], G) for arm in ("know_full", "chem_full")}
    secondary["specificity:know_full-chem_full:active"] = D.paired(sp["know_full"], sp["chem_full"], families[a])

    # Calibration of the selective-hit probability from the locked calibrators.
    calibration = {}
    mt = np.isfinite(S) & measured[:, None]
    for arm in ARMS:
        b0, b1 = lock["calibrators"][prim][arm]
        p = sigmoid(b0 + b1 * (-P[f"{prim}__{arm}"][:, li].astype(np.float64)))
        ok = mt & np.isfinite(p)
        brier, ece = D.brier_ece(p[ok], event[ok].astype(float))
        calibration[arm] = {"brier": brier, "ece": ece, "mean_p": float(p[ok].mean()), "event_rate": float(event[ok].mean())}

    # H2: simulated T0 campaigns of CAMPAIGN compounds, BUDGET nominations each; the zero arm uses the 19Q4
    # generic profile, which is all a cold-start campaign would have.
    order = sorted(range(len(cores)), key=lambda i: D.h(str(cores[i]), "campaign"))
    camps = [order[k:k + CAMPAIGN] for k in range(0, len(order), CAMPAIGN)]
    hits = {}
    G19 = P["G19"][li]
    for arm in ("zero",) + ARMS:
        per = []
        for c in camps:
            c = np.array(c)
            score = np.tile(-G19, (len(c), 1)) if arm == "zero" else -P[f"{prim}__{arm}"][c][:, li].astype(np.float64)
            score = np.where(measured[c][:, None] & np.isfinite(Y[c]), score, np.nan)   # unmeasured wells cannot be nominated
            picks = D.nominate(score, cores[c], budget=BUDGET)
            per.append(int(sum(event[c[i], l] for i, l in picks)))
        hits[arm] = per
    camp_ids = [f"c{k}" for k in range(len(camps))]
    h2 = D.cluster_signflip_test([x - y for x, y in zip(hits["know_full"], hits["chem_full"])], camp_ids, draws=10000, seed=D.SEED)
    h2_pass = sum(hits["know_full"]) > sum(hits["chem_full"]) and h2["p_greater"] < ALPHA
    h2_zero = D.cluster_signflip_test([x - y for x, y in zip(hits["know_full"], hits["zero"])], camp_ids, draws=10000, seed=D.SEED)

    # Context shift: target-context predictions in lines outside the 19Q4 panel (no chemistry arm can predict there).
    ctx_lines = list(P["ctx_lines"])
    Yc = read_outcomes(outcomes, cores, ctx_lines)
    Gc = np.nanmedian(Yc, axis=0)
    Sc = M.residualise(Yc, Gc)
    act_c = (np.isfinite(Yc).sum(1) >= 50) & ((((D.robust_z(Sc) <= -3) & (Yc <= -1)).sum(1)) >= 5)
    rc_true = D.drug_r(P[f"{prim}__tc_new_context"].astype(np.float64), Sc, Gc)
    has_c = P[f"{prim}__has_target"] & act_c
    ctx_null = {}
    for kind in D.CONTROLS:
        vals = [float(D.drug_r(P[f"{prim}__{kind}__{s}__tc_new_context"].astype(np.float64), Sc, Gc)[has_c].mean())
                for s in range(D.CONTROL_SEEDS)] if has_c.any() else []
        ctx_null[kind] = {"null_mean": float(np.mean(vals)) if vals else None, "null_p95": float(np.quantile(vals, 0.95)) if vals else None}

    out = {
        "stage": "confirmatory, sealed PRISM 24Q2 REP.1M", "protocol_sha256": sha256(HERE / "PROTOCOL.md"),
        "prediction_lock_sha256": sha256(LOCK),
        "population": {"compounds": int(len(cores)), "measured": int(measured.sum()), "active": int(active.sum()),
                       "min_active_for_power": MIN_ACTIVE, **{f"active_{k}": int((a & m).sum()) for k, m in strata.items()}},
        "arms": {k: {"mean_r_active": float(v[a].mean())} for k, v in r.items()},
        "H1": {"comparison": h1, "controls": ctrl, "verdict": h1_verdict},
        "H2": {"hits_by_arm": {k: int(sum(v)) for k, v in hits.items()}, "campaigns": len(camps), "budget_per_campaign": BUDGET,
               "nominations_per_arm": BUDGET * len(camps), "test_vs_chem_full": h2, "test_vs_zero": h2_zero,
               "verdict": "CONFIRMED" if h2_pass else "NOT_CONFIRMED"},
        "secondary": secondary, "calibration": calibration,
        "context_shift": {"lines": len(ctx_lines), "active_with_target": int(has_c.sum()),
                          "tc_mean_r": float(rc_true[has_c].mean()) if has_c.any() else None, "nulls": ctx_null},
        "replication_ceiling": replication_ceiling(outcomes, panel),
    }
    write_json(RESULTS, out)
    print(json.dumps({"H1": out["H1"]["verdict"], "H2": out["H2"]["verdict"]}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("predict", "evaluate"))
    ap.add_argument("--outcomes")
    ap.add_argument("--despite-gate", action="store_true", help="owner override when the development gate failed (a deviation)")
    args = ap.parse_args()
    if args.step == "predict":
        predict(args.despite_gate)
    else:
        if not args.outcomes:
            raise SystemExit("evaluate needs --outcomes <path to the authorised 24Q2 matrix>")
        evaluate(args.outcomes)


if __name__ == "__main__":
    main()
