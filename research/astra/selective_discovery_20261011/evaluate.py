"""Block P evaluation: run the registered arms over every campaign and compute the registered families.

Usage:
    python evaluate.py dev       # development tier (exposed block-N compounds)
    python evaluate.py confirm   # confirmation tier (requires FREEZE.json; sealed outcomes)

Writes, under ``results/<tier>/``:
* ``<library>/<lineage>/<arm>.json``: one campaign ledger per arm (screened order, pre-reveal
  predictions, refusals, verification, and for LLM arms the full call records);
* ``ROWS.csv``: one row per campaign x arm with every endpoint and cost;
* ``RESULTS.json``: totals, registered families with verdicts, calibration, refusal counts, cost.

Ledgers already on disk are reused, so an interrupted run resumes without repeating a purchase or an
LLM call.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "feasibility"))
import maestro_agent as AG  # noqa: E402
import campaign as CA  # noqa: E402
import extract as EX  # noqa: E402
import runner as RU  # noqa: E402
import stats as ST  # noqa: E402
import world as WM  # noqa: E402

BUDGET_FRAC = 0.10            # replaced from PROTOCOL_CONFIG.json when it exists
BATCH = 5
EXPLORE_SEATS = 2
DET_SOURCES = ("klass", "target", "chem")
NOVC_SOURCES = ("klass", "target", "chem", "llm")


def load_prior(U):
    from f6_llm_prior import load
    return load("prior", U.brd, U.lineages)


def strict_novel(U, ref, t):
    """Descriptive, stricter novelty (feasibility F13): shares no annotated target with a known hit for
    this lineage and is at Morgan Tanimoto below 0.4 from all of them."""
    H = U.hits()
    known = np.asarray(ref)[H[np.asarray(ref), t]]
    if not len(known):
        return np.ones(len(U.brd), bool)
    ktgt = set().union(*[U.targets[j] for j in known])
    share = np.array([bool(U.targets[i] & ktgt) for i in range(len(U.brd))])
    close = np.nan_to_num(U.sims["chem"][:, known], nan=0.0).max(1) >= 0.4
    return ~share & ~close


def config():
    p = HERE / "PROTOCOL_CONFIG.json"
    cfg = {"budget_frac": BUDGET_FRAC, "batch": BATCH, "explore_seats": EXPLORE_SEATS, "n_libraries": RU.N_LIBRARIES,
           "hit_s": WM.HIT_S, "hit_m": WM.HIT_M, "verify_s2": -0.25, "seed": 20261011}
    if p.exists():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    return cfg


def one_campaign(U, prior, arm, t, ref, pool, budget, batch, cfg, seed, conv=None):
    """Run ``arm`` on one campaign. Returns (state, extra)."""
    rng = np.random.default_rng(seed)
    perm = np.random.default_rng(900000 + seed) if arm.endswith("_perm") else None
    st = CA.State.start(U, t, ref, pool, budget, batch)
    if arm == "random":
        order = rng.permutation(pool)[:budget]
        st.predictions += [(int(c), float("nan")) for c in order]
        st.reveal(U, [int(c) for c in order])
        return st, {}
    if arm == "oracle":
        s, _ = U.selectivity(U.P[pool])
        h = U.hits()[pool, t]
        pick = pool[np.argsort(np.where(h, -10, 0) + s[:, t])[:budget]]
        st.reveal(U, [int(c) for c in pick])
        return st, {}
    if arm == "fixed":
        return CA.run_stack_arm(U, st, ("klass",), "static", rng), {}
    if arm == "vc_only":
        return CA.run_stack_arm(U, st, WM.VC_SOURCES, "static", rng), {}
    if arm == "det":
        return CA.run_stack_arm(U, st, DET_SOURCES, "refit", rng), {}
    if arm in ("conv", "conv_perm"):
        return conv.run(st, rng, permute_rng=perm, tag=arm)
    sources = NOVC_SOURCES if arm == "agent_novc" else None
    seats = cfg.get("explore_seats_secondary_arm", 2) if arm == "maestro_explore" else cfg["explore_seats"]
    ag = AG.Maestro(U, prior=prior, explore_seats=seats, stop=True, sources=sources)
    return ag.run(st, rng, permute_rng=perm)


def main(tier: str):
    t0 = time.time()
    cfg = config()
    if tier == "confirm" and not (HERE / "FREEZE.json").exists():
        raise SystemExit("TIER_SEALED: the confirmation tier opens only after FREEZE.json")
    sealed = EX.load_prism("sealed") if tier == "confirm" else None
    U = WM.build(include_new=(tier == "confirm"), sealed=sealed)
    prior = load_prior(U)
    H = U.hits()
    out_dir = HERE / "results" / tier
    arms = ["random", "fixed", "det", "vc_only", "agent_novc", "maestro", "maestro_explore", "maestro_perm",
            "conv", "conv_perm", "oracle"]
    conv = None
    rows, refusals = [], Counter()
    for name, ref, pool in RU.libraries(U, tier, cfg["seed"]):
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        RU.mask_cross(U, pool)
        budget = int(round(cfg["budget_frac"] * len(pool)))
        for t, T in enumerate(U.lineages):
            if H[pool, t].sum() == 0:
                continue
            kn = set(U.moa[ref][H[ref, t]])
            kn.discard("nan")
            unexp = H[:, t] & ~np.isin(U.moa, list(kn))
            strict = unexp & strict_novel(U, ref, t)       # descriptive: also no shared target, chemically distant
            row = {"library": name, "T": T, "budget": budget, "pool": len(pool),
                   "pool_hits": int(H[pool, t].sum()), "pool_unexpected": int(unexp[pool].sum()),
                   "pool_unexpected_strict": int(strict[pool].sum())}
            for arm in arms:
                path = out_dir / name / T / f"{arm}.json"
                if path.exists():
                    rec = json.loads(path.read_text(encoding="utf-8"))
                else:
                    if arm.startswith("conv") and conv is None:
                        import conv_agent as CV
                        conv = CV.ConvAgent(U, U.name, out_dir)
                    # deterministic across processes (Python's hash() is salted per run)
                    seed = cfg["seed"] + int(hashlib.sha256(f"{name}|{T}|{arm}".encode()).hexdigest()[:8], 16) % 100000
                    st, extra = one_campaign(U, prior, arm, t, ref, pool, budget, cfg["batch"], cfg, seed, conv)
                    if isinstance(extra, list):      # the conventional arm returns its per-round LLM records
                        extra = {"llm_calls": extra}
                    sel = np.array([c for _, c in st.screened], int)
                    rec = RU.ledger(U, H, st, arm, extra={
                        "library": name, "unexpected": int(unexp[sel].sum()) if len(sel) else 0,
                        "unexpected_strict": int(strict[sel].sum()) if len(sel) else 0,
                        "verification": AG.verify(U, st), "screens": len(sel), "rounds": st.round,
                        "expected_hits_sum": float(np.nansum([p for _, p in st.predictions])), **extra})
                    RU.write_json(path, rec)
                row[f"{arm}|hits"] = rec["hits"]
                row[f"{arm}|unexpected"] = rec["unexpected"]
                row[f"{arm}|unexpected_strict"] = rec.get("unexpected_strict", 0)
                row[f"{arm}|verified"] = rec["verification"]["verified"]
                row[f"{arm}|unverifiable"] = rec["verification"]["unverifiable"]
                row[f"{arm}|screens"] = rec["screens"]
                row[f"{arm}|rounds"] = rec["rounds"]
                row[f"{arm}|expected_hits"] = rec["expected_hits_sum"]
                for r in rec["refusals"]:
                    refusals[f"{arm}:{r['code']}"] += 1
            rows.append(row)
            print(name, T, {a: row[f"{a}|hits"] for a in ("fixed", "det", "vc_only", "agent_novc", "maestro", "conv")},
                  round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "ROWS.csv", index=False)
    g = df["T"].to_numpy()
    primary = {"H1_vc_contribution_unexpected": (df["maestro|unexpected"] - df["agent_novc|unexpected"]).to_numpy(float),
               "H2_agent_contribution_hits": (df["maestro|hits"] - df["vc_only|hits"]).to_numpy(float)}
    secondary = {"H3_vs_fixed_unexpected": (df["maestro|unexpected"] - df["fixed|unexpected"]).to_numpy(float),
                 "H4_vs_conv_unexpected": (df["maestro|unexpected"] - df["conv|unexpected"]).to_numpy(float),
                 "H5_feedback_vs_permuted_hits": (df["maestro|hits"] - df["maestro_perm|hits"]).to_numpy(float),
                 "H6_noninferior_to_det_hits": (df["maestro|hits"] - df["det|hits"]).to_numpy(float),
                 "H7_verified_vs_fixed_hits": (df["maestro|verified"] - df["fixed|verified"]).to_numpy(float),
                 "H8_conv_feedback_vs_permuted": (df["conv|hits"] - df["conv_perm|hits"]).to_numpy(float),
                 "H9_explore_stream_unexpected": (df["maestro_explore|unexpected"] - df["maestro|unexpected"]).to_numpy(float)}
    margins = {"H6_noninferior_to_det_hits": 0.10 * float(df["det|hits"].sum())}
    res = {"tier": tier, "config": cfg, "n_campaigns": int(len(df)),
           "reachable": {"hits": int(df.pool_hits.sum()), "unexpected": int(df.pool_unexpected.sum())},
           "totals": {f"{a}|{m}": int(df[f"{a}|{m}"].sum()) for a in arms
                      for m in ("hits", "unexpected", "unexpected_strict", "verified", "unverifiable", "screens", "rounds")},
           "primary": ST.family({k: (v, g) for k, v in primary.items()}, alpha=0.05),
           "secondary": ST.family({k: (v, g) for k, v in secondary.items()}, alpha=0.05, margins=margins),
           "calibration": {a: {"expected": round(float(df[f"{a}|expected_hits"].sum()), 2),
                               "observed": int(df[f"{a}|hits"].sum())} for a in ("maestro", "agent_novc", "det")},
           "refusals": dict(refusals), "seconds": round(time.time() - t0, 1)}
    res["headline"] = ("DUAL_CORE_CONFIRMED" if res["primary"]["H1_vc_contribution_unexpected"]["verdict"] == "PASS"
                       and res["primary"]["H2_agent_contribution_hits"]["verdict"] == "PASS"
                       and res["secondary"]["H6_noninferior_to_det_hits"]["verdict"] == "PASS" else "NOT_CONFIRMED")
    RU.write_json(out_dir / "RESULTS.json", res)
    print(json.dumps({k: res[k] for k in ("totals", "primary", "secondary", "headline", "calibration", "refusals")},
                     indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
