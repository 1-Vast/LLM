"""Phase 1 gate (PLAN_P1.md): reproducibility and conditional structure of substitution contrasts. Writes REPRO.json (write-once)."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cas_data as D

HERE = Path(__file__).resolve().parent
OUT = HERE / "REPRO.json"
N_BOOT = 2000
RNG = np.random.default_rng(20261019)


def halves(df):
    plates = pd.read_csv(HERE / "cache/plates.csv")
    df = df.merge(plates[["BARCODE", "DATE_CREATED"]], on="BARCODE", how="left")
    assert df.DATE_CREATED.notna().all()
    h = {}
    for line, g in df.groupby("CELL_LINE_NAME"):
        for i, d in enumerate(sorted(g.DATE_CREATED.unique())):
            h[(line, d)] = 1 + (i % 2)
    df["half"] = [h[(l, d)] for l, d in zip(df.CELL_LINE_NAME, df.DATE_CREATED)]
    return df


def families(drugs):
    ids = sorted(drugs)
    ts = {i: D.target_set(drugs[i]["target"]) for i in ids}
    cls = {}
    for a, b in itertools.combinations(ids, 2):
        if ts[a] & ts[b]:
            cls[(a, b)] = "target"
        elif drugs[a]["pathway"] == drugs[b]["pathway"]:
            cls[(a, b)] = "pathway"
        else:
            cls[(a, b)] = "unrelated"
    return cls


def unit_table(df, cls, endpoint):
    """Half-specific means per (side, drug, partner, conc, line), then Delta per unit and half."""
    rows = []
    lib = df.groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID", "half"])[[endpoint, "LIBRARY_AUC"]].mean()
    anc = df.groupby(["CELL_LINE_NAME", "LIBRARY_ID", "ANCHOR_ID", "ANCHOR_CONC", "half"])[[endpoint]].mean()
    lib_d = lib.to_dict("index")
    anc_d = anc.to_dict("index")
    lib_keys = lib.reset_index().groupby(["CELL_LINE_NAME", "ANCHOR_ID", "ANCHOR_CONC"]).LIBRARY_ID.agg(set).to_dict()
    anc_keys = anc.reset_index().groupby(["CELL_LINE_NAME", "LIBRARY_ID", "ANCHOR_CONC"]).ANCHOR_ID.agg(set).to_dict()
    for (line, B, conc), S in lib_keys.items():
        for a, b in itertools.combinations(sorted(S), 2):
            k = cls.get((a, b))
            if k is None:
                continue
            v = {}
            for h in (1, 2):
                x, y = lib_d.get((line, B, conc, a, h)), lib_d.get((line, B, conc, b, h))
                if x is None or y is None:
                    break
                v[h] = (y[endpoint] - x[endpoint], y["LIBRARY_AUC"] - x["LIBRARY_AUC"])
            if len(v) == 2:
                rows.append(("library", a, b, f"{B}@{conc}", line, k, v[1][0], v[2][0], v[1][1], v[2][1]))
    # anchor side: anchors at their own concentrations; pair anchors by concentration rank (low/high) within each anchor
    anc_r = anc.reset_index()
    rank = {}
    for aid, g in anc_r.groupby("ANCHOR_ID"):
        cs = sorted(g.ANCHOR_CONC.unique(), key=lambda s: float(str(s).split("|")[0]))
        for i, c in enumerate(cs):
            rank[(aid, c)] = i
    by = {}
    for (line, L, aid, conc, h), r in anc_d.items():
        by[(line, L, aid, rank[(aid, conc)], h)] = r[endpoint]
    keys = {}
    for (line, L, aid, rk, h) in by:
        keys.setdefault((line, L, rk), set()).add(aid)
    for (line, L, rk), S in keys.items():
        for a, b in itertools.combinations(sorted(S), 2):
            k = cls.get((a, b))
            if k is None:
                continue
            v = {}
            for h in (1, 2):
                x, y = by.get((line, L, a, rk, h)), by.get((line, L, b, rk, h))
                if x is None or y is None:
                    break
                v[h] = y - x
            if len(v) == 2:
                rows.append(("anchor", a, b, f"{L}#r{rk}", line, k, v[1], v[2], np.nan, np.nan))
    t = pd.DataFrame(rows, columns=["side", "A", "A2", "partner", "line", "cls", "d1", "d2", "s1", "s2"])
    return t.dropna(subset=["d1", "d2"])


def stats(t):
    d1, d2 = t.d1.to_numpy(), t.d2.to_numpy()
    c = np.cov(d1, d2)[0, 1]
    return dict(n=int(len(t)), r=float(np.corrcoef(d1, d2)[0, 1]), repro_sd=float(np.sqrt(max(c, 0))),
                noise_sd=float(np.sqrt(np.var(d1 - d2) / 2)), mean_abs=float(np.mean(np.abs((d1 + d2) / 2))))


def additive_resid(t, col):
    """Per drug pair and side: Delta = a(partner) + b(line) by alternating means; residuals for one half."""
    res = pd.Series(np.nan, index=t.index)
    for _, g in t.groupby(["side", "A", "A2"]):
        if g.partner.nunique() < 2 or g.line.nunique() < 2:
            continue
        y = g[col].to_numpy()
        pi = pd.factorize(g.partner)[0]
        li = pd.factorize(g.line)[0]
        a = np.zeros(pi.max() + 1)
        b = np.zeros(li.max() + 1)
        for _ in range(50):
            a = np.bincount(pi, y - b[li]) / np.bincount(pi)
            b = np.bincount(li, y - a[pi]) / np.bincount(li)
        res.loc[g.index] = y - a[pi] - b[li]
    return res


def cond_stats(t):
    r1, r2 = additive_resid(t, "d1"), additive_resid(t, "d2")
    ok = r1.notna() & r2.notna()
    if ok.sum() < 10:
        return dict(n=int(ok.sum()))
    c_res = np.cov(r1[ok], r2[ok])[0, 1]
    c_all = np.cov(t.d1[ok], t.d2[ok])[0, 1]
    return dict(n=int(ok.sum()), r_resid=float(np.corrcoef(r1[ok], r2[ok])[0, 1]), share=float(c_res / c_all) if c_all > 0 else float("nan"),
                repro_sd_resid=float(np.sqrt(max(c_res, 0))))


def boot(t, fn, key, cluster):
    vals = []
    groups = {k: g for k, g in t.groupby(cluster)}
    names = list(groups)
    for _ in range(N_BOOT):
        pick = RNG.choice(len(names), len(names), replace=True)
        bt = pd.concat([groups[names[i]] for i in pick], ignore_index=True)
        try:
            vals.append(fn(bt)[key])
        except Exception:
            vals.append(np.nan)
    v = np.array(vals, float)
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


def main():
    if OUT.exists():
        raise SystemExit("REPRO.json exists (write-once)")
    df = halves(D.full("original"))
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    cls = families(census["drugs"])
    out = dict(plan="PLAN_P1.md", n_boot=N_BOOT, endpoints={})
    for ep in ("SYNERGY_DELTA_AUC", "SYNERGY_OBS_AUC"):
        t = unit_table(df, cls, ep)
        res = dict(units_by_class=t.cls.value_counts().to_dict(), units_by_side=t.side.value_counts().to_dict())
        for k in ("target", "pathway", "unrelated"):
            sub = t[t.cls == k]
            if len(sub) < 10:
                continue
            s = stats(sub)
            s["r_ci_line"] = boot(sub, stats, "r", "line")
            s["repro_sd_ci_line"] = boot(sub, stats, "repro_sd", "line")
            res[k] = s
        tgt = t[t.cls == "target"].reset_index(drop=True)
        cs = cond_stats(tgt)
        if "r_resid" in cs:
            cs["r_resid_ci_line"] = boot(tgt, cond_stats, "r_resid", "line")
            tgt["pair"] = tgt.A + "|" + tgt.A2
            cs["r_resid_ci_pair"] = boot(tgt, cond_stats, "r_resid", "pair")
            cs["share_ci_line"] = boot(tgt, cond_stats, "share", "line")
            res["target"]["r_ci_pair"] = boot(tgt, stats, "r", "pair")
        res["target_conditional"] = cs
        lib = tgt[tgt.side == "library"].dropna(subset=["s1", "s2"])
        if len(lib) > 10:
            def r2(x, y):
                return float(1 - np.var(y - np.polyval(np.polyfit(x, y, 1), x)) / np.var(y))
            res["single_agent_baseline_library_side"] = dict(n=int(len(lib)), r2_from_single_agent_half1=r2(lib.s1, lib.d2),
                                                             r2_from_delta_half1=r2(lib.d1, lib.d2),
                                                             r2_from_both=float(1 - np.var(lib.d2 - np.c_[lib.d1, lib.s1, np.ones(len(lib))] @ np.linalg.lstsq(np.c_[lib.d1, lib.s1, np.ones(len(lib))], lib.d2, rcond=None)[0]) / np.var(lib.d2)))
        # per-pair reproducible magnitude (target class)
        per = []
        for (side, a, b), g in tgt.groupby(["side", "A", "A2"]):
            if len(g) >= 20:
                s = stats(g)
                per.append(dict(side=side, A=census["drugs"][a]["name"], A2=census["drugs"][b]["name"], **s))
        res["target_pairs"] = sorted(per, key=lambda x: -x["n"])
        out["endpoints"][ep] = res
    s = out["endpoints"]["SYNERGY_DELTA_AUC"]
    n = s["target"]["n"]
    lo_r = min(s["target"]["r_ci_line"][0], s["target"].get("r_ci_pair", [1, 1])[0])
    hi_r = max(s["target"]["r_ci_line"][1], s["target"].get("r_ci_pair", [0, 0])[1])
    cs = s["target_conditional"]
    lo_res = min(cs.get("r_resid_ci_line", [np.nan])[0], cs.get("r_resid_ci_pair", [np.nan])[0])
    if n < 300:
        dec = "BLOCKED"
    elif hi_r < 0.20:
        dec = "REJECTED"
    elif lo_r > 0 and lo_res > 0 and cs.get("share", 0) >= 0.25:
        dec = "QUALIFIED"
    elif lo_r > 0:
        dec = "CONDITIONALLY_QUALIFIED"
    else:
        dec = "REJECTED"
    out["decision"] = dict(label=dec, n_target_units=n, reliability_ci_wider=[lo_r, hi_r], conditional_r_lower=lo_res,
                           conditional_share=cs.get("share"))
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8", newline="\n")
    print(json.dumps(out["decision"], indent=1))
    for ep, r in out["endpoints"].items():
        print("==", ep, r["units_by_class"], r["units_by_side"])
        for k in ("target", "pathway", "unrelated"):
            if k in r:
                print(" ", k, {x: (round(v, 4) if isinstance(v, float) else v) for x, v in r[k].items()})
        print("  conditional", r["target_conditional"])
        print("  single-agent", r.get("single_agent_baseline_library_side"))


if __name__ == "__main__":
    main()
