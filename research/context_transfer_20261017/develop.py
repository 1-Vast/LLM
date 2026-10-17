"""Development replays on PRISM 19Q4 (exposed; development grade only).

File summary
- Path: research/context_transfer_20261017/develop.py
- Purpose: run one named development configuration of the equal-well replay over all 568 lines
  and save per-context records, so the design choices frozen in PROTOCOL.md are traceable.
- Core points:
  - Configurations vary the bridge size, the Virtual Cell rank, the repair threshold and the
    split regime (line holdout by hashed key; lineage holdout by hashed primary tissue).
  - Every configuration and its outcome is disclosed in DEVELOPMENT.json; none is confirmation.
- Interfaces: `python -B develop.py NAME` (see CONFIGS); `python -B develop.py --summary`.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import data_prism
import replay
from common import CACHE, HERE, folds, paired, tie_order, write_json

CONFIGS = {
    "main_w32_b8_r20": dict(budget=32, k_bridge=8, rank=20, repair_threshold=2.0, regime="line"),
    "w32_b4_r20": dict(budget=32, k_bridge=4, rank=20, repair_threshold=2.0, regime="line"),
    "w32_b16_r20": dict(budget=32, k_bridge=16, rank=20, repair_threshold=2.0, regime="line"),
    "w32_b8_r10": dict(budget=32, k_bridge=8, rank=10, repair_threshold=2.0, regime="line"),
    "w32_b8_r40": dict(budget=32, k_bridge=8, rank=40, repair_threshold=2.0, regime="line"),
    "lineage_w32_b8_r20": dict(budget=32, k_bridge=8, rank=20, repair_threshold=2.0, regime="lineage"),
    # second round, after the first six: expected-hit scoring, all arms and controls, repair sweep.
    # (A first launch of the two "final_*_r40" runs used a lookahead whose baseline still counted
    # items already in the bridge batch; both were stopped before writing and are not reported.)
    "v1_line_w32_b8_r40": dict(budget=32, k_bridge=8, rank=40, repair_threshold=2.0, regime="line",
                               repair_grid=True, impute_iters=0),
    "v1_lineage_w32_b8_r40": dict(budget=32, k_bridge=8, rank=40, repair_threshold=2.0,
                                  regime="lineage", repair_grid=True, impute_iters=0),
    "v2_line_w32_b8_r40": dict(budget=32, k_bridge=8, rank=40, repair_threshold=2.0, regime="line",
                               repair_grid=True, impute_iters=15),
    "v2_lineage_w32_b8_r40": dict(budget=32, k_bridge=8, rank=40, repair_threshold=2.0,
                                  regime="lineage", repair_grid=True, impute_iters=15),
    # source-verified selector (procedure.py, final variant): rank on vc0, then the procedure;
    # inner targets capped at 40 per inner fold for compute
    "menu_v2_line_w32_b8": dict(budget=32, k_bridge=8, regime="line", impute_iters=15, menu=True),
    "menu_v2_lineage_w32_b8": dict(budget=32, k_bridge=8, regime="lineage", impute_iters=15, menu=True),
}
GRID = (1.0, 2.0, 4.0, float("inf"))
OUT = CACHE / "dev"


def runtime() -> dict:
    import platform
    import scipy
    return {"python": sys.executable, "version": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__}


def run_config(name: str, fold=None) -> None:
    import json
    cfg = CONFIGS[name]
    d = data_prism.load()
    if cfg["regime"] == "line":
        fid = folds(d["contexts"], "context-transfer")
    else:
        fid = folds(d["groups"], "context-transfer-lineage")
    t = time.time()
    if cfg.get("menu"):
        import procedure
        part = OUT / f"{name}.parts"
        if fold is not None:
            menu = procedure.menu_records(d, fid, cfg["budget"], cfg["k_bridge"], data_prism.ABS_GATE,
                                          data_prism.MIN_MEASURED, cfg["impute_iters"],
                                          by_group=cfg["regime"] != "line", max_inner_targets=40,
                                          only_folds={fold})
            write_json(part / f"fold{fold}.json", {"seconds": time.time() - t, "runtime": runtime(), "menu": menu})
            print(name, "fold", fold, "done", round(time.time() - t), "s")
            return
        menu = {}
        for k in range(5):
            menu.update(json.loads((part / f"fold{k}.json").read_text(encoding="utf-8"))["menu"])
        recs, choices = {}, {}
        for rule in ("evidence", "max"):
            auto, choices[rule] = procedure.apply(menu, rule)
            for c, v in auto.items():
                recs.setdefault(c, {"context": c}).update(
                    {f"{k}_{rule}": x for k, x in v.items()})
        write_json(OUT / f"{name}.json", {"config": cfg, "seconds": time.time() - t, "runtime": runtime(),
                                          "choices": choices, "menu": menu, "records": list(recs.values())})
        print(name, "done", round(time.time() - t), "s")
        return
    recs = replay.run(d, cfg["budget"], cfg["k_bridge"], rank=cfg["rank"],
                      repair_threshold=cfg["repair_threshold"], abs_gate=data_prism.ABS_GATE,
                      min_measured=data_prism.MIN_MEASURED, fold_ids=fid,
                      repair_grid=GRID if cfg.get("repair_grid") else (),
                      impute_iters=cfg.get("impute_iters", 0))
    write_json(OUT / f"{name}.json", {"config": cfg, "seconds": time.time() - t, "runtime": runtime(),
                                      "records": recs})
    print(name, "done", round(time.time() - t), "s")


META = {"fold", "events", "misfit", "bridge_measured", "bma_weight_transfer", "auto_rank_evidence",
        "auto_rounds_evidence", "auto_rank_max", "auto_rounds_max", "auto_rank_hybrid", "auto_rounds_hybrid"}
CONTRASTS = [("vc0", "item"), ("vc0", "knn"), ("b_lookahead", "vc0"), ("b_lookahead", "b_exploit"),
             ("b_lookahead", "b_info"), ("b_lookahead", "b_panel"), ("b_lookahead", "b_random"),
             ("b_info", "b_panel"), ("maestro", "b_lookahead"), ("b_exploit", "vc0"),
             ("maestro", "vc0"), ("maestro", "b_exploit"), ("maestro", "match_panel"),
             ("match_panel", "vc0"), ("vc0", "vc0_xshuffle"), ("maestro", "maestro_yshuffle"),
             ("maestro_bma", "b_lookahead"), ("maestro@1", "maestro@inf"), ("maestro@2", "maestro@inf"),
             ("maestro@4", "maestro@inf"), ("auto_evidence", "vc0"), ("auto_evidence", "b_exploit"),
             ("auto_evidence", "b_lookahead"), ("auto_evidence", "knn"), ("auto_evidence", "match_panel"),
             ("auto_evidence", "sel_vc0_evidence"), ("auto_evidence", "sel_b_exploit_evidence"),
             ("auto_evidence", "sel_b_lookahead_evidence"), ("sel_vc0_evidence", "knn"),
             ("auto_max", "auto_evidence"), ("auto_max", "sel_vc0_max"),
             # the frozen rule (RULE_CHOICE.md), recomputed from the stored menus
             ("auto_hybrid", "sel_vc0_hybrid"), ("auto_hybrid", "sel_b_exploit_hybrid"),
             ("auto_hybrid", "sel_b_lookahead_hybrid"), ("auto_hybrid", "knn"), ("auto_hybrid", "match_panel"),
             ("auto_hybrid", "b_lookahead"), ("auto_hybrid", "vc0"), ("auto_hybrid", "auto_evidence"),
             ("auto_max", "auto_hybrid"), ("sel_vc0_hybrid", "knn")]


def summary() -> dict:
    import json
    out = {}
    for name in CONFIGS:
        path = OUT / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        recs = data["records"]
        if data["config"].get("menu"):
            base_path = OUT / f"v2_{data['config']['regime']}_w32_b8_r40.json"
            if not base_path.exists():
                continue
            base = {r["context"]: r for r in json.loads(base_path.read_text(encoding="utf-8"))["records"]}
            recs = [{**base[r["context"]], **r} for r in recs]
            import procedure
            recs = procedure.with_rule(recs, data["menu"], "hybrid")
        groups = [r["group"] for r in recs]
        s = {"config": data["config"], "contexts": len(recs),
             "mean_hits": {a: float(np.mean([r[a] for r in recs])) for a, v in recs[0].items()
                           if isinstance(v, (int, float)) and not isinstance(v, bool) and a not in META},
             "contrasts": {}}
        for a, b in CONTRASTS:
            if a in recs[0] and b in recs[0]:
                diff = np.array([r[a] - r[b] for r in recs], float)
                s["contrasts"][f"{a}-{b}"] = paired(diff, groups)
        if "repaired" in recs[0]:
            s["repaired_fraction"] = float(np.mean([r["repaired"] for r in recs]))
        if "choices" in data and data["choices"]:
            s["choices"] = {rule: {k: {"rank": v["rank"], "procedure": v["procedure"],
                                       "bridge_gains": v["bridge_gains"]} for k, v in ch.items()}
                            for rule, ch in data["choices"].items()}
        out[name] = s
    write_json(HERE / "DEVELOPMENT.json", out)
    return out


def rank_check() -> dict:
    """Does the inner-CV rank rule (vc.select_rank, source contexts only) track decision quality?"""

    from vc import select_rank
    import power
    out = {}
    for label, d, k_probe, gate, mm in (("prism", data_prism.load(), 8, data_prism.ABS_GATE, data_prism.MIN_MEASURED),
                                        ("aml_proxy", power.proxy(), 4, None, 100)):
        fid = folds(d["contexts"], "context-transfer")
        rows = {}
        for k in range(5):
            src = np.flatnonzero(fid != k)
            r, sc = select_rank(d["Y"][src].astype(float), d["X"][src].astype(float), (5, 10, 20, 40, 80),
                                k_probe, abs_gate=gate, min_measured=mm)
            rows[k] = {"rank": r, "inner_log_density": sc}
            print(label, k, r, {a: round(b, 4) for a, b in sc.items()}, flush=True)
        out[label] = rows
    write_json(HERE / "RANK_CHECK.json", out)
    return out


def llm_pilot(n_lines: int = 30) -> dict:
    """Engineering pilot of the secondary LLM arm on PRISM development lines (about 0.02 USD).

    Checks that the provider returns valid exact-k selections and measures tokens per call; its
    hits are reported but decide nothing, because 30 lines cannot.
    """

    from llm_arm import LLMBridge
    d = data_prism.load()
    fid = folds(d["contexts"], "context-transfer")
    keys = d["contexts"]
    pick = np.argsort([h for h in tie_order(keys, "llm-pilot")])[:n_lines]
    filt = np.zeros(len(keys), bool)
    filt[pick] = True
    llm = LLMBridge(CACHE / "llm_pilot_ledger.jsonl")

    def text(c):
        return {"system": "cancer cell line screened with a compound library (PRISM, log2 fold change "
                          "in viability at 2.5 uM; lower is a stronger effect)",
                "lineage": str(d["groups"][c])}

    recs = replay.run(d, 32, 8, arms=("vc0", "b_lookahead", "maestro", "llm"), rank=40,
                      repair_threshold=2.0, abs_gate=data_prism.ABS_GATE,
                      min_measured=data_prism.MIN_MEASURED, fold_ids=fid, context_filter=filt,
                      llm=llm, context_text=text, item_names=d["item_names"])
    out = {"lines": len(recs), "spend": llm.spend(),
           "refusals": {k: int(sum(r.get("llm_refusal") == k for r in recs))
                        for k in {r.get("llm_refusal") for r in recs} if k},
           "mean_hits": {a: float(np.mean([r[a] for r in recs])) for a in ("vc0", "b_lookahead", "maestro", "llm")}}
    write_json(HERE / "LLM_PILOT.json", out)
    print(out)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--llm-pilot":
        llm_pilot()
    elif sys.argv[1] == "--rank-check":
        rank_check()
    elif sys.argv[1] == "--summary":
        for k, v in summary().items():
            print(k, {a: round(x, 3) for a, x in v["mean_hits"].items() if not a.endswith(("_wasted", "_bridge_hits"))})
            for c, st in v["contrasts"].items():
                print("   ", c, round(st["mean"], 3), [round(x, 3) for x in st["ci95"]], st["p_one_sided"])
    else:
        run_config(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--fold" else None)
