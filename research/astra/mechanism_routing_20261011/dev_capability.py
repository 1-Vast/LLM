"""Development capability ablation (exploratory): is the agent null because of the task or the model?

Same 69 development killers, same prompts and scoring as ``dev_pilot.py`` (routing and adjudication,
novel-class regime) and ``dev_explain.py`` (post-observation biomarker hypotheses at 40 discovery
lines). Profiles (``models.py``): ``flash`` (earlier runs, thinking off), ``flash_think`` and ``pro``.

Usage: python dev_capability.py <profile>[,<profile>] [max_drugs]
Output: development/capability.json and development/capability_rows.csv (all profiles found).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import explain as EX  # noqa: E402
import mining as MI  # noqa: E402
import predictors as PR  # noqa: E402
import scientist as SC  # noqa: E402

sys.path.insert(0, str(PR.BLOCK_M))
import intervals as IV  # noqa: E402

SEED = 20261011
REGIME = "novel_class"
SIZE = 40
PROFILES = ("flash", "flash_think", "pro")


def run(profiles, max_drugs=None):
    world = PR.load_world("open")
    fe = MI.Features(world)
    dev = [i for i in np.where(world.role == "development")[0] if np.nanmean(world.P[i] < -1) >= 0.05][:max_drugs]
    Y = {i: PR.residual(world.P[i], world.G) for i in dev}
    for f in (HERE / "agent_outputs").glob("*@*/*/*.json"):  # keep failed records, retry them once
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec.get("status") == "failed" and not f.name.endswith(".failed.json"):
            f.replace(f.with_name(f.stem + ".failed.json"))
    for prof in profiles:
        ag = SC.Agent(world, workers=16, profile=prof)
        ag.run([(arm, REGIME, int(i)) for arm in ("route_lit", "adjudicate_lit") for i in dev])
        ex = EX.Explainer(world, ag.ledger, ag.client, workers=16, profile=prof)
        ex.run([("explain_full", int(i), f"n{SIZE}", fe.discovery(SIZE), Y[i]) for i in dev])
    return world, fe, dev, Y


def _load(max_drugs=None):
    world = PR.load_world("open")
    fe = MI.Features(world)
    dev = [i for i in np.where(world.role == "development")[0] if np.nanmean(world.P[i] < -1) >= 0.05][:max_drugs]
    return world, fe, dev, {i: PR.residual(world.P[i], world.G) for i in dev}


def score(world, fe, dev, Y):
    rows = []
    d_all = fe.discovery(SIZE)
    for i in dev:
        y = Y[i]
        b = world.baselines(i, REGIME)
        d = d_all[np.isfinite(y[d_all])]
        t = fe.test[np.isfinite(y[fe.test])]
        row = {"drug": world.drug[i], "moa": world.moa[i]}
        for k in ("L", "T", "C", "E"):
            row[k] = PR.selective_r(b[k], world.P[i], world.G) if b[k] is not None else 0.0
        Lk = world.baselines(i, "known_class")["L"]
        Lr = PR.residual(Lk, world.G) if Lk is not None else None
        row["mine_top5"] = PR.pearson(fe.predict_top(np.arange(len(fe.names)), y[d], d, t, 5), y[t], 30)
        row["mine_ridge"] = PR.pearson(fe.ridge_predict(y[d], d, t), y[t], 30)
        row["L_test"] = PR.pearson(Lr[t], y[t], 30) if Lr is not None else 0.0
        for prof in PROFILES:
            tag = "" if prof == "flash" else f"@{prof}"
            pr = HERE / "agent_outputs" / f"route_lit{tag}" / REGIME / f"{SC.slug(str(world.drug[i]))}.json"
            pa = HERE / "agent_outputs" / f"adjudicate_lit{tag}" / REGIME / f"{SC.slug(str(world.drug[i]))}.json"
            pe = HERE / "agent_outputs" / f"explain_full{tag}" / f"n{SIZE}" / f"{SC.slug(str(world.drug[i]))}.json"
            vals = {}
            if pr.exists():
                rr = json.loads(pr.read_text(encoding="utf-8"))
                if rr["status"] == "ok":
                    routes = world.compile_routes(rr["claims"]["routes"], i, REGIME)
                    vals["route"] = PR.selective_r(routes, world.P[i], world.G) if routes is not None else 0.0
                    vals["L+route"] = PR.selective_r(PR.combine([b["L"], routes]), world.P[i], world.G)
                    row[f"{prof}:n_routes"] = len(rr["claims"]["routes"])
            if pa.exists():
                ra = json.loads(pa.read_text(encoding="utf-8"))
                if ra["status"] == "ok":
                    offered = world.neighbours(i, REGIME)
                    nb = world.compile_neighbours(ra["claims"]["keep_neighbours"], i, REGIME, offered)
                    rt = world.compile_routes(ra["claims"]["routes"], i, REGIME)
                    parts = [p_ for p_ in (nb, rt) if p_ is not None]
                    adj = np.mean(parts, axis=0) if parts else None
                    vals["adjudicate"] = PR.selective_r(adj, world.P[i], world.G) if adj is not None else 0.0
                    row[f"{prof}:n_keep"] = len(ra["claims"]["keep_neighbours"])
            if pe.exists():
                re_ = json.loads(pe.read_text(encoding="utf-8"))
                if re_["status"] == "ok":
                    cols, signs = fe.columns(re_["claims"]["features"])
                    ex_pred = fe.predict_claims(cols, signs, d, t)
                    vals["explain"] = PR.pearson(ex_pred, y[t], 30) if ex_pred is not None else 0.0
                    vals["explain_mine3"] = PR.pearson(fe.predict_top(cols, y[d], d, t, 3), y[t], 30) if len(cols) else 0.0
                    vals["L_test+explain"] = PR.pearson(PR.combine([Lr[t] if Lr is not None else None, ex_pred]), y[t], 30)
                    row[f"{prof}:n_features"] = len(re_["claims"]["features"])
            for k, v in vals.items():
                row[f"{prof}:{k}"] = v if (v is not None and np.isfinite(v)) else 0.0
            row[f"{prof}:completion_tokens"] = sum(int((json.loads(q.read_text(encoding="utf-8")).get("usage") or {}).get("completion_tokens", 0) or 0)
                                                   for q in (pr, pa, pe) if q.exists())
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(df):
    cl = df["moa"].to_numpy()
    res = {"n": int(len(df)), "mean": {}, "paired": {}}
    for col in df.columns:
        if col in ("drug", "moa") or col.split(":")[-1].startswith("n_") or col.endswith("tokens"):
            continue
        v = df[col].to_numpy(float)
        ok = np.isfinite(v)
        if ok.sum() >= 5:
            est, lo, hi = IV.cluster_bootstrap(v[ok], cl[ok], n_boot=1000, seed=SEED)
            res["mean"][col] = [round(est, 4), round(lo, 4), round(hi, 4), int(ok.sum())]
    for prof in PROFILES:
        if f"{prof}:route" not in df:
            continue
        for a, b in (("route", "T"), ("route", "L"), ("adjudicate", "L"), ("L+route", "L"), ("explain", "mine_top5"),
                     ("explain", "mine_ridge"), ("L_test+explain", "L_test")):
            if f"{prof}:{a}" not in df:
                continue
            x, y = df[f"{prof}:{a}"].to_numpy(float), df[b].to_numpy(float)
            ok = np.isfinite(x) & np.isfinite(y)
            if ok.sum() < 5:
                continue
            r = IV.paired_difference(x[ok], y[ok], cl[ok], n_boot=1000, seed=SEED)
            res["paired"][f"{prof}:{a} - {b}"] = [round(r["mean_difference"], 4), round(r["ci95"][0], 4), round(r["ci95"][1], 4), r["n"]]
        if prof != "flash" and "flash:route" in df:
            for a in ("route", "adjudicate", "explain"):
                if f"{prof}:{a}" not in df:
                    continue
                x, y = df[f"{prof}:{a}"].to_numpy(float), df[f"flash:{a}"].to_numpy(float)
                ok = np.isfinite(x) & np.isfinite(y)
                if ok.sum() < 5:
                    continue
                r = IV.paired_difference(x[ok], y[ok], cl[ok], n_boot=1000, seed=SEED)
                res["paired"][f"{prof}:{a} - flash:{a}"] = [round(r["mean_difference"], 4), round(r["ci95"][0], 4), round(r["ci95"][1], 4), r["n"]]
        res[f"{prof}:mean_completion_tokens_per_drug"] = round(float(df[f"{prof}:completion_tokens"].mean()), 1)
    return res


if __name__ == "__main__":
    profs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["flash_think", "pro"]
    mx = int(sys.argv[2]) if len(sys.argv) > 2 else None
    world, fe, dev, Y = run(profs, mx) if profs != ["score"] else _load(mx)
    df = score(world, fe, dev, Y)
    res = summarise(df)
    import scientist as _S
    res["ledger_total_usd"] = round(_S.Agent.__init__ and json.loads((PR.ROOT / "tmp/mechanism_routing_spend.json").read_text())["total_usd"], 4)
    (HERE / "development").mkdir(exist_ok=True)
    (HERE / "development" / "capability.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(HERE / "development" / "capability_rows.csv", index=False)
    print(json.dumps(res, indent=1))
