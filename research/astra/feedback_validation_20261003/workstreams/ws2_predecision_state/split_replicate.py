"""Split-replicate decoupling test of single-agent coupling on O'Neil (development, exposed).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/split_replicate.py
- Purpose: the O'Neil label subtracts a Bliss expectation built from the target line's measured
  single agents, and the world model's context features (mono_*, expected) are built from the
  SAME single-agent records. This script separates the shared measurement noise from the
  biology by splitting each single-agent dose point's replicate viabilities into two disjoint
  halves (scheme set by WS2_SPLIT: `odd_even` or `pair`, see SCHEMES) and rebuilding label and
  context from different halves.
- Core points:
  - Published X/X0 = median(viability) ** g with g constant per (batch, line) (g recovered from
    the published columns; verified to CV 0.000), so half-replicate X/X0 is exact, not modelled.
  - Builder logic copied from the frozen `screens._oneil_experiments`/`build_oneil` (batches 1-2,
    same-batch singles with the frozen fallback, log-concentration interpolation). With the
    published X/X0 it must reproduce `oneil_v1.npz` exactly or the script stops.
  - Configurations (label source, context source): coupled (A,A), (B,B); decoupled (A,B), (B,A).
    Arms: wm_static, wm_full, wm_nocontext (context-free), history, H+E static prior,
    heuristic_potency, heuristic_headroom. Every selection is scored under its own label, under
    the other half's label (independent single-agent replicates, same combination wells) and
    under the published label.
  - Label artefact: correlation and hit agreement between labels A and B; share of the A-B label
    difference explained by a line + drug-in-line additive model (the structure the in-context
    feedback model learns).
- Interfaces: `WS2_SPLIT=odd_even|pair python split_replicate.py` -> outputs/split_replicate_<scheme>.json
- Depends on: common.py; research.certified_discovery.screens/xlsx (read-only).
"""
from __future__ import annotations

import math
import os
import pickle
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from common import (ONEIL, MaskedWorld, WorldConfig, agent, bootstrap_ci, columns_for, load, prior_metrics,
                    selected_rows, sha256_file, write_json)
from research.certified_discovery import screens
from research.certified_discovery.screens import LIBRARY_BATCHES, Library, _interp_log
from research.certified_discovery.xlsx import iter_rows

CACHE_DIR = Path(os.environ.get("WS2_CACHE", Path(__file__).resolve().parent / "outputs" / "cache"))
SOURCES = ("full", "A", "B")
# Replicate columns come in positively correlated pairs (1,2), (3,4), (5,6) (deviation
# correlations 0.20, 0.07, 0.16 on batch-1 six-replicate rows), so two split schemes are run:
#   odd_even: A = 1,3,5 / B = 2,4,6 (balanced, but halves share pair-level noise: conservative)
#   pair:     A = 1,2   / B = 5,6   (pair-disjoint; columns 3,4 unused)
# Three-replicate rows: odd_even A = 1,3 / B = 2; pair A = 1 / B = 3.
SCHEMES = {
    "odd_even": {6: ([0, 2, 4], [1, 3, 5]), 3: ([0, 2], [1])},
    "pair": {6: ([0, 1], [4, 5]), 3: ([0], [2])},
}
SCHEME = os.environ.get("WS2_SPLIT", "odd_even")
CONFIGS = (("A", "A"), ("A", "B"), ("B", "B"), ("B", "A"))


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_singles_split():
    """(batch, line, drug) -> {source: (conc, X/X0)} for full (published), A and B halves."""
    rows = iter_rows(screens.ONEIL_SINGLE)
    header = next(rows)
    col = {name: header.index(name) for name in ("BatchID", "cell_line", "drug_name", "X/X0")}
    conc_col = next(i for i, name in enumerate(header) if name and name.startswith("Drug_concentration"))
    via_cols = [header.index(f"viability{i}") for i in range(1, 7)]
    records = []
    g_samples = defaultdict(list)
    for row in rows:
        if not row or row[col["X/X0"]] in (None, ""):
            continue
        v = [_num(row[i]) for i in via_cols]
        reps = [x for x in v if x is not None]
        xx = float(row[col["X/X0"]])
        key = (row[col["BatchID"]], row[col["cell_line"]], row[col["drug_name"]].strip())
        records.append((key, float(row[conc_col]), reps, xx))
        med = float(np.median(reps))
        if med > 0 and xx > 0 and abs(math.log(med)) > 0.1:
            g_samples[key[:2]].append(math.log(xx) / math.log(med))
    g = {k: float(np.median(v)) for k, v in g_samples.items()}
    g_cv = {k: float(np.std(v) / abs(np.mean(v))) for k, v in g_samples.items()}
    grouped = {s: defaultdict(lambda: defaultdict(list)) for s in SOURCES}
    max_reconstruction_error = 0.0
    for key, conc, reps, xx in records:
        gk = g[key[:2]]
        recon = float(np.median(reps)) ** gk if np.median(reps) > 0 else 0.0
        max_reconstruction_error = max(max_reconstruction_error, abs(recon - xx))
        ia, ib = SCHEMES[SCHEME][len(reps)]
        half_a, half_b = [reps[i] for i in ia], [reps[i] for i in ib]
        grouped["full"][key][conc].append(xx)
        grouped["A"][key][conc].append(max(float(np.median(half_a)), 1e-9) ** gk)
        grouped["B"][key][conc].append(max(float(np.median(half_b)), 1e-9) ** gk)
    out = {}
    for s in SOURCES:
        out[s] = {}
        for key, by_conc in grouped[s].items():
            conc = np.array(sorted(by_conc))
            out[s][key] = (conc, np.array([np.mean(by_conc[x]) for x in conc]))
    meta = {"g_groups": len(g), "g_cv_max": max(g_cv.values()), "x_x0_reconstruction_max_abs_error": max_reconstruction_error,
            "rows": len(records), "replicate_counts": {str(n): int(sum(1 for r in records if len(r[2]) == n)) for n in (3, 6)}}
    return out, meta


