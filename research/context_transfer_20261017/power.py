"""Design and power check on a PRISM proxy shaped like the confirmation domain.

File summary
- Path: research/context_transfer_20261017/power.py
- Purpose: choose the Beat AML well budget and bridge size, and estimate the power of P1-P4,
  without touching any Beat AML outcome. The proxy is development data (PRISM 19Q4, exposed).
- Core points:
  - 166 PRISM items are drawn by hash among items measured in at least 300 lines, the size of the
    Beat AML inhibitor panel.
  - Each item gets a measurement rate shaped like the Beat AML census: three quarters of items
    measured in 60-97% of contexts, a quarter in 0.4-19%. Pairs are masked by hash.
  - The endpoint is recomputed on the masked proxy with no absolute gate and at least 100
    measured contexts, as registered for Beat AML.
  - Each configuration runs the equal-well replay. The report gives mean hits, paired contrasts,
    and the power of each primary contrast at 479 independent patient clusters (normal
    approximation, one-sided Holm-worst-case alpha 0.025/4).
- Interfaces: `python -B power.py NAME` (see CONFIGS); `python -B power.py --summary`.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
from scipy.stats import norm

import data_prism
import replay
from common import CACHE, HERE, folds, h, paired, selective_events, tie_order, write_json

N_ITEMS = 166
CONFIGS = {
    # round 1 (lookahead baseline bug present: these bridge arms are not interpretable; disclosed)
    "aml_w16_b4_r20": dict(budget=16, k_bridge=4, rank=20),
    "aml_w16_b2_r20": dict(budget=16, k_bridge=2, rank=20),
    "aml_w16_b8_r20": dict(budget=16, k_bridge=8, rank=20),
    "aml_w16_b4_r10": dict(budget=16, k_bridge=4, rank=10),
    "aml_w16_b4_r5": dict(budget=16, k_bridge=4, rank=5),
    # round 2: fixed lookahead; v1 = mean imputation, v2 = EM-SVD imputation; `auto` adds the
    # source-verified procedure selector (procedure.py)
    "v1_w16_b4_r10": dict(budget=16, k_bridge=4, rank=10, impute_iters=0),
    "v2_w16_b4_r10": dict(budget=16, k_bridge=4, rank=10, impute_iters=15),
    "v2_w16_b4_r5": dict(budget=16, k_bridge=4, rank=5, impute_iters=15),
    "v2_w16_b4_r20": dict(budget=16, k_bridge=4, rank=20, impute_iters=15),
    "v2_auto_w16_b4": dict(budget=16, k_bridge=4, rank=10, impute_iters=15, auto=True),
    "v1_auto_w16_b4": dict(budget=16, k_bridge=4, rank=10, impute_iters=0, auto=True),
    # structured targeted-panel proxy (whole inhibitor families)
    "s_v2_w16_b4_r10": dict(budget=16, k_bridge=4, rank=10, impute_iters=15, proxy="structured"),
    "s_v2_w16_b4_r20": dict(budget=16, k_bridge=4, rank=20, impute_iters=15, proxy="structured"),
    "s_v2_w16_b4_r5": dict(budget=16, k_bridge=4, rank=5, impute_iters=15, proxy="structured"),
    "s_v2_auto_w16_b4": dict(budget=16, k_bridge=4, rank=10, impute_iters=15, auto=True, proxy="structured"),
    # the three `*_auto_*` runs above used selector variant A (joint rank x procedure over a menu
    # with repaired lookahead); the final selector picks the rank on vc0, then the procedure
    # (two "autoF" runs of a no-margin final selector were stopped unfinished; the menu runs below
    # reproduce that rule as "max")
    "v2_menu_w16_b4": dict(budget=16, k_bridge=4, rank=10, impute_iters=15, menu=True),
    "s_v2_menu_w16_b4": dict(budget=16, k_bridge=4, rank=10, impute_iters=15, menu=True, proxy="structured"),
}
OUT = CACHE / "power"
GRID = (1.0, 2.0, 4.0, float("inf"))


def structured_items(d, elig) -> np.ndarray:
    """A targeted-panel proxy: whole inhibitor mechanism families, the most active first.

    Families are annotated mechanisms whose name contains "inhibitor" with at least 3 eligible
    members; they are ranked by mean registered events per member (development data), and up to 8
    members per family (hash order) are taken until N_ITEMS items are reached.
    """

    moa = d["item_moa"]
    fams = {}
    for i in elig:
        m = str(moa[i])
        if "inhibitor" in m and m not in ("None", "nan", ""):
            fams.setdefault(m, []).append(i)
    fams = {m: v for m, v in fams.items() if len(v) >= 3}
    rate = {m: d["events"][:, v].sum(0).mean() for m, v in fams.items()}
    chosen = []
    for m in sorted(fams, key=lambda m: (-rate[m], m)):
        v = np.array(fams[m])
        v = v[np.argsort(tie_order(d["items"][v], "aml-proxy-family"))][:8]
        chosen.extend(v[: N_ITEMS - len(chosen)].tolist())
        if len(chosen) >= N_ITEMS:
            break
    return np.sort(np.array(chosen))


def proxy(kind: str = "random") -> dict:
    d = data_prism.load()
    Y = d["Y"].astype(float)
    n_meas = np.isfinite(Y).sum(0)
    elig = np.flatnonzero(n_meas >= 300)
    if kind == "structured":
        items = structured_items(d, elig)
    else:
        order = tie_order(d["items"][elig], "aml-proxy-items")
        items = np.sort(elig[np.argsort(order)[:N_ITEMS]])
    Y = Y[:, items]
    u = tie_order(d["items"][items], "aml-proxy-rate")
    low = u < 0.25
    rate = np.where(low, 0.004 + (0.19 - 0.004) * (u / 0.25), 0.60 + 0.37 * ((u - 0.25) / 0.75))
    mask = np.array([[(h(f"{c}|{i}", "aml-proxy-mask") % 10 ** 12) / 1e12 < r
                      for i, r in zip(d["items"][items], rate)] for c in d["contexts"]])
    Y = np.where(mask, Y, np.nan)
    events, G = selective_events(Y, None, 100)
    return {"Y": Y, "X": d["X"], "events": events, "G": G, "contexts": d["contexts"],
            "groups": d["groups"], "items": d["items"][items], "item_names": d["item_names"][items]}


def run_config(name: str) -> None:
    cfg = CONFIGS[name]
    d = proxy(cfg.get("proxy", "random"))
    fid = folds(d["contexts"], "context-transfer")
    t = time.time()
    recs = replay.run(d, cfg["budget"], cfg["k_bridge"], rank=cfg["rank"], repair_threshold=2.0,
                      abs_gate=None, min_measured=100, fold_ids=fid, repair_grid=GRID,
                      impute_iters=cfg.get("impute_iters", 0))
    choices = None
    menu = None
    if cfg.get("menu"):
        import procedure
        menu = procedure.menu_records(d, fid, cfg["budget"], cfg["k_bridge"], None, 100, cfg["impute_iters"])
        choices = {}
        for rule in ("evidence", "max"):
            auto, ch = procedure.apply(menu, rule)
            choices[rule] = ch
            for r in recs:
                r.update({f"{k}_{rule}": v for k, v in auto[r["context"]].items()})
    elif cfg.get("auto"):
        import procedure_variant_a
        auto, choices = procedure_variant_a.auto_records(d, fid, cfg["budget"], cfg["k_bridge"], None, 100,
                                                         cfg.get("impute_iters", 0))
        for r in recs:
            r.update(auto[r["context"]])
    write_json(OUT / f"{name}.json", {"config": cfg, "seconds": time.time() - t,
                                      "proxy": {"items": int(len(d["items"])),
                                                "finite": int(np.isfinite(d["Y"]).sum()),
                                                "events": int(d["events"].sum()),
                                                "contexts_with_events": int((d["events"].sum(1) > 0).sum())},
                                      "choices": choices, "menu": menu, "records": recs})
    print(name, "done", round(time.time() - t), "s")


PRIMARY = [("P1", "maestro", "vc0"), ("P2", "maestro", "b_exploit"),
           ("P3", "maestro", "match_panel"), ("P4", "vc0", "knn")]
OTHER = [("b_lookahead", "vc0"), ("b_panel", "vc0"), ("b_info", "vc0"), ("b_exploit", "vc0"),
         ("vc0", "item"), ("knn", "item"), ("vc0", "vc0_xshuffle"), ("maestro", "maestro_yshuffle"),
         ("maestro@1", "maestro@inf"), ("maestro@2", "maestro@inf"), ("maestro@4", "maestro@inf"),
         ("maestro_bma", "maestro@inf"), ("auto", "vc0"), ("auto", "b_lookahead"), ("auto", "b_exploit"),
         ("auto", "knn"), ("auto", "match_panel"), ("auto", "sel_vc0"), ("auto", "sel_b_exploit"),
         ("auto", "sel_b_lookahead"), ("sel_vc0", "knn"),
         ("auto_evidence", "vc0"), ("auto_evidence", "b_exploit"), ("auto_evidence", "b_lookahead"),
         ("auto_evidence", "sel_vc0_evidence"), ("auto_evidence", "sel_b_exploit_evidence"),
         ("auto_evidence", "sel_b_lookahead_evidence"), ("auto_evidence", "match_panel"),
         ("sel_vc0_evidence", "knn"), ("auto_max", "vc0"), ("auto_max", "sel_vc0_max"),
         ("auto_max", "auto_evidence"),
         # the frozen rule (RULE_CHOICE.md), recomputed from the stored menus
         ("auto_hybrid", "sel_vc0_hybrid"), ("auto_hybrid", "sel_b_exploit_hybrid"),
         ("auto_hybrid", "sel_b_lookahead_hybrid"), ("auto_hybrid", "match_panel"), ("auto_hybrid", "knn"),
         ("auto_hybrid", "b_lookahead"), ("sel_vc0_hybrid", "knn"), ("auto_hybrid", "auto_evidence"),
         ("auto_max", "auto_hybrid")]


def power(mean, sd, n=479, alpha=0.025 / 4):
    se = sd / np.sqrt(n)
    return float(1 - norm.cdf(norm.ppf(1 - alpha) - mean / se)) if se > 0 else float(mean > 0)


def summary() -> dict:
    out = {}
    for name in CONFIGS:
        path = OUT / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        recs = data["records"]
        if data.get("menu"):
            import procedure
            recs = procedure.with_rule(recs, data["menu"], "hybrid")
        groups = [r["group"] for r in recs]
        arms = [k for k in recs[0] if isinstance(recs[0][k], (int, float)) and not isinstance(recs[0][k], bool)
                and k not in ("fold", "events", "misfit", "bridge_measured", "bma_weight_transfer",
                              "auto_rank", "auto_rounds", "auto_rank_evidence", "auto_rounds_evidence",
                              "auto_rank_max", "auto_rounds_max", "auto_rank_hybrid", "auto_rounds_hybrid")]
        s = {"config": data["config"], "proxy": data["proxy"], "contexts": len(recs),
             "mean": {a: float(np.mean([r[a] for r in recs])) for a in arms}, "contrasts": {}}
        if data.get("choices") and data.get("menu"):
            s["choices"] = {rule: {k: {"rank": v["rank"], "procedure": v["procedure"],
                                       "bridge_gains": v["bridge_gains"]} for k, v in ch.items()}
                            for rule, ch in data["choices"].items()}
        elif data.get("choices"):
            s["choices"] = {k: {"rank": v["rank"], "procedure": v["procedure"],
                                "bridge_gain_inner": v["bridge_gain_inner"]} for k, v in data["choices"].items()}
        for hid, a, b in PRIMARY + [("", a, b) for a, b in OTHER]:
            if a not in recs[0] or b not in recs[0]:
                continue
            diff = np.array([r[a] - r[b] for r in recs], float)
            st = paired(diff, groups)
            st["sd_per_context"] = float(diff.std(ddof=1))
            st["power_479_independent"] = power(diff.mean(), diff.std(ddof=1))
            st["power_at_min_useful_0.10"] = power(0.10, diff.std(ddof=1))
            s["contrasts"][(hid + " " if hid else "") + f"{a}-{b}"] = st
        out[name] = s
    write_json(HERE / "POWER.json", out)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--summary":
        for k, v in summary().items():
            print(k, v["proxy"], {a: round(x, 3) for a, x in v["mean"].items() if not a.endswith("_wasted")})
            for c, st in v["contrasts"].items():
                print("   ", c, round(st["mean"], 3), [round(x, 3) for x in st["ci95"]],
                      "sd", round(st["sd_per_context"], 2), "pow", round(st["power_479_independent"], 2),
                      "pow@.10", round(st["power_at_min_useful_0.10"], 2))
    else:
        run_config(sys.argv[1])
