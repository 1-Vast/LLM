"""Exposed-data feasibility replay with physically masked RKT query outcomes."""
from __future__ import annotations

import hashlib
import itertools
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
Q = ROOT / "research/knowledge_transfer_20261012"
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(Q)]
from virtual_cell import knowledge_transfer as kt


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def interval(x, seed=1310, draws=10000, alpha=.05):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(len(x), size=(draws, len(x)))].mean(1)
    return {"mean": float(x.mean()), "ci": np.quantile(means, [alpha/2, 1-alpha/2]).tolist(), "n": len(x)}


def diagnosis():
    rows = pd.read_parquet(Q / "results/prediction_rows.parquet")
    out = {}
    for name, g in rows.groupby("regime"):
        y, p = g.active.to_numpy(), g.p_active.to_numpy()
        out[name] = dict(n=len(g), prevalence=float(y.mean()), predicted=float(p.mean()),
                         brier=float(brier_score_loss(y, p)), auc=float(roc_auc_score(y, p)),
                         average_precision=float(average_precision_score(y, p)),
                         cosine_active=float(g.loc[y, "pooled"].mean()),
                         cosine_all=float(g.pooled.mean()),
                         cosine_inactive=float(g.loc[~y, "pooled"].mean()),
                         refusal=float((g.refusal != "").mean()))
        # Prospective direction declaration requires both predicted activity and accuracy.
        accept = (p >= .5) & (g.expected.to_numpy() >= .5)
        valid = y & (g.pooled.to_numpy() >= .5)
        out[name]["declaration_p05_cos05"] = dict(
            count=int(accept.sum()), valid=int((valid & accept).sum()),
            precision=float(valid[accept].mean()) if accept.any() else None,
            recall=float((valid & accept).sum() / max(1, valid.sum())))
    campaigns = pd.read_json(Q / "results/campaign_rows.json")
    pivot = campaigns[campaigns.budget == 1].pivot(index="campaign", columns="arm", values="utility")
    fill = campaigns[campaigns.budget == 1].groupby("arm")[["utility", "utility_vcfill", "utility_naivefill", "rounds"]].mean()
    interaction = (pivot.maestro_llm - pivot.llm_no_vc) - (pivot.sparse_hub -
        campaigns[(campaigns.budget == 1) & (campaigns.arm == "sparse_hub")].set_index("campaign").utility_naivefill)
    write("diagnosis.json", {"prediction": out, "campaign_fill": fill.to_dict("index"),
          "historical_interaction_exploratory": interval(interaction),
          "warning": "Historical arms differ in policy; this interaction is descriptive, not factorial identification."})


def score_choices(ratio, first, second):
    i = np.arange(len(first))
    x, y = ratio[i, first], ratio[i, second]
    return (x > 1) != (y > 1), ((x > 1.2) & (y < .8)) | ((y > 1.2) & (x < .8))