def _single(singles, batch, line, drug):
    if (batch, line, drug) in singles:
        return singles[(batch, line, drug)], batch
    for other in ("1", "2", "3"):
        if (other, line, drug) in singles:
            return singles[(other, line, drug)], other
    return None, None


def load_inputs():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"oneil_split_inputs_{SCHEME}.pkl"
    if path.exists():
        with open(path, "rb") as handle:
            return pickle.load(handle)
    singles, meta = read_singles_split()
    combos = dict(screens._read_combinations())
    payload = (singles, meta, combos)
    with open(path, "wb") as handle:
        pickle.dump(payload, handle)
    return payload


def build(singles_by_source, combos, label_src: str, context_src: str, reference: Library) -> Library:
    sl, sc = singles_by_source[label_src], singles_by_source[context_src]
    drug_index = {n: i for i, n in enumerate(reference.drugs)}
    line_index = {n: i for i, n in enumerate(reference.lines)}
    merged = defaultdict(list)
    combination_doses = defaultdict(set)
    for (batch, line, drug_a, drug_b), points in combos.items():
        if batch not in LIBRARY_BATCHES:
            continue
        la, _ = _single(sl, batch, line, drug_a)
        lb, _ = _single(sl, batch, line, drug_b)
        ca, _ = _single(sc, batch, line, drug_a)
        cb, _ = _single(sc, batch, line, drug_b)
        if la is None or lb is None:
            continue
        excess, expected = [], []
        for conc_a, conc_b, observed in points:
            excess.append(100.0 * (min(_interp_log(*la, conc_a), 1.0) * min(_interp_log(*lb, conc_b), 1.0) - observed))
            expected.append(1.0 - min(_interp_log(*ca, conc_a), 1.0) * min(_interp_log(*cb, conc_b), 1.0))
        i, j = sorted((drug_index[drug_a], drug_index[drug_b]))
        merged[(i, j, line_index[line])].append((float(np.mean(excess)), float(np.mean(expected))))
        combination_doses[(drug_index[drug_a], line_index[line])].update(p[0] for p in points)
        combination_doses[(drug_index[drug_b], line_index[line])].update(p[1] for p in points)
    keys = sorted(merged)
    a = np.array([k[0] for k in keys], dtype=np.int32)
    b = np.array([k[1] for k in keys], dtype=np.int32)
    c = np.array([k[2] for k in keys], dtype=np.int32)
    y = np.array([np.mean([e[0] for e in merged[k]]) for k in keys])
    exp_ = np.array([np.mean([e[1] for e in merged[k]]) for k in keys])
    mono_mean = np.full(reference.mono_mean.shape, np.nan)
    mono_top = np.full(reference.mono_top.shape, np.nan)
    for (d, l), doses in combination_doses.items():
        curve, _ = _single(sc, "1", reference.lines[l], reference.drugs[d])
        if curve is None:
            continue
        inhibition = [1.0 - min(_interp_log(*curve, dose), 1.0) for dose in sorted(doses)]
        mono_mean[d, l] = float(np.mean(inhibition))
        mono_top[d, l] = inhibition[-1]
    return Library(f"oneil_L{label_src}_C{context_src}", reference.drugs, reference.lines, a, b, c, y,
                   reference.cost_points, exp_, mono_mean, mono_top, reference.days_per_round, reference.threshold,
                   {"label_singles": label_src, "context_singles": context_src})


