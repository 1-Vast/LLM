"""Stages: synthetic | headroom | freeze | real.

  python svc_run.py synthetic      software/method controls (no real outcomes)
  python svc_run.py headroom       real data, H0 development cells only -> DEV_HEADROOM.json (source-side headroom and useful-gain criterion)
  python svc_run.py freeze         writes FREEZE.json (config + code hashes); refuses once real results exist
  python svc_run.py real           one bounded development pilot on the exported O'Neil environment (+ anchor-only control)
  (post-freeze stages api | programs | summary live in svc_post.py so the frozen code set is not edited after scoring)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import svc_evolution as E  # noqa: E402
import svc_programs as P  # noqa: E402
import svc_study as S  # noqa: E402
import svc_summarize as SM  # noqa: E402
import svc_world as W  # noqa: E402

SEEDS = (0, 1, 2)
BUDGETS = (8, 16)
CONTRASTS_ = ("E", "T")
COMPUTE_LIMIT_S = 120 * 60
CODE_FILES = ("svc_world.py", "svc_programs.py", "svc_evolution.py", "svc_study.py", "svc_summarize.py", "svc_run.py", "svc_llm.py", "svc_integrity.py")


def write_json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, default=float) + "\n", encoding="utf-8")


def read_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha_lf(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def config():
    return {"seeds": list(SEEDS), "budgets": list(BUDGETS), "contracts": list(CONTRASTS_), "shortlist_k": W.SHORTLIST_K, "generations": 3, "candidates_per_generation": 12,
            "delta_acc": S.DELTA_ACC, "acceptance": "paired mean dev gain >= delta_acc and wins on >= 60% of released cells",
            "promotion": "provisional -> demonstrated if paired gain >= 0 and wins >= half on the next batch of released cells not used to select it, else retired and parent restored",
            "splits_real": dict(zip(["H0", "D1", "D2", "D3", "A", "T"], E.BUILTIN_SPLITS["real"])),
            "splits_synthetic": dict(zip(["H0", "D1", "D2", "D3", "A", "T"], E.BUILTIN_SPLITS["synthetic"])),
            "compute_limit_minutes": COMPUTE_LIMIT_S // 60, "query_unit": "one pair-by-cell dose grid (logical unit; not wells, cultures or money)",
            "grammar_version": P.GRAMMAR_VERSION, "grammar_limits": P.LIMITS,
            "label_rule": "SUPPORTED_DEV if mean paired (evo_full - refit) >= delta_use and wins >= 60% of cells and the anchor-only control gain < 0.5 of it; NOT_SUPPORTED if mean < 0.5*delta_use; else INCONCLUSIVE"}


# ----------------------------------------------------------------------------- stages
def stage_synthetic():
    t0 = time.perf_counter()
    results = []
    for kind in ("null_anchor", "low_rank", "compositional"):
        for seed in SEEDS:
            w = W.make_synthetic(kind, seed)
            for contract in CONTRASTS_:
                for B in BUDGETS:
                    r = S.run_condition(w, "synthetic", B, contract, seed)
                    r["world_group"] = kind
                    results.append(r)
                    print(kind, seed, contract, B, round(r["compute_seconds"], 1), "s", flush=True)
    write_json("SYNTHETIC_RESULTS.json", {"compute_seconds": time.perf_counter() - t0, "results": results})
    return results


def real_world():
    return W.load_export()


def stage_headroom():
    w = real_world()
    static = w.static
    cells = E.split_cells(w.cells, "real")
    H0 = cells["H0"]
    memo = E.Memo(w)
    fc = {}
    arms = {k: v for k, v in E.baseline_arms().items()}
    arms["random_probe"] = S.arm_spec_arm({**P.base_spec(), "Q": [{"kind": "probe", "frac": 0.5, "rule": "random", "cond": None}, {"kind": "confirm", "frac": 0.5}]}, "random_probe")
    out = {"dev_cells": H0, "note": "nested leave-one-cell-out inside the nine H0 development cells; no later cell is used", "rows": []}
    for contract in CONTRASTS_:
        for B in BUDGETS:
            res = {}
            oracle = None
            for name, arm in arms.items():
                if contract == "T" and name == "direct":
                    continue
                u = []
                for seed in SEEDS:
                    rr = E.evaluate({**arm, "name": name}, w, memo, static, H0, H0, B, seed, contract, nested=True, fitted_cache=fc)
                    u.append([r["utility"] for r in rr])
                    if oracle is None or seed == SEEDS[-1]:
                        oracle_seed = np.mean([r["oracle"] for r in rr])
                res[name] = float(np.mean(u))
                oracle = float(np.mean([r["oracle"] for r in rr]))
            best_name = max((k for k in res if k != "zero"), key=lambda k: res[k])
            out["rows"].append({"contract": contract, "budget": B, "oracle": oracle, "utility": res, "best_baseline": best_name, "best_baseline_utility": res[best_name],
                                "headroom_after_best_baseline": oracle - res[best_name], "headroom_after_zero_probe": oracle - res["zero"]})
            print(contract, B, "oracle %.4f best %s %.4f headroom %.4f" % (oracle, best_name, res[best_name], oracle - res[best_name]), flush=True)
    viable = [r for r in out["rows"] if r["headroom_after_best_baseline"] >= 0.005]
    out["decision_opportunity_rows"] = [(r["contract"], r["budget"]) for r in viable]
    prim = max(out["rows"], key=lambda r: r["headroom_after_best_baseline"])
    out["primary"] = {"contract": prim["contract"], "budget": prim["budget"], "headroom": prim["headroom_after_best_baseline"]}
    out["delta_use"] = 0.25 * prim["headroom_after_best_baseline"]
    out["delta_use_rule"] = "25% of the H0-only headroom (oracle minus the best baseline) at the primary condition; 0.005 is not reused"
    out["effectiveness_claims_allowed"] = bool(viable)
    write_json("DEV_HEADROOM.json", out)
    return out


def stage_freeze():
    if (HERE / "REAL_RESULTS.json").exists():
        raise SystemExit("REAL_RESULTS.json exists: the protocol can no longer be frozen")
    head = read_json("DEV_HEADROOM.json")
    cfg = config()
    cfg["primary"], cfg["delta_use"], cfg["effectiveness_claims_allowed"] = head["primary"], head["delta_use"], head["effectiveness_claims_allowed"]
    freeze = {"config": cfg, "dev_headroom_sha256": sha_lf(HERE / "DEV_HEADROOM.json"), "code_sha256": {f: sha_lf(HERE / f) for f in CODE_FILES if (HERE / f).exists()},
              "protocol_sha256": sha_lf(HERE / "PROTOCOL.md"), "env_export_sha256": hashlib.sha256((W.WORK / "env_export.npz").read_bytes()).hexdigest()}
    write_json("FREEZE.json", freeze)
    return freeze


def check_frozen():
    fr = read_json("FREEZE.json")
    bad = [f for f, h in fr["code_sha256"].items() if sha_lf(HERE / f) != h]
    if bad:
        raise SystemExit(f"code changed after freeze: {bad}")
    return fr


def stage_real():
    fr = check_frozen()
    cfg = fr["config"]
    w = real_world()
    control = w.anchor_only(seed=0)
    prim = (cfg["primary"]["contract"], cfg["primary"]["budget"])
    order = [prim] + [(c, b) for c in CONTRASTS_ for b in BUDGETS if (c, b) != prim]
    results, skipped = [], []
    t0 = time.perf_counter()
    for contract, B in order:
        for label, world in (("oneil", w), ("oneil_anchor_only", control)):
            for seed in SEEDS:
                if time.perf_counter() - t0 > COMPUTE_LIMIT_S:
                    skipped.append((label, contract, B, seed))
                    continue
                r = S.run_condition(world, "real", B, contract, seed)
                r["world_group"] = label
                results.append(r)
                print(label, contract, B, seed, round(r["compute_seconds"], 1), "s", flush=True)
    write_json("REAL_RESULTS.json", {"compute_seconds": time.perf_counter() - t0, "skipped_conditions": skipped, "results": results})
    return results


if __name__ == "__main__":
    stage = sys.argv[1]
    {"synthetic": stage_synthetic, "headroom": stage_headroom, "freeze": stage_freeze, "real": stage_real}[stage]()