def prepare():
    import confirm
    t0 = time.perf_counter()
    query_path = ROOT / "data/external/lincs_l1000_phase2/derived/blockq_phase2_query_SEALED.npz"
    z = np.load(query_path)
    inp = confirm.phase2_inputs(z["cp"], z["compound"])
    n, L = inp.grid.shape
    truth = inp.Y[inp.library].copy()
    ratio = np.linalg.norm(truth, axis=2) / inp.thr
    refs = inp.Y[inp.ref]
    rr = np.linalg.norm(refs, axis=2) / inp.thr
    active_ref = rr > 1
    Y = inp.Y.copy()
    Y[~inp.ref] = np.nan  # No unacquired query outcomes in the model process state.
    atlas = kt.TransferAtlas.build(Y, inp.ref, inp.fps, inp.know, inp.thr)
    kap = kt.transfer_table(atlas)
    hubs = np.argsort(-kap.mean(1), kind="stable")
    first = np.array([next(t for t in hubs if grid[t]) for grid in inp.grid])
    second_hub = np.array([next(t for t in hubs if grid[t] and t != s) for grid, s in zip(inp.grid, first)])
    pair_scores = {}
    for s, t in itertools.combinations(range(L), 2):
        have = np.isfinite(rr[:, s]) & np.isfinite(rr[:, t])
        pair_scores[s, t] = (float((active_ref[have, s] != active_ref[have, t]).mean()))
    pair_order = sorted(pair_scores, key=lambda p: (-pair_scores[p], p))
    fixed = np.array([next(pair for pair in pair_order if grid[list(pair)].all()) for grid in inp.grid])
    visible = np.zeros((n, L), bool)
    visible[np.arange(n), first] = True
    atlas.Yc[inp.library, first] = truth[np.arange(n), first] - atlas.mu[first]
    with (Q / "cache/pooler_all.pkl").open("rb") as f:
        old = pickle.load(f)
    certifier = kt.Certifier(old.act_model, old.route_models, old.pool_model, old.rho_min)
    p_rkt = np.full((n, L), np.nan)
    ec = np.full((n, L), np.nan)
    cos = np.full((n, L), np.nan)
    refuse = np.zeros((n, L), bool)
    p_emp = np.full((n, L), np.nan)
    p_knn = np.full((n, L), np.nan)
    for t in range(L):
        ids = np.flatnonzero(inp.grid[:, t] & ~visible[:, t])
        if not len(ids):
            continue
        pred = kt.predict(atlas, certifier, inp.library[ids], t, visible[ids])
        p_rkt[ids, t] = pred.certificate.p_active
        ec[ids, t] = pred.certificate.expected_cosine
        cos[ids, t] = kt.centred_cosine(pred.direction, truth[ids, t] - atlas.mu[t])
        refuse[ids, t] = pred.certificate.refusal != ""
        for i in ids:
            s = first[i]
            have = np.isfinite(rr[:, s]) & np.isfinite(rr[:, t])
            cond = have & (active_ref[:, s] == (ratio[i, s] > 1))
            p_emp[i, t] = (1 + active_ref[cond, t].sum()) / (2 + cond.sum())
            neighbours = np.flatnonzero(have)[np.argsort(np.abs(rr[have, s] - ratio[i, s]), kind="stable")[:20]]
            p_knn[i, t] = (1 + active_ref[neighbours, t].sum()) / (2 + len(neighbours))
    seen_active = ratio[np.arange(n), first] > 1
    def select(prob):
        opposite = np.where(seen_active[:, None], 1-prob, prob)
        return np.nanargmax(opposite, axis=1)
    choices = {"sparse_hub": (first, second_hub), "fixed_pair": (fixed[:, 0], fixed[:, 1]),
               "empirical": (first, select(p_emp)), "empirical_knn": (first, select(p_knn)),
               "rkt": (first, select(p_rkt))}
    # A feedback-shuffled control uses predictions from another compound with the same first line.
    shuffled = p_rkt.copy()
    for s in np.unique(first):
        ids = np.flatnonzero(first == s)
        shuffled[ids] = p_rkt[np.roll(ids, 1)]
    shuffled[~inp.grid | visible] = np.nan
    # Missing donor entries are filled with the reference conditional estimate, never truth.
    shuffled = np.where(np.isnan(shuffled) & inp.grid & ~visible, p_emp, shuffled)
    choices["rkt_feedback_shuffled"] = (first, select(shuffled))
    summaries, records = {}, []
    keys = [inp.keys[i] for i in inp.library]
    for arm, (one, two) in choices.items():
        hit, robust = score_choices(ratio, one, two)
        summaries[arm] = {"discordance": interval(hit), "margin_discordance": interval(robust),
                          "hits": int(hit.sum()), "margin_hits": int(robust.sum()),
                          "replay_slots": 2*n, "simulated_rounds": 1 if arm in ("sparse_hub", "fixed_pair") else 2}
        records.extend(dict(key=keys[i], arm=arm, first=int(one[i]), second=int(two[i]),
                            hit=int(hit[i]), margin_hit=int(robust[i])) for i in range(n))
    eligible = inp.grid
    mixed = ((ratio > 1) & eligible).any(1) & ((ratio <= 1) & eligible).any(1)
    robust = ((ratio > 1.2) & eligible).any(1) & ((ratio < .8) & eligible).any(1)
    best_fixed = max(summaries[a]["discordance"]["mean"] for a in ("sparse_hub", "fixed_pair"))
    gate = mixed.mean()-best_fixed >= .05 and robust.mean() >= .10
    valid = inp.grid & ~visible
    y = ratio[valid] > 1
    prediction = {name: {"brier": float(brier_score_loss(y, prob[valid])),
                        "auc": float(roc_auc_score(y, prob[valid]))}
                  for name, prob in (("rkt", p_rkt), ("empirical", p_emp), ("empirical_knn", p_knn))}
    act = valid & (ratio > 1)
    prediction["rkt"].update(cosine_active=float(cos[act].mean()),
                              expected_active=float(ec[act].mean()), refusal=float(refuse[valid].mean()))
    metadata = []
    for i, q in enumerate(inp.library):
        rec = inp.records[q]
        metadata.append({"key": keys[i], "name": rec.name, "targets": list(rec.signed_targets()),
                         "moa": sorted(rec.hub_moa)})
    pilot = sorted(range(n), key=lambda i: hashlib.sha256(("context-pilot:"+keys[i]).encode()).hexdigest())[:84]
    write("metadata.json", {"compounds": metadata, "lines": inp.lines, "pilot": pilot,
          "hubs": hubs.tolist(), "reference_pair_scores": {f"{s},{t}": v for (s,t),v in pair_scores.items()}})
    np.savez_compressed(HERE / "replay.npz", ratio=ratio, grid=inp.grid, first=first, p_rkt=p_rkt,
                        p_emp=p_emp, p_knn=p_knn, expected=ec, refusal=refuse, truth=truth,
                        genes=np.array(inp.genes), thresholds=inp.thr)
    write("policy_rows.json", records)
    write("RESULTS.json", {"status": "EXPLORATORY", "n": n, "policies": summaries,
          "prediction": prediction, "oracle": {"mixed": int(mixed.sum()), "margin_mixed": int(robust.sum()),
          "headroom_over_best_fixed": float(mixed.mean()-best_fixed)}, "pilot_gate_passed": bool(gate),
          "runtime_seconds": time.perf_counter()-t0, "promotion": "NONE", "independent_confirmation": "NOT_AVAILABLE"})
    write("input_audit.json", {"base_commit": "ac99532a21ff23bd2221784ddf87debe196b195d",
          "sources": {str(p.relative_to(ROOT)).replace('\\','/'): digest(p) for p in (
          query_path, confirm.P2, Q/'cache/pooler_all.pkl', Q/'FREEZE.json', Q/'results/prediction_rows.parquet',
          ROOT/'src/virtual_cell/knowledge_transfer.py')}, "notes": inp.notes,
          "query_outcomes_exposure": "All previously exposed in Block Q", "fresh_confirmation": False})
    print(json.dumps({"policies": summaries, "prediction": prediction, "gate": bool(gate)}))


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        diagnosis()
        prepare()