_LIBS: dict = {}


def _init(libs):
    _LIBS.update(libs)


def run_line(line: int) -> dict:
    out = {"line": line, "configs": {}}
    labels = {s: _LIBS[(s, s)].y[_LIBS[(s, s)].c == line] for s in ("A", "B", "full")}
    n = labels["A"].size
    budget = int(math.ceil(0.1 * n))
    out["random_expect"] = {s: float(budget * (labels[s] > 10).mean()) for s in ("A", "B", "full")}
    for (ls, cs) in CONFIGS:
        lib = _LIBS[(ls, cs)]
        y = lib.y[lib.c == line]
        world = MaskedWorld(lib, line, WorldConfig())
        nocontext = MaskedWorld(lib, line, WorldConfig(context=False))
        h_e = MaskedWorld(lib, line, WorldConfig(), columns=columns_for("HE"), identity_kernel=True)
        rec = {"prior_full": prior_metrics(world, y), "prior_HE": prior_metrics(h_e, y),
               "prior_nocontext": prior_metrics(nocontext, y)}
        sel = {
            "wm_static": selected_rows(lib, world, "wm_static", line),
            "wm_full": selected_rows(lib, world, "wm_full", line),
            "wm_nocontext": selected_rows(lib, nocontext, "wm_full", line),
            "HE_static": selected_rows(lib, h_e, "wm_static", line),
            "history": selected_rows(lib, world, "history", line),
        }
        for kind in ("heuristic_potency", "heuristic_headroom"):
            arm = agent.HeuristicArm(world, kind.split("_", 1)[1])
            res = agent.run_campaign(lib, world, arm, agent.CampaignSpec(kappa=2, audit_seeds=1), seed=line)
            rec[kind + "_own_hits"] = res["exploit"]["hits"]
            # reconstruct heuristic selection deterministically (static scores)
            scores = arm.scores(None, None)
            rng = np.random.default_rng(line)
            n = world.rows.size
            budget = int(math.ceil(0.1 * n))
            batch = int(math.ceil(budget / 4))
            measured = np.zeros(n, bool)
            order = []
            for r in range(4):
                k = int(min(batch, budget - measured.sum()))
                chosen = agent._top(scores, ~measured, k, rng)
                measured[chosen] = True
                order.extend(chosen.tolist())
            sel[kind] = np.array(order, int)
        other = "B" if ls == "A" else "A"
        rec["hits"] = {}
        for name, idx in sel.items():
            rec["hits"][name] = {
                "own": int((y[idx] > 10).sum()),
                "other_half": int((labels[other][idx] > 10).sum()),
                "published": int((labels["full"][idx] > 10).sum()),
                "own_mean_label": float(y[idx].mean()), "other_mean_label": float(labels[other][idx].mean()),
            }
        out["configs"][f"L{ls}_C{cs}"] = rec
    return out


