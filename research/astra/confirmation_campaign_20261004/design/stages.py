"""EXPLORATORY stage runner of the design workstream (development -> selection -> evaluation -> feedback).

File summary
- Path: research/astra/confirmation_campaign_20261004/design/stages.py
- Purpose: run the frozen campaign contract v2 in stages, each with its own logged outcome access:
  `dev` (HD development targets only: P2 f-grid, P3, feedback gate, power; writes selection.json
  and feedback_gate.json), `feedback_dev` (HD only: fit F0/Fm/Ff and lambda; feedback_fit.json),
  `addendum` (hashes the selection, gate and fit files into plan_addendum_1.json), `eval` (E targets:
  primary R - C* and the registered descriptive secondaries) and `feedback_eval` (E role-swapped and
  same-condition feedback diagnostic).
- Core points:
  - Jaaks 2022 is exposed: every result is EXPLORATORY; outcome reads only via
    `common.exposed_ticket(purpose, "design")` and the frozen `jaaks.build_panels`.
  - The dev stage physically removes every E row from both role panels before any computation.
    E outcomes are used only by `eval` / `feedback_eval`, which refuse unless plan_addendum_1.json
    matches the selection / gate / fit files byte for byte.
  - Outputs go to new directories `design/results/<stage>_<stamp>/`; nothing is overwritten.
  - `--dry DIR` runs every stage on the frozen builder's synthetic release (no vault, no outcome of
    the real release) with all files written under DIR.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.design.stages {dev,feedback_dev,
  addendum,eval,feedback_eval,all_dry} [--dry DIR]`.
- Depends on: campaign.py, feedback.py; frozen jaaks builder, replay.load_design (design columns),
  repeats.model_id (event labels; imported only), the study's common.py.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import platform
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

from . import campaign as cp
from . import feedback as fb

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
PLATE_HIERARCHY = ROOT / "research/astra/reproducible_allocation_20261003/repeats/receipts/plate_hierarchy.csv"
CODE_FILES = ("design/campaign.py", "design/feedback.py", "design/stages.py", "design/test_design.py", "common.py",
              "protocol/campaign_contract.json", "protocol/partition.json")
FROZEN_IMPORTS = ("research/astra/feedback_validation_20261003/jaaks.py",
                  "research/astra/feedback_validation_20261003/study.py",
                  "research/certified_discovery/world.py", "research/certified_discovery/screens.py",
                  "research/astra/reproducible_allocation_20261003/allocation/replay.py",
                  "research/astra/reproducible_allocation_20261003/repeats/model_id.py",
                  "research/astra/reproducible_allocation_20261003/repeats/provenance.py",
                  "tools/datasets/combination_screens.py")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


@dataclass
class Ctx:
    dry: Path | None
    base: Path                       # where selection.json etc. live (design/ or the dry dir)
    source: Path
    partition: dict

    @property
    def selection(self) -> Path:
        return self.base / "selection.json"

    @property
    def gate(self) -> Path:
        return self.base / "feedback_gate.json"

    @property
    def fit(self) -> Path:
        return self.base / "feedback_fit.json"

    @property
    def addendum(self) -> Path:
        return self.base / "plan_addendum_1.json"

    def results_dir(self, stage: str) -> Path:
        d = self.base / "results" / f"{stage}_{time.strftime('%Y%m%d_%H%M%S')}"
        d.mkdir(parents=True, exist_ok=False)
        return d


def environment() -> dict:
    import pandas
    import scipy
    return {"python": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__, "pandas": pandas.__version__, "cwd": os.getcwd()}


def code_hashes() -> dict:
    out = {f"research/astra/confirmation_campaign_20261004/{p}": cp.sha256_file(STUDY / p) for p in CODE_FILES
           if (STUDY / p).exists()}
    out.update({p: cp.sha256_file(ROOT / p) for p in FROZEN_IMPORTS if (ROOT / p).exists()})
    return out


def write_jsonl_gz(path: Path, records) -> dict:
    if path.exists():
        raise FileExistsError(f"NO_OVERWRITE: {path}")
    n = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as handle:
        for r in records:
            handle.write(json.dumps(cp.jsonable(r), separators=(",", ":")) + "\n")
            n += 1
    return {"path": str(path), "records": n, "sha256": cp.sha256_file(path)}


# ============================================================================ data access
def synthetic_partition(tissues: dict) -> dict:
    """Same rule as protocol/make_partition.py on the synthetic lines; repeat lines = first two of each set."""
    split = {}
    for t, T in tissues.items():
        lines = sorted(T.lines)
        order = np.random.default_rng([cp.SEED, cp.TISSUE_CODE[t]]).permutation(len(lines))
        n_eval = len(lines) // 2
        E = sorted(lines[i] for i in order[:n_eval])
        HD = sorted(lines[i] for i in order[n_eval:])
        split[t] = {"E": E, "HD": HD, "repeat_lines_E": E[:2], "repeat_lines_HD": HD[:2]}
    return split


def open_data(ctx: Ctx, purpose: str) -> dict:
    from research.astra.feedback_validation_20261003 import jaaks
    from research.astra.reproducible_allocation_20261003.allocation import replay as rp

    t0 = time.perf_counter()
    if ctx.dry is not None:
        ticket = {"freeze_sha256": "DRY_RUN_NOT_A_VAULT", "data_sha256": cp.sha256_file(ctx.source),
                  "purpose": f"[design] DRY RUN (synthetic release): {purpose}"}
    else:
        from ..common import exposed_ticket
        ticket = exposed_ticket(purpose, "design")
    panels, report, candidates = jaaks.build_panels(ticket, ctx.source)
    design = rp.load_design(ctx.source)
    tissues = cp.build_tissues(panels, candidates, design)
    if ctx.partition is None:
        ctx.partition = synthetic_partition(tissues)
    for t, T in tissues.items():
        E, HD = set(ctx.partition[t]["E"]), set(ctx.partition[t]["HD"])
        if E & HD or (E | HD) != set(T.lines):
            raise AssertionError(f"PARTITION: {t} E/HD do not partition the builder lines")
    if ctx.dry is None:
        with open(PLATE_HIERARCHY, encoding="utf-8") as handle:
            event_of = {row["BARCODE"].strip(): row["event"] for row in csv.DictReader(handle)}
    else:
        event_of = None
    return {"ticket": ticket, "panels": panels, "report": report, "candidates": candidates, "design": design,
            "tissues": tissues, "event_of": event_of, "seconds": round(time.perf_counter() - t0, 2)}


def add_events(rec: dict, event_of: dict | None) -> dict:
    if "native_plates" in rec:
        if event_of is None:
            rec["n_seeding_events"] = rec["n_native_plates"]
            rec["seeding_events_source"] = "dry run: one event per plate"
        else:
            missing = [b for b in rec["native_plates"] if b not in event_of]
            if missing:
                raise AssertionError(f"plates without a seeding event: {missing[:3]}")
            rec["n_seeding_events"] = len({event_of[b] for b in rec["native_plates"]})
    return rec


def hd_targets(data: dict, part: dict):
    """HD development campaigns: E rows removed from both role panels; history = other HD lines."""
    for t in sorted(data["tissues"], key=lambda x: cp.TISSUES.index(x) if x in cp.TISSUES else 99):
        T = data["tissues"][t]
        HD, E = list(part[t]["HD"]), set(part[t]["E"])
        T_hd = cp.restrict(T, HD)
        if T_hd.present_lines & E:
            raise AssertionError("E rows present in the development view")
        for sidm in sorted(HD):
            allowed = set(HD) - {sidm}
            H = cp.restrict(T_hd, allowed)
            for role in cp.ROLES:
                tg = cp.make_target(T_hd, H, sidm, role, allowed_history=allowed, forbidden=E | {sidm})
                yield tg, cp.truth_of(T_hd, tg)


def e_targets(data: dict, part: dict):
    """E evaluation campaigns: history = all HD lines of the tissue (E lines never history)."""
    for t in sorted(data["tissues"], key=lambda x: cp.TISSUES.index(x) if x in cp.TISSUES else 99):
        T = data["tissues"][t]
        HD, E = set(part[t]["HD"]), set(part[t]["E"])
        H = cp.restrict(T, HD)
        for sidm in sorted(E):
            for role in cp.ROLES:
                tg = cp.make_target(T, H, sidm, role, allowed_history=HD, forbidden=E)
                yield tg, cp.truth_of(T, tg)


def loo_targets(data: dict):
    """All-lines sensitivity: every line, history = all other lines of the tissue (shared histories)."""
    for t in sorted(data["tissues"], key=lambda x: cp.TISSUES.index(x) if x in cp.TISSUES else 99):
        T = data["tissues"][t]
        for sidm in sorted(T.lines):
            allowed = set(T.lines) - {sidm}
            H = cp.restrict(T, allowed)
            for role in cp.ROLES:
                tg = cp.make_target(T, H, sidm, role, allowed_history=allowed, forbidden={sidm})
                yield tg, cp.truth_of(T, tg)


def tables(records_by: dict) -> tuple[dict, dict, list]:
    """records_by: name -> records; returns line values, arm tables and the sorted line keys."""
    lv = {name: cp.line_values(recs) for name, recs in records_by.items()}
    keys = cp.sort_keys(next(iter(lv.values())).keys()) if lv else []
    for name, v in lv.items():
        if set(v) != set(keys):
            raise AssertionError(f"{name}: line sets differ")
    return lv, {name: cp.arm_table(v, keys) for name, v in lv.items()}, keys


def confirmed(lv: dict, keys: list) -> np.ndarray:
    return np.array([lv[k]["confirmed"] for k in keys])


def menu_summary(metrics: list[dict], keys: list) -> dict:
    """Concordance (mean over defined roles, then over lines) and probability scores (R, C_prod)."""
    by = defaultdict(list)
    for m in metrics:
        by[(m["tissue"], m["line"])].append(m)
    out = {"concordance": {}, "probability": {}}
    for arm in cp.ARMS:
        vals, undefined = [], 0
        for k in keys:
            v = [m["concordance"][arm] for m in by[k] if m["concordance"][arm] is not None]
            undefined += sum(1 for m in by[k] if m["concordance"][arm] is None)
            if v:
                vals.append(float(np.mean(v)))
        out["concordance"][arm] = {"mean_over_lines": float(np.mean(vals)) if vals else None,
                                   "lines_defined": len(vals), "campaigns_undefined": undefined}
    for arm in cp.PROBABILITY_ARMS:
        line = {f: [] for f in ("brier", "log_loss", "calibration_in_the_large", "mean_pred", "observed_rate")}
        for k in keys:
            for f in line:
                line[f].append(float(np.mean([m["probability"][arm][f] for m in by[k]])))
        out["probability"][arm] = {f: float(np.mean(v)) for f, v in line.items()}
        out["probability"][arm]["quantity"] = cp.PROBABILITY_ARMS[arm]
    return out


def concordance_by_line(metrics: list[dict], keys: list, arm: str) -> dict:
    by = defaultdict(list)
    for m in metrics:
        if m["concordance"][arm] is not None:
            by[(m["tissue"], m["line"])].append(m["concordance"][arm])
    return {k: float(np.mean(by[k])) for k in keys if by[k]}


def prob_by_line(metrics: list[dict], keys: list, arm: str, field: str) -> np.ndarray:
    by = defaultdict(list)
    for m in metrics:
        by[(m["tissue"], m["line"])].append(m["probability"][arm][field])
    return np.array([float(np.mean(by[k])) for k in keys])


# ============================================================================ stage: dev
def select(dev_yield: dict) -> dict:
    best = {}
    for arm, by_fp in dev_yield.items():
        top = max(by_fp[fp] for fp in cp.FP_GRID)
        best[arm] = next(fp for fp in cp.FP_GRID if by_fp[fp] == top)          # ties -> smaller fp
    top_simple = max(dev_yield[a][best[a]] for a in cp.SIMPLE)
    c_star = next(a for a in cp.SIMPLE if dev_yield[a][best[a]] == top_simple)  # ties -> listed order
    return {"best_fp": best, "C_star": c_star, "fp_star": int(best[c_star]), "R_own_fp": int(best["R"])}


def stage_dev(ctx: Ctx) -> dict:
    for p in (ctx.selection, ctx.gate):
        if p.exists():
            raise SystemExit(f"REFUSED: {p} exists and is never overwritten")
    t0 = time.perf_counter()
    started = now()
    data = open_data(ctx, "design dev stage: HD development targets only (E rows removed first): P2 f-grid, "
                          "P3, feedback gate, power (plan.json)")
    out = ctx.results_dir("dev")
    p2, p3, gate_recs, metrics = defaultdict(list), defaultdict(list), defaultdict(list), []
    n_campaigns = 0
    for tg, truth in hd_targets(data, ctx.partition):
        n_campaigns += 1
        for arm in cp.ARMS:
            for fp in cp.FP_GRID:
                p2[(arm, fp)].append(add_events(cp.run_p2(tg, truth, arm, fp), data["event_of"]))
            p3[arm].append(add_events(cp.run_p3(tg, truth, arm), data["event_of"]))
        r = p3["R"][-1]
        joint = (truth["h_s"] & truth["h_v"]).astype(float)
        oracle_hook = (lambda st, j=joint, g=tg: (g.order(j), j))
        gate_recs["R"].append(r)
        gate_recs["oracle_round2_same_count"].append(add_events(cp.run_p3(
            tg, truth, "R", round2_order=oracle_hook, round2_count=r["round2_screens"],
            arm_label="R_round1+oracle_round2_same_count"), data["event_of"]))
        gate_recs["oracle_round2_reserve_rule"].append(add_events(cp.run_p3(
            tg, truth, "R", round2_order=oracle_hook, arm_label="R_round1+oracle_round2_reserve_rule"),
            data["event_of"]))
        metrics.append(cp.menu_metrics(tg, truth))
    sim_seconds = time.perf_counter() - t0
    lv2, tab2, keys = tables({f"{a}|{fp}": recs for (a, fp), recs in p2.items()})
    lv3, tab3, _ = tables(p3)
    lvg, tabg, _ = tables(gate_recs)
    dev_yield = {a: {fp: tab2[f"{a}|{fp}"]["confirmed"] for fp in cp.FP_GRID} for a in cp.ARMS}
    sel = select({a: dev_yield[a] for a in cp.PREDICTORS})
    c_star, fp_star, fp_r = sel["C_star"], sel["fp_star"], sel["R_own_fp"]
    x = confirmed(lv2[f"R|{fp_star}"], keys)
    y = confirmed(lv2[f"{c_star}|{fp_star}"], keys)
    strata = np.array([k[0] for k in keys])
    dev_contrast = cp.boot_contrast(x, y, keys)
    base_sizes = {t: len(ctx.partition[t]["E"]) for t in ctx.partition}
    t_pow = time.perf_counter()
    power = cp.power_analysis(x - y, y, strata, base_sizes=base_sizes, sims=4000 if ctx.dry is None else 200)
    power["seconds"] = round(time.perf_counter() - t_pow, 1)
    # gate
    r_yield = tabg["R"]["confirmed"]
    head_a = tabg["oracle_round2_same_count"]["confirmed"]
    head_b = tabg["oracle_round2_reserve_rule"]["confirmed"]
    rel_a = head_a / r_yield - 1.0 if r_yield else None
    rel_b = head_b / r_yield - 1.0 if r_yield else None
    with_r2 = sum(1 for r in gate_recs["R"] if r["round2_screens"] >= 1)
    frac = with_r2 / len(gate_recs["R"])
    pass_a = bool(rel_a is not None and rel_a >= 0.05)
    pass_b = bool(frac >= 0.5)
    files = {"P2_grid": write_jsonl_gz(out / "campaigns_p2_grid.jsonl.gz",
                                       (r for (a, fp) in sorted(p2) for r in p2[(a, fp)])),
             "P3": write_jsonl_gz(out / "campaigns_p3.jsonl.gz", (r for a in cp.ARMS for r in p3[a])),
             "gate": write_jsonl_gz(out / "campaigns_gate.jsonl.gz", (r for k in gate_recs for r in gate_recs[k])),
             "menu_metrics": write_jsonl_gz(out / "menu_metrics.jsonl.gz", metrics)}
    summary = {"status": cp.STATUS, "stage": "dev (HD development targets only)", "started": started,
               "ticket": data["ticket"], "build_report": data["report"], "lines": len(keys), "campaigns": n_campaigns,
               "P2_dev_table": {k: v for k, v in tab2.items()}, "P3_dev_table": tab3, "gate_tables": tabg,
               "dev_yield": dev_yield, "selection": sel, "dev_contrast_R_minus_Cstar_in_sample": dev_contrast,
               "menu_metrics_dev": menu_summary(metrics, keys),
               "per_line_confirmed": {name: {"|".join(k): v["confirmed"] for k, v in lv.items()}
                                      for name, lv in {**lv2, **{f"P3|{a}": lv3[a] for a in lv3}}.items()},
               "files": files}
    gate = {"status": cp.STATUS, "written_at": now(), "computed_on": "HD development campaigns (HD line x role), "
            "predictor R under P3", "results_dir": str(out),
            "a_round2_headroom": {"rule": "hold R's P3 round-1 purchases fixed; an oracle chooses only the round-2 "
                                          "screens by the true joint outcome (same count as R, hence the same "
                                          "reserve); pass iff its HD yield exceeds R's P3 HD yield by >= 5% relative",
                                  "R_P3_HD_yield": r_yield, "oracle_round2_same_count_yield": head_a,
                                  "relative_headroom": rel_a, "pass": pass_a,
                                  "variant_oracle_order_with_reserve_rule_yield": head_b,
                                  "variant_relative_headroom": rel_b},
            "b_round2_screening": {"rule": ">= 50% of HD campaigns (R, P3) buy >= 1 round-2 screen",
                                   "campaigns": len(gate_recs["R"]), "with_round2_screens": with_r2,
                                   "fraction": frac, "pass": pass_b},
            "pass": bool(pass_a and pass_b),
            "consequence": "feedback diagnostic RUNS" if (pass_a and pass_b) else "feedback diagnostic NOT RUN"}
    selection = {"status": cp.STATUS, "written_at": now(), "contract": "protocol/campaign_contract.json (v2, frozen)",
                 "rule": "HD development targets only, P2, measurement cap; development yield = sum over all HD lines "
                         "(pooled across tissues) of the line value; per simple predictor best fp (ties -> smaller fp); "
                         "C* = highest yield at its best fp among (S_both, L_v, C_s, C_v, C_mean, C_prod) (ties -> "
                         "listed order); fp* = C*'s best fp; R and S excluded from C* selection; R's own best fp "
                         "selected the same way (H2)",
                 "fp_grid": list(cp.FP_GRID), "C_star": c_star, "fp_star": int(fp_star), "R_own_fp": int(fp_r),
                 "own_fp": {a: int(sel["best_fp"][a]) for a in cp.PREDICTORS},
                 "dev_yield": {a: {str(fp): dev_yield[a][fp] for fp in cp.FP_GRID} for a in cp.ARMS},
                 "dev_yield_at_best_fp": {a: dev_yield[a][sel["best_fp"][a]] for a in cp.PREDICTORS},
                 "dev_lines": len(keys), "dev_campaigns": n_campaigns,
                 "dev_contrast_R_minus_Cstar_at_fp_star_in_sample": dev_contrast,
                 "power": power, "results_dir": str(out), "ticket": data["ticket"]}
    summary["power"] = power
    summary["gate"] = gate
    summary["timing_seconds"] = {"open_data": data["seconds"], "simulation": round(sim_seconds, 1),
                                 "total": round(time.perf_counter() - t0, 1)}
    summary["environment"] = environment()
    summary["code_sha256"] = code_hashes()
    summary["finished"] = now()
    cp.write_json(out / "dev_summary.json", summary)
    sel_sha = cp.write_json(ctx.selection, selection)
    gate_sha = cp.write_json(ctx.gate, gate)
    print(json.dumps({"C_star": c_star, "fp_star": fp_star, "R_own_fp": fp_r,
                      "dev_yield_best": selection["dev_yield_at_best_fp"],
                      "dev_R_minus_Cstar": {k: dev_contrast[k] for k in ("sum_x", "sum_y", "relative_gain",
                                                                         "relative_gain_ci")},
                      "gate": {"a": rel_a, "b": frac, "pass": gate["pass"]}, "selection_sha256": sel_sha,
                      "gate_sha256": gate_sha, "out": str(out)}, indent=1))
    return summary


# ============================================================================ stage: feedback_dev
def world_keep(part: dict, tissue: str, sidm: str) -> tuple[set, set]:
    HD, E = set(part[tissue]["HD"]), set(part[tissue]["E"])
    return HD | {sidm}, E


def stage_feedback_dev(ctx: Ctx) -> dict | None:
    gate = json.loads(ctx.gate.read_text(encoding="utf-8"))
    if ctx.fit.exists():
        raise SystemExit(f"REFUSED: {ctx.fit} exists")
    if not gate["pass"]:
        cp.write_json(ctx.fit, {"status": cp.STATUS, "written_at": now(), "run": False,
                                "reason": "feedback gate failed (feedback_gate.json)"})
        print("gate failed: diagnostic not run")
        return None
    t0 = time.perf_counter()
    started = now()
    data = open_data(ctx, "design feedback_dev stage: HD development campaigns only; TransferWorld fits without "
                          "any E line; fit F0/Fm/Ff and lambda (plan.json)")
    out = ctx.results_dir("feedback_dev")
    camps, rows, worlds = [], {}, {}
    t_w = time.perf_counter()
    for tg, truth in hd_targets(data, ctx.partition):
        keep, E = world_keep(ctx.partition, tg.tissue, tg.sidm)
        world, present = fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], keep, tg.sidm, E)
        if set(present) & E:
            raise AssertionError("E line in an HD world")
        sig = fb.Signal(world)
        key = (tg.tissue, tg.sidm, tg.role)
        rows[key] = fb.collect(tg, truth, sig)
        camps.append((tg, truth, sig))
        worlds[key] = {"library_lines": len(present), "s_line": world.s_line, "s_drug": world.s_drug,
                       "s_noise": world.s_noise}
    world_seconds = time.perf_counter() - t_w
    keys = cp.sort_keys({(k[0], k[1]) for k in rows})
    t_f = time.perf_counter()
    fit = fb.fit_models(rows, keys, resamples=cp.RESAMPLES if ctx.dry is None else 500)
    fit_seconds = time.perf_counter() - t_f
    evals, logs = [], []
    for tg, truth, sig in camps:
        ev, lg = fb.evaluate_campaign(tg, truth, sig, fit)
        evals.append(ev)
        logs += [add_events(r, data["event_of"]) for r in lg.values()]
    summary_is = feedback_summary(evals, keys, fit)
    files = {"campaigns": write_jsonl_gz(out / "feedback_campaigns_hd.jsonl.gz", logs),
             "evaluations": write_jsonl_gz(out / "feedback_eval_hd.jsonl.gz", evals)}
    fit_out = {"status": cp.STATUS, "written_at": now(), "run": True, "fitted_on": "HD development campaigns only",
               "gate_sha256": cp.sha256_file(ctx.gate), **{k: v for k, v in fit.items()},
               "worlds": {"|".join(k): v for k, v in worlds.items()}, "results_dir": str(out)}
    fit_sha = cp.write_json(ctx.fit, fit_out)
    cp.write_json(out / "feedback_dev_summary.json", {
        "status": cp.STATUS, "started": started, "finished": now(), "ticket": data["ticket"],
        "fit": fit_out, "in_sample_hd_evaluation": summary_is, "files": files,
        "timing_seconds": {"open_data": data["seconds"], "worlds_and_round1": round(world_seconds, 1),
                           "fit_with_bootstrap": round(fit_seconds, 1), "total": round(time.perf_counter() - t0, 1)},
        "environment": environment(), "code_sha256": code_hashes()})
    print(json.dumps({"F0": fit["F0"]["beta"], "Fm": fit["Fm"]["beta"], "Ff": fit["Ff"]["beta"],
                      "c_f_ci": fit["c_f_bootstrap"]["ci"], "c_f_zeroed": fit["Ff_used"]["c_f_zeroed"],
                      "lambda": fit["lambda"], "fit_sha256": fit_sha}, default=lambda o: np.asarray(o).tolist(),
                     indent=1))
    return fit_out


def feedback_summary(evals: list[dict], keys: list, fit: dict, boot: bool = True) -> dict:
    """Line-level summaries of the diagnostic endpoints; contrasts on the registered line bootstrap."""
    by = defaultdict(list)
    for e in evals:
        by[(e["tissue"], e["line"])].append(e)
    keys = [k for k in keys if by[k]]

    def line_auc(k, arm):
        v = [e["auc"][arm] for e in by[k] if e["auc"][arm] is not None]
        return float(np.mean(v)) if v else None

    out = {"lines": len(keys), "campaigns": len(evals), "auc": {}, "probability": {}, "p3": {}, "contrasts": {}}
    for arm in fb.ALL_RANKINGS:
        vals = [line_auc(k, arm) for k in keys]
        vals = [v for v in vals if v is not None]
        out["auc"][arm] = {"mean_over_lines": float(np.mean(vals)) if vals else None, "lines_defined": len(vals),
                           "campaigns_undefined": sum(1 for e in evals if e["auc"][arm] is None)}
    for arm in fb.PROB_RANKINGS:
        ps = [e["probability"][arm] for e in evals if e["probability"][arm] is not None]
        line_ll = [float(np.mean([e["probability"][arm]["log_loss"] for e in by[k] if e["probability"][arm]]))
                   for k in keys]
        pooled_pred = sum(e["probability"][arm]["mean_pred"] * e["n_eligible"] for e in evals if e["probability"][arm])
        pooled_obs = sum(e["probability"][arm]["observed_rate"] * e["n_eligible"] for e in evals
                         if e["probability"][arm])
        n_el = sum(e["n_eligible"] for e in evals if e["probability"][arm])
        out["probability"][arm] = {"mean_log_loss_over_lines": float(np.mean(line_ll)),
                                   "mean_brier_over_campaigns": float(np.mean([p["brier"] for p in ps])),
                                   "calibration_in_the_large_pooled": (pooled_pred - pooled_obs) / n_el if n_el else None,
                                   "mean_pred_pooled": pooled_pred / n_el if n_el else None,
                                   "observed_rate_pooled": pooled_obs / n_el if n_el else None}
    p3_lines = {arm: np.array([np.mean([e["p3"][arm]["confirmed"] for e in by[k]]) for k in keys])
                for arm in fb.ALL_RANKINGS}
    for arm in fb.ALL_RANKINGS:
        out["p3"][arm] = {f: float(sum(np.mean([e["p3"][arm][f] for e in by[k]]) for k in keys))
                          for f in ("confirmed", "n_screens", "n_screen_hits", "n_verifications", "round2_screens",
                                    "round2_screen_hits", "missed_unscreened", "missed_screened_not_verified")}
    out["identical_round1_all_campaigns"] = all(e["identical_round1"] for e in evals)
    out["F0_purchases_equal_R"] = sum(1 for e in evals if e["F0_equals_R_purchases"])
    if boot and len(keys) >= 2:
        idx = cp.boot_indices(keys)
        for a, b in (("Ff", "Fm"), ("Ff", "F0"), ("Fm", "F0"), ("U_lambda", "F0"), ("U_screen_post", "F0"),
                     ("U_lambda", "U_V0"), ("Ff", "U_lambda"), ("Ff", "U_screen_post")):
            av = [line_auc(k, a) for k in keys]
            bv = [line_auc(k, b) for k in keys]
            ok = [j for j in range(len(keys)) if av[j] is not None and bv[j] is not None]
            sub_keys = [keys[j] for j in ok]
            if len(sub_keys) >= 2:
                c = cp.boot_contrast(np.array([av[j] for j in ok]), np.array([bv[j] for j in ok]), sub_keys,
                                     idx if len(ok) == len(keys) else None)
                out["contrasts"][f"auc_{a}_minus_{b}"] = {k: c[k] for k in ("lines", "mean_x", "mean_y", "mean_diff",
                                                                            "mean_diff_ci", "better", "worse", "tied")}
            c = cp.boot_contrast(p3_lines[a], p3_lines[b], keys, idx)
            out["contrasts"][f"p3_confirmed_{a}_minus_{b}"] = {k: c[k] for k in (
                "sum_x", "sum_y", "mean_diff", "mean_diff_ci", "relative_gain", "relative_gain_ci")}
        for a, b in (("Fm", "F0"), ("Ff", "Fm"), ("F0", "R")):
            xa = np.array([np.mean([e["probability"][a]["log_loss"] for e in by[k] if e["probability"][a]])
                           for k in keys])
            xb = np.array([np.mean([e["probability"][b]["log_loss"] for e in by[k] if e["probability"][b]])
                           for k in keys])
            c = cp.boot_contrast(xa, xb, keys, idx)
            out["contrasts"][f"log_loss_{a}_minus_{b}"] = {k: c[k] for k in ("mean_x", "mean_y", "mean_diff",
                                                                             "mean_diff_ci")}
    return out


# ============================================================================ stage: addendum
def stage_addendum(ctx: Ctx) -> dict:
    if ctx.addendum.exists():
        raise SystemExit(f"REFUSED: {ctx.addendum} exists")
    rec = {"written_at": now(), "owner": "design",
           "purpose": "hash the development outputs before any E outcome is used (contract v2)",
           "selection_sha256": cp.sha256_file(ctx.selection), "feedback_gate_sha256": cp.sha256_file(ctx.gate),
           "feedback_fit_sha256": cp.sha256_file(ctx.fit) if ctx.fit.exists() else None,
           "selection": {k: json.loads(ctx.selection.read_text(encoding="utf-8"))[k] for k in
                         ("C_star", "fp_star", "R_own_fp", "own_fp")},
           "code_sha256": code_hashes(),
           "e_outcomes_used_before": False}
    cp.write_json(ctx.addendum, rec)
    print(json.dumps(rec["selection"]))
    return rec


def check_addendum(ctx: Ctx) -> dict:
    if not ctx.addendum.exists():
        raise SystemExit("REFUSED: plan_addendum_1.json (selection hash) must exist before E outcomes are used")
    add = json.loads(ctx.addendum.read_text(encoding="utf-8"))
    if cp.sha256_file(ctx.selection) != add["selection_sha256"] or cp.sha256_file(ctx.gate) != add["feedback_gate_sha256"]:
        raise SystemExit("REFUSED: selection / gate file differs from the addendum hash")
    if add["feedback_fit_sha256"] is not None and cp.sha256_file(ctx.fit) != add["feedback_fit_sha256"]:
        raise SystemExit("REFUSED: feedback fit differs from the addendum hash")
    return add


# ============================================================================ stage: eval
def stage_eval(ctx: Ctx) -> dict:
    check_addendum(ctx)
    sel = json.loads(ctx.selection.read_text(encoding="utf-8"))
    c_star, fp_star, fp_r, own = sel["C_star"], int(sel["fp_star"]), int(sel["R_own_fp"]), sel["own_fp"]
    t0 = time.perf_counter()
    started = now()
    data = open_data(ctx, f"design eval stage: E targets (history = HD lines), primary R - {c_star} at fp {fp_star} "
                          "and registered descriptive secondaries (selection.json hashed in plan_addendum_1.json)")
    out = ctx.results_dir("eval")
    recs = defaultdict(list)
    metrics, targets = [], {}
    for tg, truth in e_targets(data, ctx.partition):
        targets[(tg.tissue, tg.sidm, tg.role)] = tg
        for arm in cp.ARMS:
            recs[("primary", arm)].append(add_events(cp.run_p2(tg, truth, arm, fp_star), data["event_of"]))
            recs[("wells", arm)].append(add_events(cp.run_p2(tg, truth, arm, fp_star, unit="wells"),
                                                   data["event_of"]))
            recs[("p3", arm)].append(add_events(cp.run_p3(tg, truth, arm), data["event_of"]))
            if arm in own:
                recs[("own_fp", arm)].append(add_events(cp.run_p2(tg, truth, arm, int(own[arm])), data["event_of"]))
        # pipeline diagnostic (contract: p_sv / (c_s + p_s c_v) reported, not an optimal policy, not a comparator)
        q = tg.q
        tg.scores["pipeline_index|measurement"] = (q["p_sv"] / (1.0 + q["p_s"]), q["p_v_s"])
        tg.scores["pipeline_index|wells"] = (q["p_sv"] / (tg.cost_s + q["p_s"] * tg.cost_v), q["p_v_s"] / tg.cost_v)
        recs[("pipeline", "measurement")].append(add_events(cp.run_p2(tg, truth, "pipeline_index|measurement",
                                                                      fp_star), data["event_of"]))
        recs[("pipeline", "wells")].append(add_events(cp.run_p2(tg, truth, "pipeline_index|wells", fp_star,
                                                                unit="wells"), data["event_of"]))
        metrics.append(cp.menu_metrics(tg, truth))
    t_loo = time.perf_counter()
    for tg, truth in loo_targets(data):
        for arm in cp.ARMS:
            recs[("loo125", arm)].append(add_events(cp.run_p2(tg, truth, arm, fp_star), data["event_of"]))
    loo_seconds = time.perf_counter() - t_loo
    lv, tab, _ = tables({f"{v}|{a}": r for (v, a), r in recs.items() if v != "loo125"})
    keys = cp.sort_keys(lv[f"primary|R"].keys())
    lv_loo, tab_loo, keys_loo = tables({f"loo125|{a}": recs[("loo125", a)] for a in cp.ARMS})
    lv.update(lv_loo)
    tab.update(tab_loo)
    idx = cp.boot_indices(keys)

    def con(xname, yname, k=keys, ii=idx):
        return cp.boot_contrast(confirmed(lv[xname], k), confirmed(lv[yname], k), k, ii)

    primary = con(f"primary|R", f"primary|{c_star}")
    verdict = cp.decision(primary)
    own_fp_contrast = con(f"own_fp|R", f"own_fp|{c_star}")
    same_sign = np.sign(own_fp_contrast["relative_gain"] or 0) == np.sign(primary["relative_gain"] or 0)
    qual = ["for this history library and selected comparator"]
    if verdict["verdict"] in ("EXPLORATORY_HARM", "EXPLORATORY_WORTHWHILE_EXCLUDED") and not same_sign:
        qual.append("at the C*-optimal split (the own-fp secondary differs in sign)")
    verdict["qualification"] = qual
    secondary = {"own_fp_R_vs_Cstar (H2)": dict(own_fp_contrast, R_fp=fp_r, Cstar_fp=int(own[c_star]))}
    for a in cp.SIMPLE:
        if a != c_star:
            secondary[f"R_minus_{a}"] = con("primary|R", f"primary|{a}")
    secondary["S_both_minus_S"] = con("primary|S_both", "primary|S")
    secondary["R_minus_S"] = con("primary|R", "primary|S")
    secondary["P3_R_minus_Cstar"] = con("p3|R", f"p3|{c_star}")
    secondary["P3_R_minus_S_both"] = con("p3|R", "p3|S_both")
    secondary["wells_R_minus_Cstar"] = con("wells|R", f"wells|{c_star}")
    secondary["loo125_R_minus_Cstar"] = cp.boot_contrast(confirmed(lv[f"loo125|R"], keys_loo),
                                                         confirmed(lv[f"loo125|{c_star}"], keys_loo), keys_loo)
    menu_size = {(r["tissue"], r["line"]): r["n_menu"] for r in recs[("primary", "R")]}
    big = [k for k in keys if menu_size[k] >= 10]
    secondary["menu_ge_10_R_minus_Cstar"] = dict(con("primary|R", f"primary|{c_star}", big, None),
                                                 excluded_lines=[k for k in keys if menu_size[k] < 10])
    mats_r = cp.pair_matrices(recs[("primary", "R")], targets, keys)
    mats_c = cp.pair_matrices(recs[("primary", c_star)], targets, keys)
    secondary["two_way_line_x_pair_primary"] = cp.two_way(mats_r, mats_c, keys)
    # SV and VS separately (diagnostic only)
    by_role = {}
    for role in cp.ROLES:
        xr = np.array([lv["primary|R"][k]["by_role_confirmed"][role] for k in keys], float)
        yr = np.array([lv[f"primary|{c_star}"][k]["by_role_confirmed"][role] for k in keys], float)
        by_role[role] = cp.boot_contrast(xr, yr, keys, idx)
    secondary["role_diagnostic_R_minus_Cstar"] = by_role
    secondary["pipeline_diagnostic_not_a_comparator"] = {
        "index": "screen p_sv / (c_s + p_s x c_v); verify p_v|s / c_v (c = 1 under the measurement cap)",
        "R_minus_pipeline_measurement": con("primary|R", "pipeline|measurement"),
        "R_minus_pipeline_wells": con("wells|R", "pipeline|wells")}
    # ordering and calibration
    ms = menu_summary(metrics, keys)
    cr = concordance_by_line(metrics, keys, "R")
    cc = concordance_by_line(metrics, keys, c_star)
    both = [k for k in keys if k in cr and k in cc]
    ordering = {"concordance": ms["concordance"], "R_minus_Cstar_concordance": {
        k: v for k, v in cp.boot_contrast(np.array([cr[k] for k in both]), np.array([cc[k] for k in both]), both,
                                          idx if len(both) == len(keys) else None).items()
        if k in ("lines", "mean_x", "mean_y", "mean_diff", "mean_diff_ci", "better", "worse", "tied")}}
    calib = {"probability": ms["probability"]}
    for f in ("brier", "log_loss"):
        c = cp.boot_contrast(prob_by_line(metrics, keys, "R", f), prob_by_line(metrics, keys, "C_prod", f), keys, idx)
        calib[f"R_minus_C_prod_{f}"] = {k: c[k] for k in ("mean_x", "mean_y", "mean_diff", "mean_diff_ci")}
    qc = menu_qc(data, keys)
    files = {}
    for v in ("primary", "own_fp", "p3", "wells", "loo125", "pipeline"):
        rr = [r for (vv, a), lst in sorted(recs.items()) if vv == v for r in lst]
        files[v] = write_jsonl_gz(out / f"campaigns_{v}.jsonl.gz", rr)
    files["menu_metrics"] = write_jsonl_gz(out / "menu_metrics.jsonl.gz", metrics)
    summary = {"status": cp.STATUS, "stage": "eval (E targets)", "started": started, "ticket": data["ticket"],
               "selection": {"C_star": c_star, "fp_star": fp_star, "R_own_fp": fp_r, "own_fp": own,
                             "selection_sha256": cp.sha256_file(ctx.selection)},
               "lines": len(keys), "primary": {"contrast": "R - C* on E lines under P2 (measurement cap, 2 rounds, fp*)",
                                               "result": primary, "verdict": verdict},
               "secondary_descriptive": secondary, "tables": tab, "ordering": ordering, "calibration": calib,
               "menu_qc_exclusions": qc,
               "n1_zero_campaigns": {name: sum(1 for r in lst if r.get("n1_zero")) for name, lst in
                                     {f"{v}|{a}": l for (v, a), l in recs.items()}.items()},
               "per_line_confirmed": {name: {"|".join(k): v["confirmed"] for k, v in vals.items()}
                                      for name, vals in lv.items()},
               "files": files,
               "timing_seconds": {"open_data": data["seconds"], "loo125": round(loo_seconds, 1),
                                  "total": round(time.perf_counter() - t0, 1)},
               "environment": environment(), "code_sha256": code_hashes(), "finished": now()}
    cp.write_json(out / "eval_summary.json", summary)
    print(json.dumps({"primary": {k: primary[k] for k in ("sum_x", "sum_y", "mean_diff", "mean_diff_ci",
                                                          "relative_gain", "relative_gain_ci")},
                      "verdict": verdict, "out": str(out)}, indent=1))
    return summary


def menu_qc(data: dict, keys: list) -> dict:
    """M1: per line, S x V pairs with both orientations designed (pre-QC) that are not in the QC menu."""
    out = {}
    orient = data["design"]["orient"]
    designed_keys = defaultdict(set)
    for (t, sidm, a, b) in orient:
        designed_keys[(t, sidm)].add((a, b))
    for t, T in data["tissues"].items():
        S, V = data["candidates"][t]["S"], data["candidates"][t]["V"]
        for li, sidm in enumerate(T.lines):
            have = designed_keys[(t, sidm)]
            designed = {(s, v) for s in S for v in V if (s, v) in have and (v, s) in have}
            menu = {tuple(T.pairs[i]) for i in np.flatnonzero(T.c == li)}
            out[f"{t}|{sidm}"] = {"designed_both_orientations": len(designed), "menu": len(menu),
                                  "excluded_by_qc": len(designed - menu), "menu_not_designed": len(menu - designed),
                                  "evaluation_line": (t, sidm) in set(keys)}
    vals = list(out.values())
    return {"per_line": out, "total_designed": sum(v["designed_both_orientations"] for v in vals),
            "total_menu": sum(v["menu"] for v in vals), "total_excluded": sum(v["excluded_by_qc"] for v in vals)}


# ============================================================================ stage: feedback_eval
def synthetic_events(data: dict, repeat: set) -> dict:
    """Dry run only: two pseudo seeding events per screen orientation (label + noise, recomputed calls)."""
    out = {}
    for name, p in data["panels"].items():
        lib = p.library
        rng = np.random.default_rng([cp.SEED, 99, len(name)])
        n = len(lib)
        arr = {k: np.full(n, np.nan) for k in ("y1", "h1", "y2", "h2")}
        rows = np.flatnonzero(np.isin(lib.c, [lib.lines.index(s) for s in repeat if s in lib.lines]))
        for k in ("1", "2"):
            y = lib.y[rows] + rng.normal(0, 5.0, rows.size)
            arr["y" + k][rows] = y
            arr["h" + k][rows] = (y >= 20.0).astype(float)
        out[name] = {"chrono": arr}
    return out


def stage_feedback_eval(ctx: Ctx) -> dict | None:
    check_addendum(ctx)
    fit_json = json.loads(ctx.fit.read_text(encoding="utf-8"))
    if not fit_json.get("run"):
        print("feedback diagnostic not run (gate failed)")
        return None
    fit = fb.fit_from_json(fit_json)
    t0 = time.perf_counter()
    started = now()
    data = open_data(ctx, "design feedback_eval stage: E role-swapped campaigns (worlds without other E lines) and "
                          "same-condition repeat lines (seeding-event labels), coefficients from feedback_fit.json")
    out = ctx.results_dir("feedback_eval")
    part = ctx.partition
    evals, logs = [], []
    for tg, truth in e_targets(data, part):
        keep, E = world_keep(part, tg.tissue, tg.sidm)
        world, present = fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], keep, tg.sidm, E)
        if (set(present) & E) - {tg.sidm}:
            raise AssertionError("other E line in an E world")
        ev, lg = fb.evaluate_campaign(tg, truth, fb.Signal(world), fit)
        evals.append(ev)
        logs += [add_events(r, data["event_of"]) for r in lg.values()]
    keys_e = cp.sort_keys({(e["tissue"], e["line"]) for e in evals})
    swap = feedback_summary(evals, keys_e, fit)
    c = swap["contrasts"].get("auc_Ff_minus_Fm")
    zeroed = bool(fit["Ff_used"]["c_f_zeroed"])
    positive = bool(c is not None and c["mean_diff_ci"][0] > 0)
    decision = {"rule": "EXPLORATORY_RELATIVE_FEEDBACK_VALUE iff c_f != 0 and the E line-bootstrap 95% interval of "
                        "(AUC Ff - AUC Fm) excludes 0 on the positive side",
                "c_f_zeroed": zeroed, "auc_Ff_minus_Fm": c,
                "verdict": "EXPLORATORY_RELATIVE_FEEDBACK_VALUE" if (not zeroed and positive)
                else "EXPLORATORY_NO_RELATIVE_FEEDBACK_VALUE"}
    # same-condition repeatability (development-grade)
    t_sc = time.perf_counter()
    repeat = {t: set(part[t].get("repeat_lines_E", [])) | set(part[t].get("repeat_lines_HD", [])) for t in part}
    all_repeat = set().union(*repeat.values())
    if ctx.dry is None:
        from research.astra.reproducible_allocation_20261003.repeats import model_id
        from research.astra.reproducible_allocation_20261003.repeats.provenance import load_plate_hierarchy
        plates = load_plate_hierarchy()
        events_df = model_id.event_table(data["ticket"], plates, ctx.source)
        events = model_id.event_arrays(data["panels"], data["candidates"], events_df, all_repeat)
        src = "repeats/receipts/plate_hierarchy.csv seeding events; model_id.event_table / event_arrays, chrono"
    else:
        events = synthetic_events(data, all_repeat)
        src = "dry run: synthetic events"
    sc_evals, sc_logs = [], []
    for t in sorted(data["tissues"], key=lambda x: cp.TISSUES.index(x) if x in cp.TISSUES else 99):
        T = data["tissues"][t]
        HD, E = set(part[t]["HD"]), set(part[t]["E"])
        for sidm in sorted(repeat[t]):
            is_e = sidm in E
            allowed = HD if is_e else HD - {sidm}
            H = cp.restrict(T, allowed)
            for role in cp.ROLES:
                tg_full = cp.make_target(T, H, sidm, role, allowed_history=allowed, forbidden=E | {sidm})
                ev_arr = events[f"{t}_{role}"]["chrono"]
                rows = tg_full.rows
                y1, h1, y2, h2 = (ev_arr[k][rows] for k in ("y1", "h1", "y2", "h2"))
                elig = np.flatnonzero(np.isfinite(y1) & np.isfinite(y2) & np.isfinite(h1) & np.isfinite(h2))
                if elig.size < 10:
                    sc_evals.append({"tissue": t, "line": sidm, "role": role, "skipped": f"{elig.size} eligible"})
                    continue
                tg = cp.subset_target(tg_full, elig)
                truth = {"y_s": y1[elig], "h_s": h1[elig] > 0.5, "y_v": y2[elig], "h_v": h2[elig] > 0.5}
                keep, _ = world_keep(part, t, sidm)
                world, present = fb.fit_world(data["panels"][f"{t}_{role}"], keep, sidm, E)
                ev, lg = fb.evaluate_campaign(tg, truth, fb.Signal(world, positions=elig), fit)
                ev["set"] = "E" if is_e else "HD"
                sc_evals.append(ev)
                sc_logs += list(lg.values())
    ok = [e for e in sc_evals if "skipped" not in e]
    sc = {"source": src, "grade": "development-grade (14 repeat lines; coefficients transported from the "
                                  "role-swapped HD fit)", "skipped": [e for e in sc_evals if "skipped" in e]}
    for name, subset in (("all", ok), ("HD", [e for e in ok if e["set"] == "HD"]),
                         ("E", [e for e in ok if e["set"] == "E"])):
        ks = cp.sort_keys({(e["tissue"], e["line"]) for e in subset})
        sc[name] = feedback_summary(subset, ks, fit, boot=len(ks) >= 3) if ks else None
    files = {"campaigns_role_swapped": write_jsonl_gz(out / "feedback_campaigns_e.jsonl.gz", logs),
             "evaluations_role_swapped": write_jsonl_gz(out / "feedback_eval_e.jsonl.gz", evals),
             "campaigns_same_condition": write_jsonl_gz(out / "feedback_campaigns_same_condition.jsonl.gz", sc_logs),
             "evaluations_same_condition": write_jsonl_gz(out / "feedback_eval_same_condition.jsonl.gz", sc_evals)}
    summary = {"status": cp.STATUS, "started": started, "finished": now(), "ticket": data["ticket"],
               "fit_sha256": cp.sha256_file(ctx.fit), "role_swapped_E": swap, "decision": decision,
               "same_condition": sc, "files": files,
               "timing_seconds": {"open_data": data["seconds"], "same_condition": round(time.perf_counter() - t_sc, 1),
                                  "total": round(time.perf_counter() - t0, 1)},
               "environment": environment(), "code_sha256": code_hashes()}
    cp.write_json(out / "feedback_eval_summary.json", summary)
    print(json.dumps({"decision": decision["verdict"], "auc": swap["auc"], "out": str(out)}, indent=1, default=str))
    return summary


# ============================================================================ entry point
def make_ctx(dry: Path | None) -> Ctx:
    if dry is None:
        from ..common import JAAKS, partition
        if not (STUDY / "protocol/freeze.json").exists():
            raise SystemExit("REFUSED: contract not frozen")
        if not (HERE / "plan.json").exists():
            raise SystemExit("REFUSED: write design/plan.json first")
        return Ctx(None, HERE, JAAKS, partition())
    from research.astra.feedback_validation_20261003 import jaaks
    dry.mkdir(parents=True, exist_ok=True)
    src = dry / "synthetic_release.csv"
    if not src.exists():
        jaaks.synthetic_release(src, lines=10, drugs=12)
    return Ctx(dry, dry, src, None)


STAGES = {"dev": stage_dev, "feedback_dev": stage_feedback_dev, "addendum": stage_addendum, "eval": stage_eval,
          "feedback_eval": stage_feedback_eval}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stage", choices=sorted(STAGES) + ["all_dry"])
    parser.add_argument("--dry", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.stage == "all_dry":
        if args.dry is None:
            raise SystemExit("all_dry needs --dry DIR")
        ctx = make_ctx(args.dry)
        for name in ("dev", "feedback_dev", "addendum", "eval", "feedback_eval"):
            STAGES[name](ctx)
        return 0
    ctx = make_ctx(args.dry)
    STAGES[args.stage](ctx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
