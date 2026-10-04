"""POST HOC addendum 2 (EXPLORATORY): matched no-feedback control for U_screen_post.

File summary
- Path: research/astra/confirmation_campaign_20261004/design/addendum_2_screen_static.py
- Purpose: U_screen_post (S0 + F: frozen TransferWorld prior mean on the screen scale plus the feedback
  posterior shift) was the strongest existing comparator of the feedback diagnostic, but its matched
  no-feedback control U_screen_static (S0 alone, same world, no purchased label) was not reported, so its
  advantage could not be attributed to feedback. This addendum computes, on exactly the campaigns and
  eligible round-2 candidate sets of the feedback_eval stage (role-swapped E: 122 campaigns;
  same-condition repeat lines: 28 campaigns), AUC, log loss where defined, and P3 confirmed yield for
  U_screen_static, U_screen_post, U_V0 and U_lambda, plus the registered line-bootstrap intervals of
  U_screen_post - U_screen_static and U_lambda - U_V0. Defined after the feedback results were seen
  (POST HOC; plan_addendum_2.json written first).
- Core points:
  - Worlds, round-1 purchases (R under P3), eligible sets, coefficients (feedback_fit.json) and the
    same-condition event construction are those of stages.stage_feedback_eval (imported, unchanged).
  - Reproduction check: AUC and P3 yield of U_screen_post / U_lambda / U_V0 must equal the stored
    feedback_eval per-campaign values exactly; mismatches are counted.
  - Log loss is undefined for these four rankings (continuous screen- or verification-scale labels, not
    probabilities); reported as null with the reason.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.design.addendum_2_screen_static`
- Depends on: design/campaign.py, feedback.py, stages.py (imported); the study's common.py.
"""
from __future__ import annotations

import gzip
import json
import time
from collections import defaultdict

import numpy as np

from . import campaign as cp
from . import feedback as fb
from . import stages as sg

LABEL = "POST HOC, EXPLORATORY (exposed data; defined after the feedback_eval results were seen)"
RANKINGS = ("U_screen_static", "U_screen_post", "U_V0", "U_lambda")
CONTRASTS = (("U_screen_post", "U_screen_static"), ("U_lambda", "U_V0"))
FEEDBACK_EVAL = sg.HERE / "results/feedback_eval_20261004_130535"
PLAN = sg.HERE / "plan_addendum_2.json"


def evaluate(tg: cp.Target, truth: dict, signal: fb.Signal, fit: dict) -> tuple[dict, dict]:
    st = fb.round1_state(tg, truth)
    d = fb.Decision2(tg, signal, st)
    preds = fb.predictions(d, tg, fit)
    preds["U_screen_static"] = d.S0.copy()
    e = d.eligible
    joint = np.asarray(truth["h_s"], bool) & np.asarray(truth["h_v"], bool)
    out = {"tissue": tg.tissue, "line": tg.sidm, "role": tg.role, "n_menu": tg.n, "M": tg.M,
           "n_eligible": int(e.sum()), "eligible_joint_hits": int(joint[e].sum()),
           "frozen_predictions_sha256": {k: cp.score_hash(preds[k]) for k in RANKINGS},
           "auc": {k: cp.auc(preds[k][e], joint[e]) for k in RANKINGS},
           "log_loss": {k: None for k in RANKINGS}, "p3": {}}
    logs = {}
    for k in RANKINGS:
        def hook(state, key=k):
            dd = fb.Decision2(tg, signal, state)
            p = fb.predictions(dd, tg, fit)
            p["U_screen_static"] = dd.S0.copy()
            return tg.order(p[key]), p[key]
        rec = cp.run_p3(tg, truth, "R", round2_order=hook, arm_label=k)
        out["p3"][k] = {f: rec[f] for f in ("confirmed", "n_screens", "n_screen_hits", "n_verifications",
                                            "round2_screens", "round2_screen_hits", "spent")}
        logs[k] = rec
    out["identical_round1"] = len({tuple(r["rounds"][0]["screens"]) for r in logs.values()}) == 1
    return out, logs