def label_artefact(libs) -> dict:
    ya, yb, yf = libs[("A", "A")].y, libs[("B", "B")].y, libs[("full", "full")].y
    lib = libs[("A", "A")]
    hit_a, hit_b, hit_f = ya > 10, yb > 10, yf > 10
    d = ya - yb
    # share of the A-B difference explained by line + drug-in-line additive structure
    explained, total = 0.0, 0.0
    for l in np.unique(lib.c):
        k = lib.c == l
        n_drugs = len(lib.drugs)
        Z = np.zeros((k.sum(), n_drugs + 1))
        Z[:, 0] = 1
        span = np.arange(k.sum())
        Z[span, 1 + lib.a[k]] += 1
        Z[span, 1 + lib.b[k]] += 1
        coef, *_ = np.linalg.lstsq(Z, d[k], rcond=None)
        fit = Z @ coef
        explained += float(((fit - d[k].mean()) ** 2).sum())
        total += float(((d[k] - d[k].mean()) ** 2).sum())
    yh = ya > 10
    return {
        "pearson_label_A_B": float(np.corrcoef(ya, yb)[0, 1]),
        "pearson_label_A_published": float(np.corrcoef(ya, yf)[0, 1]),
        "hits_A": int(hit_a.sum()), "hits_B": int(hit_b.sum()), "hits_published": int(hit_f.sum()),
        "p_hitB_given_hitA": float(hit_b[hit_a].mean()), "p_hitA_given_hitB": float(hit_a[hit_b].mean()),
        "sd_label_difference_A_B": float(np.std(d)), "sd_label_published": float(np.std(yf)),
        "share_of_AB_difference_explained_by_line_plus_drug_in_line": explained / total,
        "within_line_spearman_expectedB_labelA_median": float(np.median([
            __import__("scipy").stats.spearmanr(libs[("A", "B")].expected[lib.c == l], ya[lib.c == l]).correlation
            for l in np.unique(lib.c)])),
        "within_line_spearman_expectedA_labelA_median": float(np.median([
            __import__("scipy").stats.spearmanr(libs[("A", "A")].expected[lib.c == l], ya[lib.c == l]).correlation
            for l in np.unique(lib.c)])),
        "n_hits_A_and_not_B": int((yh & ~hit_b).sum()),
    }


def summarise(per_line) -> dict:
    lines = sorted(r["line"] for r in per_line)
    by = {r["line"]: r for r in per_line}
    arms = list(by[lines[0]]["configs"]["LA_CA"]["hits"])
    out = {"totals": {}, "contrasts": {}}
    for cfg in by[lines[0]]["configs"]:
        out["totals"][cfg] = {}
        for arm in arms:
            out["totals"][cfg][arm] = {s: int(sum(by[l]["configs"][cfg]["hits"][arm][s] for l in lines))
                                       for s in ("own", "other_half", "published")}
        for p in ("prior_full", "prior_HE", "prior_nocontext"):
            out["totals"][cfg][p + "_top_budget_hits"] = int(sum(by[l]["configs"][cfg][p]["hits_top_budget"] for l in lines))
            out["totals"][cfg][p + "_spearman_median"] = float(np.median([by[l]["configs"][cfg][p]["spearman"] for l in lines]))

    def per_line_val(cfg, arm, s):
        return np.array([by[l]["configs"][cfg]["hits"][arm][s] for l in lines], float)

    for arm in arms:
        for s in ("own", "other_half"):
            coupled = (per_line_val("LA_CA", arm, s) + per_line_val("LB_CB", arm, s)) / 2
            decoupled = (per_line_val("LA_CB", arm, s) + per_line_val("LB_CA", arm, s)) / 2
            d = coupled - decoupled
            out["contrasts"][f"{arm}:coupled-decoupled:{s}"] = {"mean_per_line": float(d.mean()), "sum": float(d.sum()),
                                                               "ci95": bootstrap_ci(d)}
    # feedback gain under own vs other-half scoring (does feedback learn single-agent noise?)
    for cfgs, label in ((("LA_CA", "LB_CB"), "coupled"), (("LA_CB", "LB_CA"), "decoupled")):
        for s in ("own", "other_half"):
            for ref in ("wm_static", "history"):
                g = sum(per_line_val(c, "wm_full", s) - per_line_val(c, ref, s) for c in cfgs) / 2
                out["contrasts"][f"wm_full-{ref}:{label}:{s}"] = {"mean_per_line": float(g.mean()), "sum": float(g.sum()),
                                                                  "ci95": bootstrap_ci(g)}
    # random expectation per label (budget x line hit fraction) and history skill attenuation
    for cfg in ("LA_CA", "LB_CB"):
        ls = cfg[1]
        other = "B" if ls == "A" else "A"
        r_own = sum(by[l]["random_expect"][ls] for l in lines)
        r_oth = sum(by[l]["random_expect"][other] for l in lines)
        hist_own = out["totals"][cfg]["history"]["own"]
        hist_oth = out["totals"][cfg]["history"]["other_half"]
        f = (hist_oth - r_oth) / max(hist_own - r_own, 1e-9)
        entry = {"random_expected_own": r_own, "random_expected_other": r_oth, "history_skill_retention": f}
        for arm in ("wm_static", "wm_full", "wm_nocontext", "HE_static"):
            g_own = out["totals"][cfg][arm]["own"] - hist_own
            g_oth = out["totals"][cfg][arm]["other_half"] - hist_oth
            entry[arm] = {"gain_vs_history_own": g_own, "gain_vs_history_other": g_oth,
                          "expected_other_if_no_artefact": f * g_own}
            ml_own = np.array([by[l]["configs"][cfg]["hits"][arm]["own_mean_label"] - by[l]["configs"][cfg]["hits"]["history"]["own_mean_label"] for l in lines])
            ml_oth = np.array([by[l]["configs"][cfg]["hits"][arm]["other_mean_label"] - by[l]["configs"][cfg]["hits"]["history"]["other_mean_label"] for l in lines])
            entry[arm]["mean_label_gain_vs_history_own"] = {"mean": float(ml_own.mean()), "ci95": bootstrap_ci(ml_own)}
            entry[arm]["mean_label_gain_vs_history_other"] = {"mean": float(ml_oth.mean()), "ci95": bootstrap_ci(ml_oth)}
        out["coupled_pipeline_" + cfg] = entry
    # ratio of other-half to own hits per arm (replicability of selections under independent singles)
    for arm in arms:
        own = sum(out["totals"][c][arm]["own"] for c in ("LA_CA", "LB_CB", "LA_CB", "LB_CA"))
        oth = sum(out["totals"][c][arm]["other_half"] for c in ("LA_CA", "LB_CB", "LA_CB", "LB_CA"))
        out["contrasts"][f"{arm}:other_half_over_own"] = {"ratio": oth / max(own, 1), "own": own, "other": oth}
    return out


