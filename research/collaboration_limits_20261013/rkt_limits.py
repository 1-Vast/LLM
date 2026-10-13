"""L1000 workstream: why RKT degrades without an anchor, and why memory has not produced learning.

File summary
- Path: research/collaboration_limits_20261013/rkt_limits.py
- Purpose: exploratory analyses on the exposed Block Q tier (702 GSE70138 compounds, 7 lines),
  pre-specified in PROTOCOL.md. They explain; they do not confirm.
- Core points:
  - Inputs come read-only from `research/knowledge_transfer_20261012` (its input builder, its sealed
    query loader, which now opens because that study is frozen and run, and its GSE92742 certifier).
  - Predictions use the promoted `virtual_cell.knowledge_transfer` (parity with the study shown 2026-10-12).
  - `ceiling`: how much a single analogue could ever recover, and how specific directions relate
    across compounds versus across lines of one compound.
  - `curve`: accuracy against reference-library size.
  - `memory`: sequential campaigns where measured cells become references, against no memory,
    shuffled memory and pseudo-label (self-training) memory.
- Commands: ceiling, curve, memory.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
BLOCKQ = ROOT / "research/knowledge_transfer_20261012"
sys.path.insert(0, str(BLOCKQ))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
import confirm as Q  # noqa: E402  (frozen Block Q module, read-only)
from extract_phase2 import load_query  # noqa: E402
from maestro.transfer_value import sparse_transfer_design  # noqa: E402
from virtual_cell import knowledge_transfer as kt  # noqa: E402


def h(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def write_json(name: str, value) -> None:
    (STUDY / name).write_text(json.dumps(value, indent=2, allow_nan=False, default=float) + "\n", encoding="utf-8")


def world():
    q = load_query()
    inp = Q.phase2_inputs(q["cp"], q["compound"])
    pooler = pickle.loads((BLOCKQ / "cache/pooler_all.pkl").read_bytes())
    cert = kt.Certifier(pooler.act_model, pooler.route_models, pooler.pool_model, pooler.rho_min)
    return inp, cert


def active_mask(inp) -> np.ndarray:
    """Library x lines: measured and active (raw norm above the vehicle 95th percentile)."""
    Y = inp.Y[inp.library].astype(np.float64)
    norm = np.linalg.norm(np.nan_to_num(Y), axis=2)
    return inp.grid & (norm > inp.thr[None])


def one_visible(inp, rows: np.ndarray, T: int) -> np.ndarray:
    """Block Q's A1 rule: one other measured line per query, chosen by hash."""
    lib_pos = {r: j for j, r in enumerate(inp.library)}
    vis = np.zeros((len(rows), len(inp.lines)), bool)
    for i, c in enumerate(rows):
        g = inp.grid[lib_pos[c]]
        others = [s for s in range(len(inp.lines)) if s != T and g[s]]
        if others:
            vis[i, others[Q.h(f"vis:{inp.keys[c]}:{T}") % len(others)]] = True
    return vis