def summarise(evals: list[dict]) -> dict:
    by = defaultdict(list)
    for e in evals:
        by[(e["tissue"], e["line"])].append(e)
    keys = cp.sort_keys(by)

    def line_auc(k, arm):
        v = [e["auc"][arm] for e in by[k] if e["auc"][arm] is not None]
        return float(np.mean(v)) if v else None

    out = {"lines": len(keys), "campaigns": len(evals), "auc": {}, "log_loss": {}, "p3_confirmed": {}, "contrasts": {}}
    for arm in RANKINGS:
        vals = [v for v in (line_auc(k, arm) for k in keys) if v is not None]
        out["auc"][arm] = {"mean_over_lines": float(np.mean(vals)) if vals else None, "lines_defined": len(vals),
                           "campaigns_undefined": sum(1 for e in evals if e["auc"][arm] is None)}
        out["log_loss"][arm] = {"value": None, "reason": "not a probability (continuous label-scale prediction)"}
        out["p3_confirmed"][arm] = float(sum(np.mean([e["p3"][arm]["confirmed"] for e in by[k]]) for k in keys))
    for a, b in CONTRASTS:
        av, bv = [line_auc(k, a) for k in keys], [line_auc(k, b) for k in keys]
        ok = [j for j in range(len(keys)) if av[j] is not None and bv[j] is not None]
        sub = [keys[j] for j in ok]
        c = cp.boot_contrast(np.array([av[j] for j in ok]), np.array([bv[j] for j in ok]), sub)
        out["contrasts"][f"auc_{a}_minus_{b}"] = {k: c[k] for k in ("lines", "mean_x", "mean_y", "mean_diff",
                                                                    "mean_diff_ci", "better", "worse", "tied")}
        xa = np.array([np.mean([e["p3"][a]["confirmed"] for e in by[k]]) for k in keys])
        xb = np.array([np.mean([e["p3"][b]["confirmed"] for e in by[k]]) for k in keys])
        c = cp.boot_contrast(xa, xb, keys)
        out["contrasts"][f"p3_confirmed_{a}_minus_{b}"] = {k: c[k] for k in (
            "sum_x", "sum_y", "mean_diff", "mean_diff_ci", "relative_gain", "relative_gain_ci", "better", "worse")}
    return out


