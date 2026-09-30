"""Score the dual-core v2 runs under `protocol.json` and write `outputs/dual_core_v2_20260928/analysis.json`.

File summary
- Path: research/dual_core_v2/report.py
- Purpose: one pass over the v2 traces and ablation records that computes every registered quantity
  (and the labelled diagnostics). Nothing here changes a run.
- Core points:
  - Integrity: jobs, audit problems, reproduction anchors, lineage, sources selected per model.
  - Risk control (repaired Learn-then-Test and repaired P2) by design (`split` primary,
    `nested_crossfit` descriptive) and world model, for both p-values.
  - Calibration of the step risk after selection with correct lineage (Platt on the calibration
    fold, scored on the test fold), next to block 7's numbers.
  - Risk ranking (AUROC with unit-cluster intervals) of step, plan and conservative plan risk.
  - Risk-select vs stop-only on the same measure at matched coverage, and the calibrated choice.
  - World comparison on identical executed steps (ablation), and the bottleneck ladder:
    forecast change, log-loss change, action change, outcome change, with the oracle ceiling.
  - The 2 x 3 world x policy grid on the split design's test folds.
- Interfaces: `main`; CLI `python -m research.dual_core_v2.report`
- Depends on: analysis.py, risk_control.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis as A
from . import risk_control as RC

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_v2_20260928"
SEED = A.SEED
WORLDS = ("reference", "v1", "v2")


def _by_arm(traces, arm, dataset=None):
    return [t for t in traces if t["arm"] == arm and (dataset is None or t["dataset"] == dataset)]


def _split_test(traces):
    """Traces on test folds under the split design: model (f, f+1) on fold f."""
    out = []
    for t in traces:
        f, g = sorted(t["model"])
        pair = (f, g) if (f + 1) % 5 == g else (g, f) if (g + 1) % 5 == f else None
        if pair is not None and t["fold"] == pair[0]:
            out.append(t)
    return out


def _split_cal(traces):
    out = []
    for t in traces:
        f, g = sorted(t["model"])
        pair = (f, g) if (f + 1) % 5 == g else (g, f) if (g + 1) % 5 == f else None
        if pair is not None and t["fold"] == pair[1]:
            out.append(t)
    return out


# ------------------------------------------------------------------------------------ integrity
def integrity(metas) -> dict:
    jobs = [m["job"] for m in metas]
    return {"jobs": len(jobs), "expected": 40, "problems": sum(len(m["problems"]) for m in metas),
            "anchor": {"episodes": sum(m["anchor"]["episodes"] for m in metas),
                       "matches": sum(m["anchor"]["matches"] for m in metas)},
            "lineage_training_folds": {"_".join(map(str, m["job"][:4])): m["lineage"]["training_folds"] for m in metas},
            "sources": {"_".join(map(str, m["job"][:4])): {w: m["world"][w]["source"] for w in ("v1", "v2")} for m in metas},
            "source_counts": {w: dict(Counter(f"{m['job'][0]}|{m['world'][w]['source']}" for m in metas)) for w in ("v1", "v2")},
            "validator_cannot_eliminate": sorted("_".join(map(str, m["job"][:4])) for m in metas
                                                 if not m["lineage"]["validator"].get("eliminates"))}


# ------------------------------------------------------------------------------------ risk control
def risk_control(traces) -> dict:
    out = {}
    for ds in ("sciplex3", "l1000"):
        for world in WORLDS:
            tr = _by_arm(traces, world, ds)
            if not tr:
                continue
            for design in ("split", "nested_crossfit"):
                for method in ("betting", "hb"):
                    r = A.certify_design(tr, design, method=method)
                    out[f"{ds}|{world}|{design}|{method}"] = {
                        "folds": {f: {k: v.get(k) for k in ("status", "policy", "abstains", "calibration_units",
                                                            "test_units", "plugin_policy", "plugin_status")}
                                  for f, v in r["folds"].items()},
                        "min_p": {f: (min(((k, c["p"]) for k, c in v["candidates"].items()), key=lambda x: x[1])
                                      if v.get("candidates") else None) for f, v in r["folds"].items()},
                        "certified_policy_test": A.summarise(r["test"]),
                        "plugin_test": A.summarise(r["plugin_test"])}
            p0 = A.episode_table(_split_test(tr), None)
            out[f"{ds}|{world}|split|P0_test"] = A.summarise(p0)
    return out


# ------------------------------------------------------------------------------------ calibration
def calibration(traces) -> dict:
    from research.dual_core import e2 as E2
    out = {}
    for ds in ("sciplex3", "l1000"):
        for world in WORLDS:
            tr = _by_arm(traces, world, ds)
            if not tr:
                continue
            steps = A.step_table(tr)
            if steps.empty:
                continue
            steps = steps.dropna(subset=["risk_step"])
            parts = []
            for f in A.FOLDS:
                c = (f + 1) % 5
                m = "m" + "".join(map(str, sorted((f, c))))
                cal = steps[(steps.model == m) & (steps.fold == c)].rename(columns={"risk_step": "risk"})
                test = steps[(steps.model == m) & (steps.fold == f)].rename(columns={"risk_step": "risk"})
                if cal.empty or test.empty:
                    continue
                fn, info = E2.platt(cal)
                parts.append(test.assign(calibrated=fn(test.risk.to_numpy()), slope=info.get("b")))
            if not parts:
                continue
            h = pd.concat(parts, ignore_index=True)
            y = h.wrong.to_numpy(float)
            nll = lambda p: -(y * np.log(np.clip(p, 1e-9, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-9, 1)))
            h = h.assign(nr=nll(h.risk.to_numpy()), nc=nll(h.calibrated.to_numpy()))
            u = h.groupby("unit").agg(obs=("wrong", "sum"), raw=("risk", "sum"), cal=("calibrated", "sum"),
                                      dn=("nc", "mean"), rn=("nr", "mean"))
            rng = np.random.default_rng(SEED)
            idx = rng.integers(len(u), size=(A.DRAWS, len(u)))
            ratio = lambda a, b: np.quantile(u[a].to_numpy()[idx].sum(1) / np.maximum(u[b].to_numpy()[idx].sum(1), 1e-12),
                                             [0.025, 0.975]).tolist()
            diff = (u.dn - u.rn).to_numpy()
            out[f"{ds}|{world}"] = {"steps": int(len(h)), "units": int(len(u)), "events": int(y.sum()),
                                    "observed_over_forecast_raw": float(y.sum() / h.risk.sum()),
                                    "raw_ci": ratio("obs", "raw"),
                                    "observed_over_forecast_calibrated": float(y.sum() / h.calibrated.sum()),
                                    "calibrated_ci": ratio("obs", "cal"),
                                    "nll_calibrated_minus_raw_unit_mean": float(diff.mean()),
                                    "nll_ci": np.quantile(diff[idx].mean(1), [0.025, 0.975]).tolist(),
                                    "platt_slopes": sorted({float(s) for s in h.slope.dropna()})}
    return out


# ------------------------------------------------------------------------------------ ranking
def ranking(traces) -> dict:
    out = {}
    test = _split_test(traces)
    for ds in ("sciplex3", "l1000"):
        for world in WORLDS:
            st = A.step_table(_by_arm(test, world, ds))
            for score in ("risk_step", "risk_plan", "risk_plan_upper"):
                if st.empty or st[score].notna().sum() == 0:
                    continue
                out[f"{ds}|{world}|{score}"] = A.risk_ranking(st.reset_index(drop=True), score, draws=1000)
    return out


# ------------------------------------------------------------------------------------ risk-select vs stop-only
def risk_select(traces, spec) -> dict:
    out = {}
    test = _split_test(traces)
    cal = _split_cal(traces)
    fine = np.unique(np.r_[np.linspace(0, 0.05, 101), np.linspace(0.05, 1.0, 96)])
    for ds in ("sciplex3", "l1000"):
        caps = spec["risk_select"]["caps"][ds]
        for world in ("reference", "v2"):
            p0 = _by_arm(test, world, ds)
            if not p0:
                continue
            units = sorted({str(t["unit"]) for t in p0})
            rng = np.random.default_rng(SEED)
            idx = rng.integers(len(units), size=(2000, len(units)))
            for measure, field in (("point", "plan"), ("upper", "plan_upper")):
                curve = {}
                for lam in fine:
                    u = A.unit_means(A.episode_table(p0, float(lam), field).astype({"wrong": float, "decided": float}))
                    curve[float(lam)] = u.reindex(units)
                cov_b = np.stack([curve[l].decided.to_numpy()[idx].mean(1) for l in fine])      # thresholds x draws
                wr_b = np.stack([curve[l].wrong.to_numpy()[idx].mean(1) for l in fine])
                for cap in caps[measure]:
                    arm = f"{world}|{measure}|{cap:g}"
                    rs = _by_arm(test, arm, ds)
                    if not rs:
                        continue
                    ur = A.unit_means(A.episode_table(rs, None).astype({"wrong": float, "decided": float,
                                                                         "correct": float})).reindex(units)
                    so = curve[min(fine, key=lambda l: abs(l - cap))]
                    rc, rw = ur.decided.to_numpy()[idx].mean(1), ur.wrong.to_numpy()[idx].mean(1)
                    risk_rs = np.where(rc > 0, rw / np.where(rc > 0, rc, 1), np.nan)
                    # stop-only risk interpolated at the risk-select coverage, per draw
                    matched = []
                    for b in range(idx.shape[0]):
                        c, w = cov_b[:, b], wr_b[:, b]
                        order = np.argsort(c, kind="stable")
                        cs, ws = c[order], w[order]
                        target, pos = rc[b], cs > 0
                        if target <= 0 or not pos.any() or target > cs.max() or target < cs[pos].min():
                            matched.append(np.nan)
                            continue
                        wi = np.interp(target, cs, ws)
                        matched.append(wi / target)
                    diff = risk_rs - np.asarray(matched)
                    ok = np.isfinite(diff)
                    out[f"{ds}|{world}|{measure}|{cap:g}"] = {
                        "risk_select": {"coverage": float(ur.decided.mean()), "wrong_per_episode": float(ur.wrong.mean()),
                                        "wrong_among_decided": RC.conditional_risk(ur.wrong, ur.decided),
                                        "correct": float(ur.correct.mean())},
                        "stop_only_same_cap": {"coverage": float(so.decided.mean()),
                                               "wrong_among_decided": RC.conditional_risk(so.wrong, so.decided)},
                        "matched_coverage_difference": float(np.nanmedian(diff)) if ok.any() else None,
                        "matched_coverage_ci": np.quantile(diff[ok], [0.025, 0.975]).tolist() if ok.sum() > 50 else None,
                        "undefined_draws": int((~ok).sum())}
            # calibrated choice: repaired P2 among {P0, caps} on the calibration fold, applied to the test fold
            for measure in ("point", "upper"):
                chosen_frames, picks = [], {}
                for f in A.FOLDS:
                    c = (f + 1) % 5
                    m = "m" + "".join(map(str, sorted((f, c))))
                    arms = {1.0: world, **{cap: f"{world}|{measure}|{cap:g}" for cap in caps[measure]}}
                    cal_losses, test_frames = {}, {}
                    for key, arm in arms.items():
                        ct = [t for t in cal if t["arm"] == arm and t["dataset"] == ds and A.model_id(t) == m]
                        tt = [t for t in test if t["arm"] == arm and t["dataset"] == ds and A.model_id(t) == m]
                        if not ct or not tt:
                            continue
                        cal_losses[key] = RC.unit_losses(A.episode_table(ct, None))
                        test_frames[key] = A.episode_table(tt, None)
                    if 1.0 not in cal_losses:
                        continue
                    units_c = cal_losses[1.0].units
                    cal_losses = {k: RC.unit_losses(pd.DataFrame({"unit": list(v.units), "wrong": v.wrong, "decided": v.decided}),
                                                    units_c) for k, v in cal_losses.items()}
                    pick, status = RC.plugin_select(cal_losses, cal_losses[1.0], alpha=0.05, rho=0.5)
                    picks[f] = (pick, status)
                    chosen_frames.append(RC.apply_policy(test_frames, pick))
                if chosen_frames:
                    out[f"{ds}|{world}|{measure}|calibrated_P2"] = {"picks": picks,
                                                                   "test": A.summarise(pd.concat(chosen_frames, ignore_index=True))}
    return out


# ------------------------------------------------------------------------------------ world comparison and ladder
def _nll(record, variant, truth):
    probs = record["forecasts"].get(variant, {}).get(truth)
    if not probs:
        return np.nan
    return -np.log(max(probs.get(record["label"], 0.0), 1e-12))


def ladder(traces, ablation) -> dict:
    truth_of = {(t["compound"], t["h1"], t["h2"], t["dataset"]): t["truth"] for t in traces}
    frame = []
    for r in ablation:
        f, g = sorted(r["model"])
        test_fold = f if (f + 1) % 5 == g else g if (g + 1) % 5 == f else None
        if r["fold"] != test_fold:                  # split design: test role only, one model per episode
            continue
        ds = r["dataset"]
        tr = truth_of.get((r["compound"], r["h1"], r["h2"], ds))
        if tr is None:
            continue
        row = {"dataset": ds, "arm": r["arm"], "unit": str(r["unit"]), "step": r["step"], "prompts": r["prompts"],
               "source_v2": r["sources"].get("v2"), "source_v1": r["sources"].get("v1")}
        for v in r["forecasts"]:
            row[f"nll_{v}"] = _nll(r, v, tr)
            fr, fv = r["forecasts"].get("reference", {}).get(tr, {}), r["forecasts"][v].get(tr, {})
            row[f"tv_{v}"] = 0.5 * sum(abs(fv.get(k, 0.0) - fr.get(k, 0.0)) for k in set(fr) | set(fv)) if fr and fv else np.nan
            row[f"changed_{v}"] = r["choice"].get(v) != r["choice"].get("reference")
        frame.append(row)
    df = pd.DataFrame(frame)
    out = {}
    rng = np.random.default_rng(SEED)
    for (ds, arm), g in df.groupby(["dataset", "arm"]):
        for scope, h in (("all_steps", g), ("steps_with_prompt", g[g.prompts > 0])):
            if h.empty:
                continue
            entry = {"steps": int(len(h)), "units": int(h.unit.nunique()),
                     "v2_sources": h.source_v2.value_counts().to_dict(), "v1_sources": h.source_v1.value_counts().to_dict()}
            u = h.groupby("unit")
            idx = rng.integers(u.ngroups, size=(A.DRAWS, u.ngroups))
            for v in ("v1", "v2", "prompt", "transfer", "additive", "transfer_dist", "oracle"):
                if f"nll_{v}" not in h:
                    continue
                d = (u[f"nll_{v}"].mean() - u["nll_reference"].mean()).to_numpy()
                ok = np.isfinite(d)
                entry[v] = {"nll_minus_reference": float(np.nanmean(d)),
                            "ci": np.quantile(np.nanmean(np.where(ok, d, np.nan)[idx], axis=1), [0.025, 0.975]).tolist(),
                            "forecast_tv_from_reference_mean": float(h[f"tv_{v}"].mean()),
                            "share_forecast_changed": float((h[f"tv_{v}"] > 1e-9).mean()),
                            "share_action_changed": float(h[f"changed_{v}"].mean())}
            d = (u["nll_v2"].mean() - u["nll_v1"].mean()).to_numpy()
            entry["v2_minus_v1"] = {"nll": float(d.mean()), "ci": np.quantile(d[idx].mean(1), [0.025, 0.975]).tolist()}
            out[f"{ds}|{arm}|{scope}"] = entry
    return out


def outcome_changes(traces) -> dict:
    """Live arms on identical episodes: how often the action sequence and the decision differ from reference."""
    out = {}
    test = _split_test(traces)
    key = lambda t: (t["compound"], t["h1"], t["h2"], tuple(t["model"]))
    for ds in ("sciplex3", "l1000"):
        ref = {key(t): t for t in _by_arm(test, "reference", ds)}
        for world in ("v1", "v2", "oracle"):
            other = {key(t): t for t in _by_arm(test, world, ds)}
            common = sorted(set(ref) & set(other))
            if not common:
                continue
            first = sum((ref[k]["steps"][0]["action"] if ref[k]["steps"] else None) !=
                        (other[k]["steps"][0]["action"] if other[k]["steps"] else None) for k in common)
            seq = sum([s["action"] for s in ref[k]["steps"]] != [s["action"] for s in other[k]["steps"]] for k in common)
            outcome = sum((ref[k]["score"]["correct"], ref[k]["score"]["wrong"]) !=
                          (other[k]["score"]["correct"], other[k]["score"]["wrong"]) for k in common)
            two_prompts = sum(1 for k in common for s in other[k]["steps"] if (s.get("note") or {}).get("prompts", 0) >= 2)
            fa, fb = A.episode_table([ref[k] for k in common], None), A.episode_table([other[k] for k in common], None)
            out[f"{ds}|{world}-reference"] = {"episodes": len(common), "first_action_differs": first,
                                              "sequence_differs": seq, "decision_outcome_differs": outcome,
                                              "steps_with_two_or_more_prompts": two_prompts,
                                              "correct": A.paired_difference(fb, fa, "correct"),
                                              "wrong_per_episode": A.paired_difference(fb, fa, "wrong"),
                                              "coverage": A.paired_difference(fb, fa, "decided"),
                                              "wrong_among_decided": A.paired_difference(fb, fa, "wrong_among_decided")}
    return out


# ------------------------------------------------------------------------------------ 2 x 3 grid
def grid(traces, spec) -> dict:
    out = {}
    test, cal = _split_test(traces), _split_cal(traces)
    for ds in ("sciplex3", "l1000"):
        cap = spec["risk_select"]["caps"][ds]["point"][1]
        cells = {}
        for world in ("reference", "v2"):
            p0 = _by_arm(test, world, ds)
            if not p0:
                continue
            cells[(world, "P0")] = A.episode_table(p0, None)
            # stop-only on step risk at the repaired-P2 threshold chosen on the calibration fold
            frames = []
            for f in A.FOLDS:
                c = (f + 1) % 5
                m = "m" + "".join(map(str, sorted((f, c))))
                ct = [t for t in cal if t["arm"] == world and t["dataset"] == ds and A.model_id(t) == m]
                tt = [t for t in test if t["arm"] == world and t["dataset"] == ds and A.model_id(t) == m]
                if not ct or not tt:
                    continue
                units_c = sorted({str(t["unit"]) for t in ct})
                losses = {lam: RC.unit_losses(A.episode_table(ct, lam), units_c) for lam in A.candidates()}
                pick, _ = RC.plugin_select(losses, losses[1.0], alpha=0.05, rho=0.5)
                frames.append(RC.apply_policy({lam: A.episode_table(tt, lam) for lam in A.candidates()}, pick))
            cells[(world, "stop_only")] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            rs = _by_arm(test, f"{world}|point|{cap:g}", ds)
            cells[(world, "risk_select")] = A.episode_table(rs, None) if rs else pd.DataFrame()
        if len(cells) < 6:
            continue
        units = sorted(set(cells[("reference", "P0")].unit))
        rng = np.random.default_rng(SEED)
        idx = rng.integers(len(units), size=(A.DRAWS, len(units)))
        means = {k: A.unit_means(v.astype({c: float for c in ("wrong", "decided", "correct", "abstained")})).reindex(units)
                 for k, v in cells.items()}
        res = {"cells": {f"{w}|{p}": A.summarise(v) for (w, p), v in cells.items()}, "effects": {}}
        for metric in ("decided", "wrong", "correct", "measurements"):
            m = {k: v[metric].to_numpy()[idx].mean(1) for k, v in means.items()}
            for policy in ("stop_only", "risk_select"):
                inter = (m[("v2", policy)] - m[("v2", "P0")]) - (m[("reference", policy)] - m[("reference", "P0")])
                res["effects"][f"{metric}|interaction|{policy}"] = np.quantile(inter, [0.025, 0.5, 0.975]).tolist()
                res["effects"][f"{metric}|policy_effect_reference|{policy}"] = np.quantile(
                    m[("reference", policy)] - m[("reference", "P0")], [0.025, 0.5, 0.975]).tolist()
            res["effects"][f"{metric}|world_effect_P0"] = np.quantile(m[("v2", "P0")] - m[("reference", "P0")],
                                                                       [0.025, 0.5, 0.975]).tolist()
        out[ds] = res
    return out


def main() -> dict:
    spec = A.protocol()
    runs = A.load_runs(parts=("traces", "ablation"))
    traces, ablation, metas = runs["traces"], runs["ablation"], runs["meta"]
    result = {"protocol": "research/dual_core_v2/protocol.json", "integrity": integrity(metas),
              "risk_control": risk_control(traces), "calibration": calibration(traces), "ranking": ranking(traces),
              "risk_select": risk_select(traces, spec), "ladder": ladder(traces, ablation),
              "outcome_changes": outcome_changes(traces), "grid": grid(traces, spec)}
    (OUT / "analysis.json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str)[:4000])