# ---------------------------------------------------------------- question 2
def ceiling() -> dict:
    import pandas as pd
    from knowledge import tanimoto
    inp, cert = world()
    atlas = kt.TransferAtlas.build(inp.Y, inp.ref, inp.fps, inp.know, inp.thr)
    act = active_mask(inp)
    L = len(inp.lines)
    pred = pd.read_parquet(BLOCKQ / "results/prediction_rows.parquet")
    refs = np.flatnonzero(inp.ref)
    rows = []
    for T in range(L):
        R = atlas.ref_rows(T)
        U = kt.unit_rows(atlas.Yc[R, T].astype(np.float64))
        Up = kt.unit_rows(kt.perp(atlas.Yc[R, T].astype(np.float64), atlas.G[T][None]))
        for j in np.flatnonzero(act[:, T]):
            c = inp.library[j]
            y = atlas.Yc[c, T].astype(np.float64)
            cos = U @ kt.unit_rows(y[None])[0]
            spec = Up @ kt.unit_rows(kt.perp(y[None], atlas.G[T][None]))[0]
            sim = tanimoto(inp.fps[R], inp.fps[c])
            nn = int(np.argmax(sim))
            rows.append({"compound": int(c), "line": T, "oracle_donor_cosine": float(cos.max()),
                         "oracle_donor_specific": float(spec.max()), "oracle_donor_tanimoto": float(sim[int(np.argmax(cos))]),
                         "nearest_structure_tanimoto": float(sim[nn]), "nearest_structure_cosine": float(cos[nn]),
                         "top5_oracle_mean_cosine": float(np.sort(cos)[-5:].mean())})
    df = pd.DataFrame(rows)
    pb = pred[(pred.regime == "B") & pred.active][["compound", "line", "pooled"]].rename(columns={"pooled": "regime_B"})
    pa1 = pred[(pred.regime == "A1") & pred.active][["compound", "line", "pooled"]].rename(columns={"pooled": "regime_A1"})
    df = df.merge(pb, on=["compound", "line"]).merge(pa1, on=["compound", "line"])
    bins = [0, .3, .4, .5, .6, .8, 1.01]
    df["tanimoto_bin"] = pd.cut(df.nearest_structure_tanimoto, bins, right=False)
    by_bin = df.groupby("tanimoto_bin", observed=True).agg(n=("regime_B", "size"), regime_B=("regime_B", "mean"),
                                                           regime_A1=("regime_A1", "mean"),
                                                           oracle_donor=("oracle_donor_cosine", "mean")).reset_index()
    # Pair structure of specific directions among active references.
    rng = np.random.default_rng(h("pairs") % 2 ** 32)
    moa = [inp.records[r].hub_moa for r in range(len(inp.keys))]
    tgt = [inp.records[r].target_set() for r in range(len(inp.keys))]
    raw_ref = np.linalg.norm(np.nan_to_num(inp.Y[refs].astype(np.float64)), axis=2) > inp.thr[None]
    P = {}
    for T in range(L):
        a = refs[raw_ref[:, T] & np.isfinite(atlas.Yc[refs, T, 0])]
        P[T] = (a, kt.unit_rows(kt.perp(atlas.Yc[a, T].astype(np.float64), atlas.G[T][None])))
    pairs = {"same_compound_other_line_raw": [], "same_compound_other_line_mapped": [], "same_moa": [], "shared_target": [],
             "tanimoto_ge_0_6": [], "random": []}
    for s in range(L):
        for t in range(L):
            if s == t or (s, t) not in atlas.maps:
                continue
            a_s, u_s = P[s]
            a_t, u_t = P[t]
            common, i_s, i_t = np.intersect1d(a_s, a_t, return_indices=True)
            pairs["same_compound_other_line_raw"] += list((u_s[i_s] * u_t[i_t]).sum(1))
            B = atlas.maps[(s, t)].B.astype(np.float64)
            mapped = kt.unit_rows(kt.perp(atlas.Yc[common, s].astype(np.float64) @ B, atlas.G[t][None]))
            pairs["same_compound_other_line_mapped"] += list((mapped * u_t[i_t]).sum(1))
    for T in range(L):
        a, u = P[T]
        sim = u @ u.T
        fp = inp.fps[a]
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                if moa[a[i]] and moa[a[i]] & moa[a[j]]:
                    pairs["same_moa"].append(sim[i, j])
                if tgt[a[i]] and tgt[a[i]] & tgt[a[j]]:
                    pairs["shared_target"].append(sim[i, j])
            tt = tanimoto(fp, fp[i])
            for j in np.flatnonzero(tt >= .6):
                if j > i:
                    pairs["tanimoto_ge_0_6"].append(sim[i, j])
        k = rng.integers(len(a), size=(3000, 2))
        k = k[k[:, 0] != k[:, 1]]
        pairs["random"] += list(sim[k[:, 0], k[:, 1]])
    pair_summary = {k: {"n": len(v), "mean_specific_cosine": float(np.mean(v)) if v else None,
                        "q25_q50_q75": np.quantile(v, [.25, .5, .75]).tolist() if v else None} for k, v in pairs.items()}
    result = {"label": "EXPOSED Block Q tier; exploratory",
              "active_cells": len(df),
              "means": {k: float(df[k].mean()) for k in ("regime_B", "regime_A1", "oracle_donor_cosine", "oracle_donor_specific",
                                                          "top5_oracle_mean_cosine", "nearest_structure_cosine",
                                                          "nearest_structure_tanimoto", "oracle_donor_tanimoto")},
              "fraction_nearest_tanimoto_ge_0_5": float((df.nearest_structure_tanimoto >= .5).mean()),
              "by_nearest_tanimoto": [{"bin": str(r.tanimoto_bin), "n": int(r.n), "regime_B": float(r.regime_B),
                                       "regime_A1": float(r.regime_A1), "oracle_donor": float(r.oracle_donor)} for r in by_bin.itertuples()],
              "specific_direction_pairs": pair_summary,
              "gamma": float(atlas.gamma)}
    write_json("rkt_ceiling.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "by_nearest_tanimoto"}, indent=1))
    return result


# ---------------------------------------------------------------- question 5: learning curve
def _score(atlas, cert, inp, rows_by_line: dict, regime: str) -> list[float]:
    out = []
    for T, rows in rows_by_line.items():
        vis = np.zeros((len(rows), len(inp.lines)), bool) if regime == "B" else one_visible(inp, rows, T)
        p = kt.predict(atlas, cert, rows, T, vis)
        out += list(kt.centred_cosine(p.direction, atlas.Yc[rows, T].astype(np.float64)))
    return out


def curve() -> dict:
    inp, cert = world()
    act = active_mask(inp)
    lib_order = sorted(range(len(inp.library)), key=lambda j: h(f"curve-query:{inp.keys[inp.library[j]]}"))[:240]
    rows_by_line = {T: inp.library[[j for j in lib_order if act[j, T]]] for T in range(len(inp.lines))}
    refs = np.flatnonzero(inp.ref)
    result = {"label": "EXPOSED Block Q tier; exploratory", "queries": len(lib_order),
              "active_cells": int(sum(len(v) for v in rows_by_line.values())), "points": []}
    t0 = time.time()
    for frac in (1 / 8, 1 / 4, 1 / 2, 1.0):
        for rep in range(3 if frac < 1 else 1):
            order = sorted(refs, key=lambda r: h(f"curve:{rep}:{inp.keys[r]}"))
            keep = np.array(order[:int(round(frac * len(refs)))])
            ref = np.zeros(len(inp.keys), bool)
            ref[keep] = True
            atlas = kt.TransferAtlas.build(inp.Y, ref, inp.fps, inp.know, inp.thr)
            b, a1 = _score(atlas, cert, inp, rows_by_line, "B"), _score(atlas, cert, inp, rows_by_line, "A1")
            result["points"].append({"fraction": frac, "rep": rep, "n_refs": int(ref.sum()), "regime_B": float(np.mean(b)),
                                     "regime_A1": float(np.mean(a1)), "gamma": float(atlas.gamma), "maps": len(atlas.maps)})
            print(json.dumps(result["points"][-1]), f"{time.time() - t0:.0f}s", flush=True)
    x = np.log2([p["n_refs"] for p in result["points"]])
    for key in ("regime_B", "regime_A1"):
        yv = np.array([p[key] for p in result["points"]])
        slope, icpt = np.polyfit(x, yv, 1)
        n_full = len(refs)
        result[f"{key}_slope_per_doubling"] = float(slope)
        result[f"{key}_predicted_gain_one_campaign_64_compounds"] = float(slope * np.log2((n_full + 64) / n_full))
    write_json("rkt_learning_curve.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "points"}, indent=1))
    return result


# ---------------------------------------------------------------- question 5: sequential memory
def memory() -> dict:
    """Eleven Block Q campaigns in order; measured cells of earlier campaigns become references."""
    inp, cert = world()
    base = kt.TransferAtlas.build(inp.Y, inp.ref, inp.fps, inp.know, inp.thr)
    kappa = kt.transfer_table(base)
    truth = base.Yc.copy()
    act = active_mask(inp)
    lib_pos = {r: j for j, r in enumerate(inp.library)}
    order = sorted(range(len(inp.library)), key=lambda j: Q.h(f"confirm-lib:{inp.keys[inp.library[j]]}"))
    n_sub = max(1, len(order) // Q.SUBLIB)
    camps = [np.array(order[s::n_sub]) for s in range(n_sub)]
    hidden = base.Yc.copy()
    hidden[inp.library] = np.nan
    arms = ("no_memory", "memory", "shuffled", "pseudo_label")
    atlases = {}
    for arm in arms:
        a = copy.copy(base)
        a.Yc, a.ref = hidden.copy(), base.ref.copy()
        atlases[arm] = a
    rng = np.random.default_rng(h("memory-shuffle") % 2 ** 32)
    rows = []
    t0 = time.time()
    for s, sel in enumerate(camps):
        lib, grid = inp.library[sel], inp.grid[sel]
        W = len(lib)
        chosen = sparse_transfer_design(grid, kappa, W, seed=h(f"memory-design:{s}") % 2 ** 32)
        cells = np.argwhere(chosen)
        for arm in arms:
            atlas = atlases[arm]
            # Zero-shot (regime B) on this campaign's active cells, before any of its measurements.
            zs = []
            for T in range(len(inp.lines)):
                rr = lib[act[sel, T]]
                if len(rr):
                    p = kt.predict(atlas, cert, rr, T, np.zeros((len(rr), len(inp.lines)), bool))
                    zs += list(kt.centred_cosine(p.direction, truth[rr, T].astype(np.float64)))
            # Profile the design: write measured cells for this campaign's own fills.
            atlas.Yc[lib[cells[:, 0]], cells[:, 1]] = truth[lib[cells[:, 0]], cells[:, 1]]
            util, fills = [], {}
            for T in range(len(inp.lines)):
                open_rows = np.flatnonzero(grid[:, T] & ~chosen[:, T])
                if len(open_rows):
                    p = kt.predict(atlas, cert, lib[open_rows], T, chosen[open_rows])
                    for k, j in enumerate(open_rows):
                        fills[(j, T)] = p.direction[k]
                for j in np.flatnonzero(act[sel, T]):
                    util.append(1.0 if chosen[j, T] else float(kt.centred_cosine(fills[(j, T)], truth[lib[j], T].astype(np.float64))))
            rows.append({"campaign": s, "arm": arm, "zero_shot_active_cosine": float(np.mean(zs)) if zs else None,
                         "zero_shot_cells": len(zs), "map_utility": float(np.mean(util)) if util else None,
                         "refs": int(atlas.ref.sum())})
            # Admission for later campaigns.
            if arm == "no_memory":
                atlas.Yc[lib] = np.nan
            elif arm == "memory":
                atlas.ref[lib] = True
            elif arm == "shuffled":
                for T in range(len(inp.lines)):
                    m = cells[cells[:, 1] == T]
                    if len(m) > 1:
                        perm = rng.permutation(len(m))
                        atlas.Yc[lib[m[:, 0]], T] = truth[lib[m[perm, 0]], T]
                atlas.ref[lib] = True
            elif arm == "pseudo_label":
                for (j, T), d in fills.items():
                    measured = atlas.Yc[lib[j], chosen[j]]
                    scale_ = float(np.linalg.norm(measured, axis=-1).mean()) if len(measured) else 0.0
                    atlas.Yc[lib[j], T] = (d * scale_).astype(atlas.Yc.dtype)
                atlas.ref[lib] = True
        print(f"campaign {s} {time.time() - t0:.0f}s", {r['arm']: round(r['zero_shot_active_cosine'], 4) for r in rows[-4:]}, flush=True)
    from tools.evaluation.scoring import cluster_signflip_test
    later = [r for r in rows if r["campaign"] >= 1]
    by = {(r["campaign"], r["arm"]): r for r in later}
    contrasts = {}
    for arm in ("memory", "shuffled", "pseudo_label"):
        for key in ("zero_shot_active_cosine", "map_utility"):
            d = [by[(c, arm)][key] - by[(c, "no_memory")][key] for c in range(1, n_sub)]
            contrasts[f"{arm}_minus_no_memory_{key}"] = {"mean": float(np.mean(d)), "per_campaign": d,
                                                         "signflip": cluster_signflip_test(d, [str(c) for c in range(1, n_sub)])}
    result = {"label": "EXPOSED Block Q tier; exploratory", "campaigns": n_sub, "rows": rows, "contrasts": contrasts}
    write_json("rkt_memory.json", result)
    print(json.dumps({k: {"mean": v["mean"], "p_two_sided": v["signflip"]["p_two_sided"]} for k, v in contrasts.items()}, indent=1))
    return result


def main() -> None:
    commands = {"ceiling": ceiling, "curve": curve, "memory": memory}
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=tuple(commands))
    commands[parser.parse_args().command]()


if __name__ == "__main__":
    main()