def reproduction(evals: list[dict], stored_path) -> dict:
    stored = {}
    with gzip.open(stored_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            r = json.loads(line)
            if "skipped" not in r:
                stored[(r["tissue"], r["line"], r["role"])] = r
    checked = mismatched = 0
    for e in evals:
        s = stored[(e["tissue"], e["line"], e["role"])]
        for arm in ("U_screen_post", "U_lambda", "U_V0"):
            checked += 1
            same = (e["auc"][arm] == s["auc"][arm] and e["p3"][arm]["confirmed"] == s["p3"][arm]["confirmed"]
                    and e["frozen_predictions_sha256"][arm] == s["frozen_predictions_sha256"][arm]
                    and e["n_eligible"] == s["n_eligible"])
            mismatched += int(not same)
    return {"stored": str(stored_path.relative_to(sg.ROOT)).replace("\\", "/"), "campaigns": len(evals),
            "checks": checked, "mismatched": mismatched}


def main() -> int:
    from ..common import JAAKS, exposed_ticket, partition

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    me = sg.HERE / "addendum_2_screen_static.py"
    if plan["code_sha256"][str(me.relative_to(sg.ROOT)).replace("\\", "/")] != cp.sha256_file(me):
        raise SystemExit("REFUSED: addendum code differs from plan_addendum_2.json")
    ctx = sg.Ctx(None, sg.HERE, JAAKS, partition())
    sg.check_addendum(ctx)
    fit_json = json.loads(ctx.fit.read_text(encoding="utf-8"))
    if cp.sha256_file(ctx.fit) != plan["feedback_fit_sha256"]:
        raise SystemExit("REFUSED: feedback_fit.json differs")
    fit = fb.fit_from_json(fit_json)
    t0 = time.perf_counter()
    started = sg.now()
    data = sg.open_data(ctx, "design POST HOC addendum 2 (plan_addendum_2.json): U_screen_static vs U_screen_post and "
                             "U_V0 vs U_lambda on the feedback_eval campaigns (role-swapped E, same-condition repeats)")
    out = ctx.results_dir("addendum2")
    part = ctx.partition
    evals, logs = [], []
    for tg, truth in sg.e_targets(data, part):
        keep, E = sg.world_keep(part, tg.tissue, tg.sidm)
        world, present = fb.fit_world(data["panels"][f"{tg.tissue}_{tg.role}"], keep, tg.sidm, E)
        ev, lg = evaluate(tg, truth, fb.Signal(world), fit)
        evals.append(ev)
        logs += [sg.add_events(r, data["event_of"]) for r in lg.values()]
    from research.astra.reproducible_allocation_20261003.repeats import model_id
    from research.astra.reproducible_allocation_20261003.repeats.provenance import load_plate_hierarchy
    repeat = {t: set(part[t].get("repeat_lines_E", [])) | set(part[t].get("repeat_lines_HD", [])) for t in part}
    all_repeat = set().union(*repeat.values())
    events = model_id.event_arrays(data["panels"], data["candidates"],
                                   model_id.event_table(data["ticket"], load_plate_hierarchy(), ctx.source), all_repeat)
    sc_evals, sc_logs = [], []
    for t in sorted(data["tissues"], key=lambda x: cp.TISSUES.index(x)):
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
                    raise AssertionError("feedback_eval skipped no same-condition campaign")
                tg = cp.subset_target(tg_full, elig)
                truth = {"y_s": y1[elig], "h_s": h1[elig] > 0.5, "y_v": y2[elig], "h_v": h2[elig] > 0.5}
                keep, _ = sg.world_keep(part, t, sidm)
                world, _ = fb.fit_world(data["panels"][f"{t}_{role}"], keep, sidm, E)
                ev, lg = evaluate(tg, truth, fb.Signal(world, positions=elig), fit)
                ev["set"] = "E" if is_e else "HD"
                sc_evals.append(ev)
                sc_logs += list(lg.values())
    result = {
        "label": LABEL, "plan": "design/plan_addendum_2.json", "plan_sha256": cp.sha256_file(PLAN),
        "started": started, "ticket": data["ticket"], "feedback_fit_sha256": cp.sha256_file(ctx.fit),
        "role_swapped_E": summarise(evals),
        "same_condition_all": summarise(sc_evals),
        "same_condition_HD": summarise([e for e in sc_evals if e["set"] == "HD"]),
        "same_condition_E": summarise([e for e in sc_evals if e["set"] == "E"]),
        "identical_round1_all": all(e["identical_round1"] for e in evals + sc_evals),
        "reproduction_role_swapped": reproduction(evals, FEEDBACK_EVAL / "feedback_eval_e.jsonl.gz"),
        "reproduction_same_condition": reproduction(sc_evals, FEEDBACK_EVAL / "feedback_eval_same_condition.jsonl.gz"),
        "files": {"campaigns": sg.write_jsonl_gz(out / "addendum2_campaigns.jsonl.gz", logs + sc_logs),
                  "evaluations": sg.write_jsonl_gz(out / "addendum2_evaluations.jsonl.gz",
                                                   [dict(e, target="role_swapped_E") for e in evals]
                                                   + [dict(e, target="same_condition") for e in sc_evals])},
        "seconds": round(time.perf_counter() - t0, 1), "finished": sg.now(),
        "environment": sg.environment()}
    cp.write_json(out / "addendum2_summary.json", result)
    for name in ("role_swapped_E", "same_condition_all"):
        r = result[name]
        print(name, json.dumps({"auc": r["auc"], "p3": r["p3_confirmed"], "contrasts": r["contrasts"]}, indent=1))
    print(result["reproduction_role_swapped"], result["reproduction_same_condition"], out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
