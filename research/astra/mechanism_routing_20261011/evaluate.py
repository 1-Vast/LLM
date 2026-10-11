"""Block N evaluator: run once on the sealed confirmation drugs, or rehearse on development drugs.

All settings come from ``PROTOCOL_CONFIG.json``.

* ``tier="sealed"``: the reference pool is the reference + development drugs and the queries are
  the confirmation drugs. Requires FREEZE.json (``tiers.load``).
* ``tier="dev"``: the reference pool is the reference drugs and the queries are the development
  drugs. This is a rehearsal: no sealed value is read.

Sections, all paired by drug, with a mechanism-class cluster bootstrap:

* ``killers`` (drugs killing >= 5% of lines):
  * selective r of A, L, T, C, E (known and novel class);
  * the own partial screen: test-line r of L against mining on 40 or 160 discovery lines;
  * the flash agent arms (novel class) and the explainer (40 lines);
  * L, T and C scored against the independent secondary screen.
* ``trust`` (all queries, novel class): selective-prediction value of trust rankings (``trust.py``).

Verdicts use a family-wise interval: Bonferroni within each family of registered contrasts, a
percentile cluster bootstrap with ``n_boot`` draws.
* PASS: the lower bound is above 0.
* HARM: the upper bound is below 0.
* NOT_SUPPORTED: otherwise.

Writes RESULTS.json, ROWS_killers.csv and ROWS_trust.csv to ``out_dir``.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mining as MI  # noqa: E402
import predictors as PR  # noqa: E402
import trust as TR  # noqa: E402

AGENT_OUT = HERE / "agent_outputs"


def protocol() -> dict:
    return json.loads((HERE / "PROTOCOL_CONFIG.json").read_text(encoding="utf-8"))


def slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def record(*parts) -> dict | None:
    p = AGENT_OUT.joinpath(*parts)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def fin(v) -> float:
    """A missing or undefined prediction scores 0 (no information), as in development."""
    return 0.0 if (v is None or not np.isfinite(v)) else float(v)


def groups_of(clusters):
    keys, inv = np.unique(np.asarray(clusters), return_inverse=True)
    return [np.where(inv == k)[0] for k in range(len(keys))]


def boot_mean(d, clusters, n_boot, seed, levels):
    """Mean of ``d`` with cluster-bootstrap percentile intervals at each two-sided level."""
    d = np.asarray(d, float)
    groups = groups_of(clusters)
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        draws[b] = d[np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])].mean()
    out = {"n": int(len(d)), "estimate": float(d.mean()), "share_positive": float(np.mean(d > 0)),
           "share_negative": float(np.mean(d < 0))}
    for name, lv in levels.items():
        a = (1 - lv) / 2
        out[name] = [float(np.quantile(draws, a)), float(np.quantile(draws, 1 - a))]
    return out


def boot_metric(df, fn, n_boot, seed, levels):
    """Cluster bootstrap of a whole-sample statistic ``fn(sub_df)`` (trust contrasts)."""
    groups = groups_of(df["moa"].to_numpy())
    rng = np.random.default_rng(seed)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        draws[b] = fn(df.iloc[np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])])
    out = {"n": int(len(df)), "estimate": float(fn(df))}
    for name, lv in levels.items():
        a = (1 - lv) / 2
        out[name] = [float(np.quantile(draws, a)), float(np.quantile(draws, 1 - a))]
    return out


# ------------------------------------------------------------------------------------------- world
def setup(tier: str, poison_seed: int | None):
    world = PR.load_world("sealed" if tier == "sealed" else "open")
    role = "confirmation" if tier == "sealed" else "development"
    queries = [int(i) for i in np.where(world.role == role)[0]]
    if poison_seed is not None:  # negative control: permute each query's profiles across lines
        rng = np.random.default_rng(poison_seed)
        for i in queries:
            world.P[i] = world.P[i][rng.permutation(world.P.shape[1])]
            world.S2[i] = world.S2[i][rng.permutation(world.S2.shape[1])]
    return world, queries


def killers_of(world, queries, P):
    lfc, share = P["killer"]["lfc"], P["killer"]["share"]
    return [i for i in queries if np.nanmean(world.P[i] < lfc) >= share]


def run_llm(world, queries, killers, fe, P):
    """Frozen flash prompts. Trust arms run for every query, the others only for killers."""
    import explain as EX
    import scientist as SC
    L = P["llm"]
    agent = SC.Agent(world, workers=L["workers"], profile=L["profile"])
    tasks = [(arm, L["regime"], i) for arm in L["all_query_arms"] for i in queries]
    tasks += [(arm, L["regime"], i) for arm in L["killer_arms"] for i in killers]
    agent.run(tasks)
    ex = EX.Explainer(world, agent.ledger, agent.client, workers=L["workers"], profile=L["profile"])
    size = L["explain_size"]
    ex.run([("explain_full", i, f"n{size}", fe.discovery(size), PR.residual(world.P[i], world.G)) for i in killers])
    return round(agent.ledger.total_usd, 4)


# ------------------------------------------------------------------------------------------- rows
def killer_row(world, fe, i, P, with_llm):
    row = {"drug": str(world.drug[i]), "moa": str(world.moa[i])}
    reg = P["llm"]["regime"]
    b = {}
    for regime in ("known_class", "novel_class"):
        b[regime] = world.baselines(i, regime)
        for k in ("A", "L", "T", "C", "E"):
            if k in b[regime]:
                row[f"{regime}:{k}"] = fin(PR.selective_r(b[regime][k], world.P[i], world.G))
    bk = b["known_class"]
    row["known_class:A+L"] = fin(PR.selective_r(PR.combine([bk["A"], bk["L"]]), world.P[i], world.G))
    bn = b[reg]
    if with_llm:
        name = slug(str(world.drug[i]))
        routes = {}
        for arm in ("route_lit", "route_nolit"):
            rec = record(arm, reg, f"{name}.json")
            routes[arm] = world.compile_routes(rec["claims"]["routes"], i, reg) if rec and rec["status"] == "ok" else None
            row[f"agent:{arm}"] = fin(PR.selective_r(routes[arm], world.P[i], world.G))
        row["agent:L+route_lit"] = fin(PR.selective_r(PR.combine([bn["L"], routes["route_lit"]]), world.P[i], world.G))
        rec = record("adjudicate_lit", reg, f"{name}.json")
        adj = None
        if rec and rec["status"] == "ok":
            offered = world.neighbours(i, reg)
            parts = [p for p in (world.compile_neighbours(rec["claims"]["keep_neighbours"], i, reg, offered),
                                 world.compile_routes(rec["claims"]["routes"], i, reg)) if p is not None]
            adj = np.mean(parts, axis=0) if parts else None
        row["agent:adjudicate_lit"] = fin(PR.selective_r(adj, world.P[i], world.G))
    # own partial screen (test lines never shown to anyone)
    y = PR.residual(world.P[i], world.G)
    t = fe.test[np.isfinite(y[fe.test])]
    Lk = b["known_class"]["L"]
    Lr = PR.residual(Lk, world.G)[t] if Lk is not None else None
    row["own:L_test"] = fin(PR.pearson(Lr, y[t], 30)) if Lr is not None else 0.0
    Ln = PR.residual(bn["L"], world.G)[t] if bn["L"] is not None else None  # unseen-class transfer
    row["own:Lnovel_test"] = fin(PR.pearson(Ln, y[t], 30)) if Ln is not None else 0.0
    for size in P["own_screen"]["sizes"]:
        d = fe.discovery(size)
        d = d[np.isfinite(y[d])]
        ridge = fe.ridge_predict(y[d], d, t)
        row[f"own:top5@{size}"] = fin(PR.pearson(fe.predict_top(np.arange(len(fe.names)), y[d], d, t, 5), y[t], 30))
        row[f"own:ridge@{size}"] = fin(PR.pearson(ridge, y[t], 30))
        row[f"own:L+ridge@{size}"] = fin(PR.pearson(PR.combine([Lr, ridge]), y[t], 30))
        row[f"own:Lnovel+ridge@{size}"] = fin(PR.pearson(PR.combine([Ln, ridge]), y[t], 30))
        if with_llm and size == P["llm"]["explain_size"]:
            rec = record("explain_full", f"n{size}", f"{slug(str(world.drug[i]))}.json")
            ok = rec is not None and rec["status"] == "ok"
            cols, signs = fe.columns(rec["claims"]["features"]) if ok else (np.array([], int), np.array([]))
            ep = fe.predict_claims(cols, signs, d, t)
            row[f"agent:explain@{size}"] = fin(PR.pearson(ep, y[t], 30)) if ep is not None else 0.0
            row[f"agent:L+explain@{size}"] = fin(PR.pearson(PR.combine([Lr, ep]), y[t], 30))
            row[f"agent:Lnovel+explain@{size}"] = fin(PR.pearson(PR.combine([Ln, ep]), y[t], 30))
    # independent secondary screen of the same drug (different plates and run)
    if np.isfinite(world.S2[i]).sum() >= P["secondary_min_lines"]:
        for k in ("L", "T", "C"):
            row[f"secondary:{k}"] = fin(PR.selective_r(bn[k], world.S2[i], world.G))
        row["secondary:ceiling"] = fin(PR.selective_r(world.P[i], world.S2[i], world.G))
    return row


def trust_rows(world, queries, P, with_llm):
    reg = P["llm"]["regime"]
    rows = []
    for i in queries:
        b = world.baselines(i, reg)
        name = slug(str(world.drug[i]))
        adj = record("adjudicate_lit", reg, f"{name}.json") if with_llm else None
        rte = record("route_lit", reg, f"{name}.json") if with_llm else None
        rows.append({"drug": str(world.drug[i]), "moa": str(world.moa[i]),
                     "utility": fin(PR.selective_r(b["L"], world.P[i], world.G)),
                     **TR.scores_for(world, i, reg, adj, rte)})
    return TR.composite(pd.DataFrame(rows))


# ------------------------------------------------------------------------------------------- main
def main(tier: str = "sealed", out_dir: Path | None = None, poison_seed: int | None = None, with_llm: bool = True) -> dict:
    t0 = time.time()
    P = protocol()
    nb, seed = P["n_boot"], P["seed"]
    out_dir = Path(out_dir) if out_dir else HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    world, queries = setup(tier, poison_seed)
    killers = killers_of(world, queries, P)
    fe = MI.Features(world)
    res = {"tier": tier, "poison_seed": poison_seed, "with_llm": with_llm,
           "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL_CONFIG.json").read_bytes()).hexdigest(),
           "n_reference": int(len(world.ref)), "n_queries": len(queries), "n_killers": len(killers)}
    if with_llm:
        if poison_seed is not None:
            raise ValueError("outcome poisoning runs without the agent (the explainer would see poisoned lines)")
        res["ledger_total_usd"] = run_llm(world, queries, killers, fe, P)

    kdf = pd.DataFrame([killer_row(world, fe, i, P, with_llm) for i in killers])
    kdf.to_csv(out_dir / "ROWS_killers.csv", index=False)
    tdf = trust_rows(world, queries, P, with_llm)
    tdf.to_csv(out_dir / "ROWS_trust.csv", index=False)

    lv95 = {"ci95": 0.95}
    res["means"] = {}
    for c in kdf.columns:
        if c in ("drug", "moa"):
            continue
        sub = kdf[kdf[c].notna()]
        res["means"][c] = boot_mean(sub[c].to_numpy(float), sub["moa"].to_numpy(), nb, seed, lv95)
    res["trust_metrics"] = {"mean_utility": float(tdf["utility"].mean()),
                            "oracle": TR.evaluate(tdf["utility"], tdf["utility"]),
                            **{c: TR.evaluate(TR.rank01(tdf[c]), tdf["utility"])
                               for c in ("top_sim", "mean5_sim", "moa_agree5", "l1000_norm", "vc", "keep", "kill",
                                         "kill_prior", "agent", "vc+agent")}}
    res["contrasts"] = contrasts(kdf, tdf, P, with_llm)
    res["decisions"] = decide(res["contrasts"], P)
    res["seconds"] = round(time.time() - t0, 1)
    (out_dir / "RESULTS.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def family_levels(P, fam):
    k = sum(1 for c in P["contrasts"] if c["family"] == fam)
    return {"ci95": 0.95, "ci_family": 1 - P["alpha"] / k}


def contrasts(kdf, tdf, P, with_llm=True):
    nb, seed = P["n_boot"], P["seed"]
    out = {}
    for c in P["contrasts"]:
        lv = family_levels(P, c["family"])
        if c["family"] == "agent" and not with_llm:
            out[c["id"]] = None
        elif c["kind"] == "paired":
            if c["a"] not in kdf or c["b"] not in kdf:
                out[c["id"]] = None
                continue
            sub = kdf[kdf[c["a"]].notna() & kdf[c["b"]].notna()]
            d = sub[c["a"]].to_numpy(float) - sub[c["b"]].to_numpy(float)
            out[c["id"]] = boot_mean(d, sub["moa"].to_numpy(), nb, seed, lv)
        elif c["kind"] == "trust_vs_mean":  # utility of the most-trusted share minus the mean utility
            out[c["id"]] = boot_metric(tdf, lambda s, a=c["a"], m=c["metric"]: TR.evaluate(TR.rank01(s[a]), s["utility"])[m]
                                       - float(s["utility"].mean()), nb, seed, lv)
        elif c["kind"] == "trust_paired":
            out[c["id"]] = boot_metric(tdf, lambda s, a=c["a"], b=c["b"], m=c["metric"]:
                                       TR.evaluate(TR.rank01(s[a]), s["utility"])[m]
                                       - TR.evaluate(TR.rank01(s[b]), s["utility"])[m], nb, seed, lv)
    return out


def decide(cons, P):
    out = {}
    for c in P["contrasts"]:
        r = cons.get(c["id"])
        if r is None:
            out[c["id"]] = {"name": c["name"], "family": c["family"], "verdict": "NOT_RUN", "predicted": c["predicted"]}
            continue
        lo, hi = r["ci_family"]
        v = "PASS" if lo > 0 else ("HARM" if hi < 0 else "NOT_SUPPORTED")
        out[c["id"]] = {"name": c["name"], "family": c["family"], "estimate": r["estimate"], "ci_family": [lo, hi],
                        "verdict": v, "predicted": c["predicted"], "prediction_held": v == c["predicted"]}
    h = P["headline"]
    out["headline"] = {
        "vc_value_confirmed": all(out[k]["verdict"] == "PASS" for k in h["vc_primary"]),
        "agent_value_shown": any(out[k]["verdict"] == "PASS" for k in h["agent_any"]),
        "agent_harm": [k for k in h["agent_any"] if out[k]["verdict"] == "HARM"],
    }
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="sealed", choices=["sealed", "dev"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--poison", type=int, default=None)
    a = ap.parse_args()
    r = main(a.tier, Path(a.out) if a.out else None, a.poison, not a.no_llm)
    print(json.dumps(r["decisions"], indent=1))
