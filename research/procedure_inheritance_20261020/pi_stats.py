"""Summary statistics, resource accounting and the pre-registered development decision. Descriptive only: eight streams support no confidence-interval claim and no SUPPORT label.

Unit = one synthetic stream; its outcome for an arm/budget = mean realised shortlist utility of its 12 later-task backgrounds (batches 2-4).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import pi_run as R

DELTA = 0.01
LATER = (2, 3, 4)
ARMS_ALL = R.ARMS + R.XARMS


def load(run_dir):
    run_dir = Path(run_dir) / "streams"
    streams, x = {}, {}
    for p in sorted(run_dir.glob("*.json.gz")):
        if p.name.endswith(".xplant.json.gz"):
            d = R.read_gz(p)
            x[d["sid"]] = d
        else:
            d = R.read_gz(p)
            streams[d["sid"]] = d
    return streams, x


def _rows(d, x):
    rows = list(d["rows"])
    if x is not None:
        rows += x["rows"]
    return rows


def stream_means(streams, xp):
    """{sid: {(arm,B): mean utility over later tasks}}, plus oracle, plus anchors {sid: {(arm,ckpt): mean}} (B=4)."""
    out, anch, spent, cpu = {}, {}, {}, {}
    for sid, d in streams.items():
        rows = _rows(d, xp.get(sid))
        acc, sp, cp, an = {}, {}, {}, {}
        for r in rows:
            if r["role"] == "task" and r["batch"] in LATER:
                k = (r["arm"], r["budget_arm"])
                acc.setdefault(k, []).append(r["utility"])
                sp.setdefault(k, []).append(r["n_spent"])
                cp.setdefault(k, []).append(r["cpu_s"])
                if r["arm"] == "prior":
                    acc.setdefault(("oracle", r["budget_arm"]), []).append(r["oracle"])
            elif r["role"] == "anchor":
                an.setdefault((r["arm"], r["ckpt"]), []).append(r["utility"])
        out[sid] = {k: float(np.mean(v)) for k, v in acc.items()}
        spent[sid] = {k: float(np.mean(v)) for k, v in sp.items()}
        cpu[sid] = {k: float(np.sum(v)) for k, v in cp.items()}
        anch[sid] = {k: float(np.mean(v)) for k, v in an.items()}
    return out, anch, spent, cpu


def paired(means, a, b, sids=None):
    sids = sids or sorted(means)
    d = np.array([means[s][a] - means[s][b] for s in sids if a in means[s] and b in means[s]])
    if not len(d):
        return None
    return {"mean": float(d.mean()), "sd": float(d.std(ddof=1)) if len(d) > 1 else None, "n": int(len(d)), "n_positive": int((d > 0).sum()), "n_below_neg_delta": int((d < -DELTA).sum()),
            "min": float(d.min()), "max": float(d.max()), "per_stream": {s: float(means[s][a] - means[s][b]) for s in sids if a in means[s] and b in means[s]}}


def contrast_table(means):
    C = {}
    for B in (3, 4):
        for conv in ("f1_kg1", "f1_kg2", "f1_distill"):
            C[f"f1_plan@{B} - {conv}@{B}"] = paired(means, ("f1_plan", B), (conv, B))
        C[f"f1_plan@{B} - f1_plan_re@{B}"] = paired(means, ("f1_plan", B), ("f1_plan_re", B))
        C[f"f1_plan@{B} - f1_plan_nobranch@{B}"] = paired(means, ("f1_plan", B), ("f1_plan_nobranch", B))
        C[f"f1_plan@{B} - f1_plan_xplant@{B}"] = paired(means, ("f1_plan", B), ("f1_plan_xplant", B))
        C[f"f1_kg2@{B} - f1_kg1@{B}"] = paired(means, ("f1_kg2", B), ("f1_kg1", B))
        C[f"f1_distill@{B} - f1_kg2@{B}"] = paired(means, ("f1_distill", B), ("f1_kg2", B))
        C[f"f1_kg1@{B} - f0_kg1@{B}"] = paired(means, ("f1_kg1", B), ("f0_kg1", B))
        C[f"f0_plan@{B} - f1_plan@{B}"] = paired(means, ("f0_plan", B), ("f1_plan", B))
        C[f"f1_kg1@{B} - exploit@{B}"] = paired(means, ("f1_kg1", B), ("exploit", B))
    C["PRIMARY f1_plan@3 - f1_kg2@4 (one assay unit saved?)"] = paired(means, ("f1_plan", 3), ("f1_kg2", 4))
    C["f1_kg2@3 - f1_kg2@4"] = paired(means, ("f1_kg2", 3), ("f1_kg2", 4))
    C["f1_distill@3 - f1_kg2@4"] = paired(means, ("f1_distill", 3), ("f1_kg2", 4))
    C["f1_kg1@3 - f1_kg2@4"] = paired(means, ("f1_kg1", 3), ("f1_kg2", 4))
    # 2x2 factorial at each budget: factor inheritance (f0->f1) x plan inheritance (kg1 fresh -> plan)
    for B in (3, 4):
        f = {k: {s: means[s][(k, B)] for s in means} for k in ("f0_kg1", "f1_kg1", "f0_plan", "f1_plan")}
        inter = {s: (f["f1_plan"][s] - f["f1_kg1"][s]) - (f["f0_plan"][s] - f["f0_kg1"][s]) for s in means}
        v = np.array(list(inter.values()))
        C[f"2x2 interaction@{B}"] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "n": len(v), "per_stream": inter}
    return C


def by_kind(means):
    out = {}
    kinds = sorted({s.split("_")[0] for s in means})
    for k in kinds:
        sids = [s for s in means if s.startswith(k + "_")]
        out[k] = {}
        for name, a, b in (("plan@3-kg2@3", ("f1_plan", 3), ("f1_kg2", 3)), ("plan@4-kg2@4", ("f1_plan", 4), ("f1_kg2", 4)), ("plan@3-kg1@3", ("f1_plan", 3), ("f1_kg1", 3)),
                           ("kg2@3-kg1@3", ("f1_kg2", 3), ("f1_kg1", 3)), ("distill@3-kg2@3", ("f1_distill", 3), ("f1_kg2", 3)), ("plan@3-kg2@4", ("f1_plan", 3), ("f1_kg2", 4))):
            p = paired(means, a, b, sids)
            out[k][name] = None if p is None else {"mean": p["mean"], "n": p["n"]}
    return out


def retention(anch):
    """Anchors are never-released old-regime backgrounds (B=4): deployed arm minus fresh Kg1 on the same anchors at each checkpoint; plus drift of that gap."""
    out = {}
    for arm in ("f1_plan", "f1_plan_re", "f0_plan", "f1_distill", "f1_kg2"):
        out[arm] = {}
        for c in range(4):
            d = [anch[s][(arm, c)] - anch[s][("f1_kg1" if not arm.startswith("f0") else "f0_kg1", c)] for s in anch if (arm, c) in anch[s]]
            out[arm][str(c)] = {"mean_minus_fresh_kg1": float(np.mean(d)), "min_stream": float(np.min(d)), "n": len(d)}
    return out


def costs(streams, xp, cpu):
    """CPU seconds (process time, one numerical thread), mean per stream. total(arm,B) = shared factor learning + arm-specific learning + invocation over ALL 16 task backgrounds."""
    res = {}
    for B in (3, 4):
        for arm in ARMS_ALL:
            tot, parts = [], {"factor_learning": [], "arm_learning": [], "invocation_tasks": [], "n_candidates": [], "n_replays": []}
            for sid, d in streams.items():
                fl = 0.0 if arm in ("prior", "exploit") else (sum(g["factors"]["off"]["cpu_s"] for g in d["generations"]) if arm.startswith("f0") else
                                                                sum(g["factors"]["on"]["cpu_s"] for g in d["generations"]))
                al, nc, nr = 0.0, 0, 0
                if "plan" in arm and arm not in ("f1_plan_nobranch", "f1_plan_xplant"):
                    for g in d["generations"]:
                        rec = g["plans"][f"{arm}|{B}"]
                        al += rec["cpu_s"]
                        nc += rec["n_candidates"]
                        nr += rec["n_replays"]
                elif arm in ("f1_plan_nobranch", "f1_plan_xplant"):
                    for g in d["generations"]:                       # derived from the f1 plan: charged its full discovery
                        rec = g["plans"][f"f1_plan|{B}"]
                        al += rec["cpu_s"] if arm == "f1_plan_nobranch" else 0.0
                        nc += rec["n_candidates"]
                        nr += rec["n_replays"]
                elif arm == "f1_distill":
                    al = sum((g["student"] or {}).get("cpu_s", 0.0) for g in d["generations"])
                    nc = sum((g["student"] or {}).get("teacher_decisions", 0) for g in d["generations"])
                inv = cpu[sid].get((arm, B), 0.0)
                parts["factor_learning"].append(fl)
                parts["arm_learning"].append(al)
                parts["invocation_tasks"].append(inv)
                parts["n_candidates"].append(nc)
                parts["n_replays"].append(nr)
                tot.append(fl + al + inv)
            res[f"{arm}@{B}"] = {"total_cpu_s": float(np.mean(tot))} | {k: float(np.mean(v)) for k, v in parts.items()}
    return res


def breakeven(cost, n_later=16):
    """Reuse count N* at which discovering/learning the artifact costs less than planning fresh at every use: arm_learning / (per-use cpu of comparator - per-use cpu of arm)."""
    out = {}
    for B in (3, 4):
        for arm in ("f1_plan", "f1_distill"):
            for comp in ("f1_kg1", "f1_kg2"):
                a, c = cost[f"{arm}@{B}"], cost[f"{comp}@{B}"]
                per_a, per_c = a["invocation_tasks"] / n_later, c["invocation_tasks"] / n_later
                gap = per_c - per_a
                learn = a["arm_learning"]
                out[f"{arm}@{B} vs fresh {comp}"] = {"arm_learning_cpu_s": learn, "per_use_cpu_arm": per_a, "per_use_cpu_fresh": per_c,
                                                    "break_even_uses": (learn / gap) if gap > 1e-9 else None, "uses_in_study": n_later}
    return out


def exits(streams, xp):
    out = {}
    for sid, d in streams.items():
        rows = _rows(d, xp.get(sid))
        o = {"unknown_exit_novel_regime": [0, 0], "unknown_exit_known_regime": [0, 0], "plan_inapplicable": 0, "plan_invocations": 0, "plan_stop": 0, "branch_counts": {}, "direct_fallback": 0}
        for r in rows:
            if r["role"] != "task" or r["arm"] not in ARMS_ALL:
                continue
            if r["arm"] in ("f1_kg1", "f1_kg2", "f1_plan", "f1_distill"):
                novel = r["regime"] == 5
                key = "unknown_exit_novel_regime" if novel else "unknown_exit_known_regime"
                o[key][0] += int(r["exit_unknown"])
                o[key][1] += 1
            if r["arm"] == "f1_plan":
                if r.get("plan_applicable") is not None:
                    o["plan_invocations"] += 1
                    o["plan_inapplicable"] += int(r["plan_applicable"] is False)
                    if r.get("branch") is not None:
                        o["branch_counts"][str(r["branch"])] = o["branch_counts"].get(str(r["branch"]), 0) + 1
                    o["plan_stop"] += int(bool(r.get("plan_stop")))
            o["direct_fallback"] += int(r.get("direct_fallback", 0))
        out[sid] = o
    return out


def lifecycle(streams):
    out = {}
    for sid, d in streams.items():
        rec = {}
        for arm in ("f1_plan", "f0_plan", "f1_plan_re"):
            for B in (3, 4):
                st = [g["plans"][f"{arm}|{B}"] for g in d["generations"]]
                rec[f"{arm}|{B}"] = {"statuses": [s["status"] for s in st], "deployed_checkpoints": int(sum(s["deployed"] is not None for s in st)),
                                     "reuse_events": int(sum(s["status"] == "incumbent_kept" or s["best_source"] == "archive" and s["status"] == "demonstrated" for s in st)),
                                     "strict_rule_would_pass": int(sum(bool((s["vs_incumbent"] or {}).get("strict_library_rule")) for s in st)),
                                     "n_candidates": [s["n_candidates"] for s in st]}
        rec["factors"] = {m: [{"n_regimes": g["factors"][m]["n_regimes"], "n_candidates": g["factors"][m]["n_candidates"]} for g in d["generations"]] for m in ("on", "off")}
        out[sid] = rec
    return out


def decide(means, anch, delta=DELTA):
    sids = sorted(means)

    def pooled(a, b):
        return float(np.mean([means[s][a] - means[s][b] for s in sids]))
    d = {"delta": delta}
    for B in (3, 4):
        conv = {s: max(means[s][("f1_kg2", B)], means[s][("f1_distill", B)]) for s in sids}
        diff = np.array([means[s][("f1_plan", B)] - conv[s] for s in sids])
        d[f"B{B}"] = {"plan_minus_best_conventional_pooled": float(diff.mean()), "streams_plan_at_least_conventional": int((diff >= 0).sum()),
                      "plan_minus_fresh_kg1_pooled": pooled(("f1_plan", B), ("f1_kg1", B)),
                      "plan_minus_nobranch_pooled": pooled(("f1_plan", B), ("f1_plan_nobranch", B)),
                      "plan_minus_xplant_pooled": pooled(("f1_plan", B), ("f1_plan_xplant", B))}
    prim = pooled(("f1_plan", 3), ("f1_kg2", 4))
    d["primary_unit_saving_pooled"] = prim
    d["primary_unit_saving_holds"] = bool(prim >= -delta)
    d["worst_stream_plan_minus_kg1"] = float(min(means[s][("f1_plan", B)] - means[s][("f1_kg1", B)] for s in sids for B in (3, 4)))
    ret = min(anch[s][("f1_plan", c)] - anch[s][("f1_kg1", c)] for s in anch for c in range(4))
    d["worst_anchor_plan_minus_kg1"] = float(ret)
    beats = {B: d[f"B{B}"]["plan_minus_best_conventional_pooled"] >= delta and d[f"B{B}"]["streams_plan_at_least_conventional"] >= 6 for B in (3, 4)}
    abl = {B: d[f"B{B}"]["plan_minus_nobranch_pooled"] >= delta / 2 and d[f"B{B}"]["plan_minus_xplant_pooled"] >= delta / 2 for B in (3, 4)}
    nobenefit = all(d[f"B{B}"]["plan_minus_fresh_kg1_pooled"] < delta for B in (3, 4))
    plan_vs_conv_all = all(d[f"B{B}"]["plan_minus_best_conventional_pooled"] < delta for B in (3, 4))
    if beats[3] and abl[3] and d["worst_anchor_plan_minus_kg1"] >= -delta and d["worst_stream_plan_minus_kg1"] >= -delta:
        label = "ADVANCE_TO_POWERED_INDEPENDENT_DESIGN"
    elif nobenefit:
        label = "CLOSE_NO_PRACTICAL_BENEFIT_OVER_FRESH_ONE_STEP_PLANNING"
    elif plan_vs_conv_all:
        label = "CLOSE_EXPLAINED_BY_CONVENTIONAL_LOOKAHEAD_OR_DISTILLATION"
    else:
        label = "INCONCLUSIVE_DEVELOPMENT"
    d["label"] = label
    return d


def build_summary(run_dir, cfg=None):
    streams, xp = load(run_dir)
    means, anch, spent, cpu = stream_means(streams, xp)
    cost = costs(streams, xp, cpu)
    full = {"n_streams": len(streams), "stream_ids": sorted(streams), "pooled_means": {f"{a}@{B}": float(np.mean([means[s][(a, B)] for s in means if (a, B) in means[s]]))
                                                                                         for a in ARMS_ALL for B in (3, 4) if all((a, B) in means[s] for s in means)},
            "oracle_mean": float(np.mean([means[s][("oracle", 4)] for s in means])),
            "units_spent": {f"{a}@{B}": float(np.mean([spent[s][(a, B)] for s in spent if (a, B) in spent[s]])) for a in ARMS_ALL for B in (3, 4) if all((a, B) in spent[s] for s in spent)},
            "per_stream_means": {s: {f"{a}@{B}": v for (a, B), v in means[s].items()} for s in sorted(means)},
            "contrasts": contrast_table(means), "by_kind": by_kind(means), "retention": retention(anch), "costs": cost, "break_even": breakeven(cost),
            "exits": exits(streams, xp), "lifecycle": lifecycle(streams), "decision": decide(means, anch),
            "elapsed": {"wall_s_sum": float(sum(d["resources"]["wall_s"] for d in streams.values())), "cpu_s_sum": float(sum(d["resources"]["cpu_s"] for d in streams.values())),
                        "xplant_cpu_s_sum": float(sum(d["cpu_s"] for d in xp.values()))}}
    return json.loads(json.dumps(full, default=float))


def diff_summaries(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: missing")
            else:
                out += diff_summaries(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += diff_summaries(x, y, f"{path}[{i}]")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        # CPU/wall figures are measurements stored in the run files; everything is recomputed from those files, so exact agreement to rounding is required
        if abs(a - b) > 1e-9 * max(1.0, abs(a), abs(b)):
            out.append(f"{path}: {a} != {b}")
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")
    return out


if __name__ == "__main__":
    import sys
    run = Path(sys.argv[1])
    out = Path(sys.argv[2])
    s = build_summary(run)
    out.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(s["decision"]["label"])