def main() -> int:
    started = time.time()
    singles, meta, combos = load_inputs()
    reference = load(ONEIL)
    libs = {}
    for ls in SOURCES:
        for cs in SOURCES:
            if (ls, cs) in CONFIGS or ls == cs:
                libs[(ls, cs)] = build(singles, combos, ls, cs, reference)
    full = libs[("full", "full")]
    parity = {
        "rows_equal": bool(np.array_equal(full.a, reference.a) and np.array_equal(full.b, reference.b) and np.array_equal(full.c, reference.c)),
        "y_max_abs": float(np.max(np.abs(full.y - reference.y))),
        "expected_max_abs": float(np.max(np.abs(full.expected - reference.expected))),
        "mono_mean_max_abs": float(np.nanmax(np.abs(full.mono_mean - reference.mono_mean))),
    }
    if not (parity["rows_equal"] and parity["y_max_abs"] < 1e-9 and parity["expected_max_abs"] < 1e-12):
        raise SystemExit(f"builder parity failed: {parity}")
    artefact = label_artefact(libs)
    with ProcessPoolExecutor(max_workers=16, initializer=_init, initargs=(libs,)) as pool:
        per_line = list(pool.map(run_line, range(len(reference.lines))))
    summary = summarise(per_line)
    payload = {"purpose": "WS2 split-replicate decoupling test (O'Neil development, exposed)",
               "oneil_single_sha256": sha256_file(screens.ONEIL_SINGLE), "oneil_combination_sha256": sha256_file(screens.ONEIL_COMBINATION),
               "library_sha256": sha256_file(ONEIL),
               "singles_meta": meta, "builder_parity": parity, "label_artefact": artefact, "summary": summary,
               "per_line": per_line, "wall_seconds": round(time.time() - started, 1)}
    payload["scheme"] = SCHEME
    payload["split"] = SCHEMES[SCHEME]
    path = write_json(f"split_replicate_{SCHEME}.json", payload)
    print(path)
    print("parity", parity)
    print("artefact", artefact)
    for cfg, t in summary["totals"].items():
        print(cfg, {k: v for k, v in t.items()})
    for k, v in summary["contrasts"].items():
        print(k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
