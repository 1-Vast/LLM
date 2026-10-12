"""Block Q confirmation runner: routed knowledge transfer and certificate-planned profiling campaigns.

Frozen by ``FREEZE.json`` and executed once on the sealed GSE70138 query tier (compounds never
profiled in GSE92742). Modes:
  python confirm.py --dry-run-phase1      pipeline check on development data (phase-1 fold 0)
  python confirm.py --dry-run-synthetic   phase-2 reference tier with random query responses
  python confirm.py --confirm             opens the sealed tier (refused before FREEZE.json)
The dry runs never read the sealed file. Everything registered is in ``PROTOCOL.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import campaign as C
import engine
import metrics as M
import rkt
from dev_common import CACHE, N_FOLDS, fold_of, knowledge_tokens, load_phase1, phase1_knowledge, vehicle_thresholds
from dev_mono2 import monolithic
from dev_routes2 import N_REF, h
from pool import SPECIFIC_ROUTES, fit_nested

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P2 = ROOT / "data/external/lincs_l1000_phase2/derived/blockq_phase2_reference.npz"
P1_PERT = ROOT / "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz"
SUBLIB = 61
MIN_LINES_P2 = 5
BUDGETS = (0.5, 1.0, 2.0)
PRIMARY_BUDGET = 1.0
MONO_RHO = 0.118           # development out-of-fold specific cosine of the monolithic ridge (dev_mono2)
AUDIT_REGIMES = ("A", "A1", "B")


@dataclass
class Inputs:
    name: str
    Y: np.ndarray            # n x L x p responses (references and library)
    ref: np.ndarray          # n boolean: reference compounds
    keys: list
    library: np.ndarray      # row indices of library compounds
    grid: np.ndarray         # n_lib x L: profileable cells
    records: list
    fps: np.ndarray
    know: np.ndarray
    targets: list
    KD: np.ndarray
    kd_genes: list
    thr: np.ndarray
    lines: list
    genes: list
    notes: dict


# ----------------------------------------------------------------------------- inputs

def inchikey_skeletons_profiled(p2: dict) -> set[str]:
    """InChIKey connectivity blocks of every compound with a 10 uM / 24 h response in either release."""
    z = load_phase1()
    pert1 = pd.read_csv(P1_PERT, sep="\t", low_memory=False).drop_duplicates("pert_id").set_index("pert_id")
    out = set()
    for pids in z["pert_ids"]:
        for p in str(pids).split("|"):
            if p in pert1.index and isinstance(pert1.loc[p, "inchi_key"], str):
                out.add(pert1.loc[p, "inchi_key"].split("-")[0])
    out |= {r["inchikey"].split("-")[0] for r in p2["ref"] if r["inchikey"]}
    return out


def phase2_inputs(query_cp: np.ndarray, query_keys: np.ndarray) -> Inputs:
    from knowledge import build_knowledge, morgan_matrix
    z = np.load(P2, allow_pickle=True)
    kn = json.loads((CACHE / "phase2_knowledge.json").read_text(encoding="utf-8"))
    if [r["key"] for r in kn["query"]] != [str(k) for k in query_keys] or [r["key"] for r in kn["ref"]] != [str(k) for k in z["ref_compound"]]:
        raise RuntimeError("COMPOUND_ORDER_MISMATCH")
    lines = [str(x) for x in z["line"]]
    rows = kn["ref"] + kn["query"]
    n_ref = len(kn["ref"])
    Y = np.concatenate([z["ref_cp"].astype(np.float32), query_cp.astype(np.float32)], 0)
    ref = np.zeros(len(rows), bool); ref[:n_ref] = True
    dup = inchikey_skeletons_profiled(kn)
    is_dup = np.array([bool(r["inchikey"]) and r["inchikey"].split("-")[0] in dup for r in kn["query"]])
    n_sig = np.array([r["n_sig"] for r in kn["query"]])
    eligible = ~is_dup & ((n_sig > 0).sum(1) >= MIN_LINES_P2)
    library = n_ref + np.flatnonzero(eligible)
    meta_grid = n_sig[eligible] > 0
    grid = meta_grid & np.isfinite(Y[library][..., 0])     # registered: a cell needs metadata and a response
    records = build_knowledge([r["key"] for r in rows], [r["name"] for r in rows], [r["cids"] for r in rows],
                              [r["smiles"] for r in rows])
    fps = morgan_matrix([r["smiles"] for r in rows])
    know, _ = knowledge_tokens(records)
    targets = [r.signed_targets() for r in records]
    veh, vline = z["vehicle"].astype(np.float64), z["vehicle_line"]
    thr = np.array([np.quantile(np.linalg.norm(veh[vline == l], axis=1), 0.95) for l in lines])
    notes = {"n_query": int(len(kn["query"])), "excluded_duplicate_structure": int(is_dup.sum()),
             "excluded_few_lines": int((~is_dup & ~eligible).sum()), "n_library": int(eligible.sum()),
             "grid_cells": int(grid.sum()), "grid_metadata_without_response": int((meta_grid & ~grid).sum())}
    return Inputs("phase2", Y, ref, [r["key"] for r in rows], library, grid, records, fps, know, targets,
                  z["xpr"].astype(np.float32), [str(g) for g in z["xpr_gene"]], thr, lines,
                  [str(g) for g in z["gene_symbol"]], notes)


def phase1_dryrun_inputs(f: int = 0) -> Inputs:
    z = load_phase1()
    records, fps, know, vocab, targets = phase1_knowledge()
    Y = z["cp"].astype(np.float32)
    keys = [str(k) for k in z["compound"]]
    folds = np.array([fold_of(k) for k in keys])
    nlines = np.isfinite(Y[..., 0]).sum(1)
    pool = sorted(np.flatnonzero((folds != f) & (nlines >= 6)), key=lambda i: h(f"ref{f}:{keys[i]}"))
    ref = np.zeros(len(keys), bool); ref[pool[:N_REF]] = True
    library = np.array(sorted(np.flatnonzero((folds == f) & (nlines >= 6))))
    return Inputs("phase1_dryrun", Y, ref, keys, library, np.isfinite(Y[library, :, 0]), records, fps, know, targets,
                  z["kd"].astype(np.float32), [str(g) for g in z["kd_gene"]], vehicle_thresholds(z),
                  [str(x) for x in z["line"]], [str(g) for g in z["gene_symbol"]], {"fold": f})


def confirmation_pooler(exclude_fold: int | None = None):
    """Meta-models fitted on the phase-1 development route table (dev2), nested by compound fold."""
    tag = "all" if exclude_fold is None else f"no{exclude_fold}"
    path = CACHE / f"pooler_{tag}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes()), path
    z2 = dict(np.load(CACHE / "dev2_routes.npz"))
    tr = np.ones(len(z2["fold"]), bool) if exclude_fold is None else z2["fold"] != exclude_fold
    G = z2["G_table"][z2["fold"][tr], z2["line"][tr]].astype(np.float64)
    gam = float(np.mean(z2["gammas"] if exclude_fold is None else z2["gammas"][np.arange(N_FOLDS) != exclude_fold]))
    pooler = fit_nested(z2["F"][tr].astype(np.float64), {r: z2[f"av_{r}"][tr] for r in SPECIFIC_ROUTES},
                        {r: z2[f"pred_{r}"][tr].astype(np.float64) for r in SPECIFIC_ROUTES}, G,
                        z2["truth"][tr].astype(np.float64), z2["active"][tr], z2["fold"][tr], gam)
    path.write_bytes(pickle.dumps(pooler))
    return pooler, path


# ----------------------------------------------------------------------------- prediction tier

def prediction_tier(inp: Inputs, atlas, maps, G, gamma, pooler) -> pd.DataFrame:
    thr, L = inp.thr, len(inp.lines)
    lib_grid = np.zeros((len(inp.keys), L), bool); lib_grid[inp.library] = inp.grid
    out = []
    cache: dict = {}
    for T in range(L):
        q = inp.library[inp.grid[:, T]]
        if not len(q):
            continue
        truth = atlas.Yc[q, T].astype(np.float64)
        active = np.linalg.norm(inp.Y[q, T].astype(np.float64), axis=1) > thr[T]
        measured = lib_grid[q]
        one = np.zeros_like(measured)
        for i, c in enumerate(q):
            others = [s for s in range(L) if s != T and measured[i, s]]
            if others:
                one[i, others[h(f"vis:{inp.keys[c]}:{T}") % len(others)]] = True
        Gq = np.repeat(G[T][None], len(q), 0)
        mono = monolithic(inp.Y.astype(np.float64), inp.fps, inp.know, inp.ref, q, np.full(len(q), T))
        mono_dec = rkt.unit_rows(gamma * Gq + MONO_RHO * np.sqrt(1 - gamma ** 2) * rkt.unit_rows(M.perp(mono, Gq)))
        for regime, vis in (("A", measured), ("A1", one), ("B", np.zeros_like(measured))):
            blk = engine.query_block(atlas, q, T, vis, maps, thr, cache)
            direction, s, cert, ecos = engine.predict_block(blk, pooler, G, gamma)
            top = np.max(np.stack([np.where(blk.routes[r].available, blk.routes[r].support[:, 0], 0)
                                   for r in ("pheno", "chem", "know")], 1), 1)
            rec = {"compound": q, "key": [inp.keys[c] for c in q], "line": T, "regime": regime, "active": active,
                   "pooled": rkt.centred_cosine(direction, truth), "pooled_specific": M.specific_cosine(direction, truth, Gq),
                   "generic": rkt.centred_cosine(Gq, truth), "expected": ecos, "rho": cert.rho, "p_active": cert.p_active,
                   "refusal": cert.refusal, "applicability": top,
                   "mono_raw": rkt.centred_cosine(mono, truth), "mono_decomposed": rkt.centred_cosine(mono_dec, truth)}
            for r in SPECIFIC_ROUTES:
                o = blk.routes[r]
                rec[f"{r}_available"] = o.available
                rec[f"{r}"] = np.where(o.available, rkt.centred_cosine(o.pred, truth), np.nan)
                rec[f"{r}_specific"] = np.where(o.available, M.specific_cosine(o.pred, truth, Gq), np.nan)
            g = rkt.route_genetic(atlas, q, T)
            rec["genetic_available"] = g.available
            rec["genetic_specific"] = np.where(g.available, M.specific_cosine(g.pred, truth, Gq), np.nan)
            out.append(pd.DataFrame(rec))
    return pd.concat(out, ignore_index=True)


def prediction_hypotheses(df: pd.DataFrame) -> dict:
    res = {}
    for regime in AUDIT_REGIMES:
        d = df[(df.regime == regime) & df.active]
        if d.key.nunique() < 2:
            res[regime] = {"n_active_cells": int(len(d)), "refusal": "TOO_FEW_ACTIVE_COMPOUNDS"}
            continue
        allr = df[df.regime == regime]
        b = {"n_active_cells": int(len(d)), "n_compounds": int(d.key.nunique()),
             "pooled_centred": float(d.pooled.mean()), "generic_centred": float(d.generic.mean()),
             "expected_centred": float(d.expected.mean()), "pooled_specific": float(d.pooled_specific.mean()),
             "refusal_fraction": float((d.refusal != "").mean()),
             "activity_auroc": float(roc_auc_score(allr.active, allr.p_active)) if allr.active.nunique() == 2 else None,
             "pooled_vs_generic": M.paired_cluster_test(d.pooled.values, d.generic.values, d.key.values)}
        ctx = d[d.context_available]
        if len(ctx):
            b["context_coverage"] = float(len(ctx) / len(d))
            b["context_centred"] = float(ctx.context.mean())
            b["pooled_vs_context"] = M.paired_cluster_test(ctx.pooled.values, ctx.context.values, ctx.key.values)
        for r in SPECIFIC_ROUTES:
            dd = d[d[f"{r}_available"]]
            b[f"{r}_route"] = {"coverage": float(len(dd) / max(len(d), 1)), "centred": float(dd[r].mean()) if len(dd) else None,
                               "specific": float(dd[f"{r}_specific"].mean()) if len(dd) else None}
        b["mono_decomposed_centred"] = float(d.mono_decomposed.mean())
        b["mono_raw_centred"] = float(d.mono_raw.mean())
        b["pooled_vs_monolithic"] = M.paired_cluster_test(d.pooled.values, d.mono_decomposed.values, d.key.values)
        loss = 1 - d.pooled.values
        b["aurc"] = M.aurc_difference(d.expected.values, d.applicability.values, loss, d.key.values)
        b["aurc_random"] = float(loss.mean())
        b["aurc_oracle"] = M.aurc(-loss, loss)
        gen = d[d.genetic_available]
        b["genetic_route"] = {"coverage": float(len(gen) / max(len(d), 1)),
                              "specific": float(gen.genetic_specific.mean()) if len(gen) else None}
        res[regime] = b
    return res


# ----------------------------------------------------------------------------- campaign tier

def campaigns(inp: Inputs, atlas, maps, pooler, G, gamma, kappa, tag: str):
    order = sorted(range(len(inp.library)), key=lambda j: h(f"{tag}-lib:{inp.keys[inp.library[j]]}"))
    n_sub = max(1, len(order) // SUBLIB)
    raw = np.linalg.norm(np.nan_to_num(inp.Y[inp.ref]), axis=2)
    have = np.isfinite(inp.Y[inp.ref][..., 0])
    ref_rate = ((raw > inp.thr[None]) & have).sum(0) / np.maximum(have.sum(0), 1)
    out = []
    for s in range(n_sub):
        sel = np.array(order[s::n_sub])
        lib = inp.library[sel]
        recs = [inp.records[i] for i in lib]
        meta = {"lines": inp.lines, "genes": inp.genes, "ref_rate": ref_rate, "names": [r.name for r in recs],
                "moa": [sorted(r.hub_moa) for r in recs],
                "targets": [sorted(r.hub_targets) or sorted(r.mapkg)[:6] for r in recs]}
        out.append((C.Campaign(f"{tag}{s}", atlas, maps, pooler, G, gamma, inp.thr, lib, inp.grid[sel], kappa), meta))
    return out


def run_campaigns(camps, agent, llm_arms, det_arms=C.DETERMINISTIC_ARMS, budgets=BUDGETS, workers: int = 6):
    import llm_arms as LA
    rows = []
    t0 = time.time()
    for c, meta in camps:
        for b in budgets:
            W = int(round(b * len(c.library)))
            for arm in det_arms:
                r = C.run_arm(c, arm, W)
                r.update({"campaign": c.cid, "budget": b, "W": W, "n_lib": len(c.library), "n_cells": int(c.grid.sum())})
                rows.append(r)
        print(f"  {c.cid} deterministic done {time.time() - t0:.0f}s", flush=True)
    jobs = [(c, meta, arm) for c, meta in camps for arm in llm_arms]

    def one(job):
        c, meta, arm = job
        W = int(round(PRIMARY_BUDGET * len(c.library)))
        r = LA.run_llm_arm(c, arm, W, meta, agent)
        r.update({"campaign": c.cid, "budget": PRIMARY_BUDGET, "W": W, "n_lib": len(c.library), "n_cells": int(c.grid.sum())})
        print(f"  {c.cid} {arm} {r['utility']:.3f} errors {len(r['errors'])} fallback {r['fallback_cells']} {time.time() - t0:.0f}s", flush=True)
        return r

    if jobs:
        with ThreadPoolExecutor(workers) as ex:
            rows += list(ex.map(one, jobs))
    return pd.DataFrame(rows)


CAMPAIGN_CONTRASTS = {
    # name: (arm a, arm b, sided) evaluated at the primary budget; one-sided means a > b
    "C1_sparse_hub_vs_dense": ("sparse_hub", "dense", "greater"),
    "C2_maestro_vs_sparse_hub": ("maestro", "sparse_hub", "greater"),
    "C3_maestro_vs_activity_greedy": ("maestro", "activity_greedy", "greater"),
    "C3b_maestro_vs_ad_uncertainty": ("maestro", "ad_uncertainty", "greater"),
    "C4_maestro_vs_llm_conv_vc": ("maestro", "llm_conv_vc", "greater"),
    "C4b_llm_conv_vc_vs_llm_no_vc": ("llm_conv_vc", "llm_no_vc", "greater"),
    "C5_maestro_llm_vs_maestro": ("maestro_llm", "maestro", "two_sided"),
    "C6_sparse_random_vs_dense": ("sparse_random", "dense", "greater"),
    "C7_maestro_vs_vc_only": ("maestro", "vc_only", "greater"),
    "C8_maestro_static_vs_sparse_hub": ("maestro_static", "sparse_hub", "greater"),
}


def hypothesis_p(res: dict, h: dict):
    """(estimate, p) of one registered hypothesis from the raw results, or (None, refusal code)."""
    if h["tier"] == "prediction":
        reg = res["prediction"].get(h["regime"], {})
        if "refusal" in reg:
            return None, reg["refusal"]
        if h["statistic"] == "aurc":
            a = reg["aurc"]
            return a["estimate"], a["p_le_zero"]
        t = reg.get(h["statistic"])
        if t is None:
            return None, "NOT_RUN"
        return t["estimate"], t["p_greater"] if h["sided"] == "greater" else t["p_two_sided"]
    c = res["campaigns"]["contrasts"].get(f"{h['contrast']}@{h['budget']}")
    if c is None:
        return None, "NOT_RUN"
    return c["mean_difference"], c["p"]


def verdicts(res: dict, protocol: dict) -> dict:
    out = {"primary": {}, "secondary": {}}
    for group, alpha in (("primary", protocol["primary_alpha_one_sided"]), ("secondary", protocol["secondary_alpha_one_sided"])):
        for h in protocol[group]:
            est, p = hypothesis_p(res, h)
            if est is None:
                out[group][h["id"]] = {"status": p}
                continue
            if h["sided"] == "two_sided":
                status = "DIFFERENT" if p <= alpha else "NO_DIFFERENCE_DETECTED"
            else:
                status = "PASS" if p <= alpha and est > 0 else "FAIL"
            out[group][h["id"]] = {"status": status, "estimate": est, "p": p, "alpha": alpha}
    passed = {k for k, v in out["primary"].items() if v["status"] == "PASS"}
    claims = {name: ("CONFIRMED" if set(ids) <= passed else "NOT_CONFIRMED") for name, ids in protocol["claims"].items()}
    out["claims"] = claims
    out["headline"] = ("CONFIRMED" if all(v == "CONFIRMED" for v in claims.values())
                       else "PARTIAL" if passed else "NOT_CONFIRMED")
    out["passed_primary"] = sorted(passed)
    return out


def campaign_hypotheses(df: pd.DataFrame) -> dict:
    sys.path.insert(0, str(ROOT))
    from tools.evaluation.scoring import cluster_signflip_test
    res = {"means": {}, "contrasts": {}}
    for b in sorted(df.budget.unique()):
        sub = df[df.budget == b]
        res["means"][str(b)] = sub.groupby("arm")[["utility", "usable", "utility_vcfill", "utility_naivefill", "rounds", "wells"]].mean().round(4).to_dict("index")
    for b in sorted(df.budget.unique()):
        sub = df[df.budget == b].set_index(["arm", "campaign"]).utility
        for name, (a, bb, sided) in CAMPAIGN_CONTRASTS.items():
            if a not in sub.index.get_level_values(0) or bb not in sub.index.get_level_values(0):
                continue
            d = (sub.loc[a] - sub.loc[bb]).dropna()
            t = cluster_signflip_test(d.values.tolist(), d.index.tolist())
            res["contrasts"][f"{name}@{b}"] = {"a": a, "b": bb, "sided": sided, "mean_difference": float(d.mean()),
                                               "favour": int((d > 0).sum()), "oppose": int((d < 0).sum()),
                                               "p": t["p_greater"] if sided == "greater" else t["p_two_sided"],
                                               "exact": t["exact"], "min_attainable_one_sided_p": t["min_attainable_one_sided_p"]}
    return res


# ----------------------------------------------------------------------------- driver

def build_world(inp: Inputs, pooler):
    atlas = rkt.build_atlas(inp.Y, inp.ref, inp.fps, inp.know, inp.targets, inp.KD, inp.kd_genes)
    maps = rkt.context_maps(atlas)
    G = engine.generic_direction(atlas, inp.thr)
    gamma = engine.gamma_estimate(atlas, inp.thr, G)
    kappa = C.transfer_specific(atlas, maps, G, inp.thr)
    return atlas, maps, G, gamma, kappa


def execute(inp: Inputs, pooler, out_dir: Path, *, tag: str, agent=None, llm_arms=(), max_campaigns=None) -> dict:
    t0 = time.time()
    atlas, maps, G, gamma, kappa = build_world(inp, pooler)
    print(f"[{inp.name}] world built: gamma {gamma:.4f}, maps {len(maps)}, {time.time() - t0:.0f}s", flush=True)
    pred = prediction_tier(inp, atlas, maps, G, gamma, pooler)
    print(f"[{inp.name}] prediction tier {len(pred)} rows {time.time() - t0:.0f}s", flush=True)
    camps = campaigns(inp, atlas, maps, pooler, G, gamma, kappa, tag)
    if max_campaigns is not None:
        camps = camps[:max_campaigns]
    cdf = run_campaigns(camps, agent, llm_arms)
    out_dir.mkdir(parents=True, exist_ok=True)
    pred.to_parquet(out_dir / "prediction_rows.parquet")
    cdf.to_json(out_dir / "campaign_rows.json", orient="records", indent=0, default_handler=str)
    res = {"inputs": inp.notes, "gamma": gamma, "n_maps": len(maps), "kappa_mean": float(kappa[kappa > 0].mean()),
           "n_campaigns": len(camps), "library_sizes": [len(c.library) for c, _ in camps],
           "prediction": prediction_hypotheses(pred), "campaigns": campaign_hypotheses(cdf),
           "seconds": round(time.time() - t0, 1)}
    if agent is not None and agent.ledger is not None:
        res["provider_spend_usd"] = round(agent.ledger.session_total_usd, 6)
        res["provider_calls"] = len(agent.ledger.entries)
    return res


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run-phase1", action="store_true")
    g.add_argument("--dry-run-synthetic", action="store_true")
    g.add_argument("--confirm", action="store_true")
    ap.add_argument("--max-campaigns", type=int, default=None)
    ap.add_argument("--llm", choices=("live", "offline", "none"), default="none")
    a = ap.parse_args()
    import llm_arms as LA
    if a.confirm:
        import verify_freeze
        if (HERE / "results" / "raw_results.json").exists():
            raise RuntimeError("ALREADY_RUN: the confirmation is executed once")
        verify_freeze.check()            # refuses unless every frozen file matches its hash
        from extract_phase2 import load_query
        q = load_query()                 # refuses with TIER_SEALED before FREEZE.json
        inp = phase2_inputs(q["cp"], q["compound"])
        pooler, _ = confirmation_pooler(None)
        (HERE / "results").mkdir(exist_ok=True)
        agent = LA.Agent(HERE / "results" / "llm_cache.jsonl", HERE / "results" / "llm_spend.json", ceiling_usd=3.0)
        res = execute(inp, pooler, HERE / "results", tag="confirm", agent=agent, llm_arms=LA.LLM_ARMS)
        (HERE / "results" / "raw_results.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        protocol = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
        out = {"verdicts": verdicts(res, protocol), "raw": "results/raw_results.json",
               "frozen_utc": json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))["frozen_utc"],
               "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        (HERE / "RESULTS.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
        print(json.dumps(out["verdicts"], indent=1, default=str))
        return
    if a.dry_run_phase1:
        inp = phase1_dryrun_inputs(0)
        pooler, _ = confirmation_pooler(0)
        tag = "dry"
    else:
        z = np.load(P2, allow_pickle=True)
        kn = json.loads((CACHE / "phase2_knowledge.json").read_text(encoding="utf-8"))
        rng = np.random.default_rng(0)
        n_sig = np.array([r["n_sig"] for r in kn["query"]])
        fake = rng.normal(size=(len(kn["query"]), len(z["line"]), z["ref_cp"].shape[2])).astype(np.float32)
        fake *= np.where(rng.random(fake.shape[:2]) < 0.1, 3.0, 1.0)[..., None].astype(np.float32)  # some active cells
        fake[n_sig == 0] = np.nan
        inp = phase2_inputs(fake, z["query_compound"])
        inp.name = "synthetic"
        pooler, _ = confirmation_pooler(None)
        tag = "syn"
    agent = None
    if a.llm != "none":
        agent = LA.Agent(CACHE / "llm_dev_cache.jsonl", CACHE / "llm_dev_spend.json", ceiling_usd=3.0, offline=a.llm == "offline")
    res = execute(inp, pooler, CACHE / f"dryrun_{inp.name}", tag=tag, agent=agent,
                  llm_arms=LA.LLM_ARMS if agent else (), max_campaigns=a.max_campaigns)
    res["verdicts_dry"] = verdicts(res, json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8")))
    (CACHE / f"dryrun_{inp.name}.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("inputs", "gamma", "n_campaigns", "seconds")}, default=str))


if __name__ == "__main__":
    main()
