"""Produce the requested dated record from verified Round-2 artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from research.identifiability_audit import round2 as R


def number(value):
    return "NA" if value is None else f"{value:.4f}"


def interval(metric):
    if metric["mean"] is None:
        return "NA"
    return f"{metric['mean']:+.4f} [{metric['ci95'][0]:+.4f}, {metric['ci95'][1]:+.4f}]"


def render(out: Path):
    folder = out / "interventions"
    summary = json.loads((folder / "task_summary.json").read_text())
    state = json.loads((out / "state/state_summary.json").read_text())
    cached = json.loads((out / "cached_world/summary.json").read_text())
    controls = json.loads((out / "physical_controls.json").read_text())
    risks = json.loads((out / "matched_risk_summary.json").read_text())
    validation = json.loads((out / "result_validation.json").read_text())
    if not validation["passed"]:
        raise RuntimeError("result_validation_failed")
    lines = ["", "---", "", "# Round 2: forecast to action to terminal-decision audit (2026-09-30)", "",
        "## R2.1 Outcome and scope", "",
        "The audit completed eight predeclared cells on all five folds of SciPlex3 B and L1000 LT. "
        "The reference baseline reproduced every historical `belief` action sequence. No model was trained and "
        "production `src` was not changed. Historical oracle arms remain diagnostic ceilings. "
        "WorldV2 forecast swap and its policy interaction were not executed: fitted transitions were not serialized, "
        "and recreating them would fit a model. ReferenceWorld is reported under its own name.", "",
        "Real reference forecast content improves SciPlex3 reading quality and choices relative to permutation, "
        "but does not establish terminal benefit over fixed. Paired baseline-minus-fixed utility is "
        "-0.0054 [-0.0436,+0.0386] on SciPlex3 and +0.0137 [-0.0096,+0.0408] on L1000. "
        "Both chemical-cluster CIs include zero. Risk-select lowers unconditional errors and costs while "
        "also reducing correct decisions and coverage; this is not general decision improvement.", "",
        "All datasets, outcomes and research backends have development exposure since 2026-09-26; "
        "this is a descriptive path audit, not independent generalization, biological mechanism validation or "
        "evidence of decision superiority. STATE is audited only at its registered Tahoe c39 condition.", "",
        "## R2.2 Round 1 recovery and corrections", "",
        "The missing log and six contract tests were recovered byte-for-byte from stash object `11f7e57`, "
        "without applying or dropping the stash. `recovery.json` records hashes. Both raw-source action tables "
        "were independently regenerated in a fresh directory and matched all 1,296 / 2,144 rows. "
        "The source gate passed 59 checks, including the actual 2.456 GB SciPlex3 H5AD SHA-256 and every "
        "original e_data1 output hash. `verification.json` and `round1_input_hashes.json` are the receipts.", "",
        "SciPlex3 has two recorded low-cell-count conditions: Alisertib (MLN8237), 13 rep1 cells; "
        "SRT3025 HCl, 17 rep1 cells; both at A549 / 24 h / 10,000 nM, versus a 20-cell threshold. "
        "They are known QC-failed attempts, not absent treatments or laboratory failure receipts.", "",
        "L1000's four unresolved well counts are BRD-K00627859 (23 vs 24), BRD-K02130563 (23 vs 24), "
        "BRD-K72703948 (12 vs 13), and BRD-K88742110 (23 vs 24), all MCF7 / 24 h / 10,000 nM. "
        "BRD-K81418486's 190 cached vs 191 instance rows reduce to 190 distinct well slots; its plate count "
        "still disagrees, 153 vs 154. Thus four well-count source linkages remain unresolved and a fifth "
        "plate-count linkage is also unresolved. All five affected source conditions enter conservative path bounds. "
        "The extra plate caveat was recorded before L1000 outcomes were summarized in `source_addendum_pre_l1000.json`.", "",
        "Corrections to R1: 108 and 268 are compound counts; the frozen uncertainty groups number 105 Murcko "
        "skeletons and 205 identity/scaffold components. SciPlex3's full episode-action grid has 15,336 cells "
        "(1,278 x 12), not 12,936. The R1 latent-reading bound compares oracle-may-abstain with fixed-must-act; "
        "its observed diagnostic is 0.1473, whereas 0.1790 uses fixed-may-abstain and is a different contrast. "
        "Original artifacts and original log prose remain preserved; this section supersedes those interpretations.", "",
        "## R2.3 Four-arm unified-score review", "",
        "The fixed arm here is R1's cross-fitted `fixed_star`, distinct from the registered fixed order in R2 "
        "policy swap. Rates below are chemical-unit means, with all metric cluster intervals in each "
        "`*_four_arm_summary.json`. Days now charge only executed attempts. R1 charged the whole chosen "
        "sequence even after an early elimination; this changed cost figures, not terminal utilities.", "",
        "| Task | Diagnostic arm | correct | wrong | undetermined | deferred | measurements | days | utility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for task in summary:
        arms = json.loads((folder / (task + "_four_arm_summary.json")).read_text())
        for arm, values in arms.items():
            lines.append("| " + task + " | " + arm + " | " + " | ".join(number(values[m]["mean"]) for m in
                ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility")) + " |")
    lines += ["", "The statement that abstention buys cost but not correctness is valid for the diagnostic oracle "
        "alone: it turns undetermined into deferred without changing correct or wrong. It is false as a "
        "general fixed-policy claim. Fixed abstention lowers correct-unit means by 0.0507445 (SciPlex3) "
        "and 0.0290901 (L1000), and utility by 0.0316969 / 0.0231873. The widened oracle-minus-fixed "
        "correctness gap partly reflects damage to fixed, not new model or action value. Utility "
        "`correct - 2*wrong` has no cost term; cost savings are reported separately.", "",
        "## R2.4 Frozen interventions and information", "",
        "SciPlex3 B: 1,278 episodes, 12 menu actions, 16-day budget, maximum two attempts. L1000 LT: "
        "3,648 episodes, eight actions, 12-day budget, maximum two attempts. Each fold's exact episodes, "
        "legal menu, training set, validator calibration, QC, endpoint, costs and reference parameters are "
        "in `*_freeze.json`; initial seed is 20260930. QC failures cost days and change no evidence. "
        "Time order, distinct actions and stopping on the first registered elimination remain fixed.", "",
        "Forecast swap uses one existing belief expectimax planner: none, original reference, within-task "
        "action permutation, and a constant uniform five-reading forecast. Permutation remaps forecast "
        "queries/history among the same task's actions while retaining hypothesis/context and the offered "
        "action identifier. WorldV2 is unavailable. Policy swap supplies the same immutable reference "
        "query-to-forecast function to fixed, baseline planner, discrimination selection and existing "
        "upper-risk-select. No held-out result selects a combination or threshold. Risk caps use the "
        "historically predeclared middle upper cap: 0.5294 / 0.2558. The two extra none/reference fixed "
        "cells are negative controls for forecast presence by policy interaction.", "",
        "Policies see hypotheses, structures, training-only reference tables, frozen validator parameters, "
        "design menu, budgets and purchased readings. Hidden truth and unpurchased readings stay on the "
        "scoring/execution side. The original `P.discrimination` wrapper's inaccessible magnitude field "
        "is bypassed by feeding the same forecasts directly into the existing `select_discriminating_action`; "
        "no magnitude priority or new selector is added. Forecasts enter selection, not repair or final "
        "evidence updates. Fixed deliberately ignores forecasts. Selector calls, quality probes and forecast "
        "input/output SHA-256 are distinct in `*_forecasts.jsonl.gz`.", "",
        "## R2.5 Task-level terminal results", "",
        "These point rates describe the frozen local replay. Where a selected condition has unresolved source "
        "linkage, the inferential comparison is only the utility interval shown; the raw replay point and "
        "its bootstrap interval do not resolve that source uncertainty. Same exact fixed paths have zero "
        "paired difference under every shared missing-world resolution. Other bounds are conservative outer "
        "bounds using U in [-2,+1]; no forecast fills a missing biological outcome.", "",
        "| Task | forecast / policy | correct | wrong | deferred | measurements | days | utility | replay U-fixed (95% CI) | identification U-fixed bounds |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for task, task_report in summary.items():
        for cell in task_report["cells"]:
            m = cell["metrics"]
            values = " | ".join(number(m[x]["mean"]) for x in
                                 ("correct", "wrong", "deferred", "measurements", "days", "utility"))
            bounds = f"[{m['delta_lo']['mean']:+.4f}, {m['delta_hi']['mean']:+.4f}]"
            lines.append(f"| {task} | {cell['forecast']} / {cell['policy']} | {values} | "
                         f"{interval(m['delta_utility'])} | {bounds} |")
    lines += ["", "## R2.6 Forecast quality and path changes", "",
        "NLL and multiclass Brier score the attempted reading distribution under the true hypothesis "
        "after freezing predictions; QC is a separate class. Initial all-menu quality and selected-action "
        "pre-measurement quality are separate. Structural validator folds never consumed a forecast; "
        "their placeholder quality probes are excluded from quality claims. None has no quality estimate.", "",
        "Ranking below is the explicitly defined unconditioned one-step forecast utility minus day price, "
        "not an assertion that every selector uses that ranking. Forecast-swap changes are relative to "
        "reference/baseline; policy-swap changes are relative to reference/fixed. Later actions and terminal "
        "changes, conditional and unconditional unchanged-terminal shares, all CIs and paired correct/wrong "
        "differences are in `task_summary.json` and episode path tables.", "",
        "| Task | forecast / policy | NLL all-menu | NLL selected | ranking changed | first changed | later changed | sequence changed | changed-action same-terminal / changed actions |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for task, task_report in summary.items():
        for cell in task_report["cells"]:
            m = cell["metrics"]
            values = " | ".join(number(m[x]["mean"]) for x in
                ("nll_all", "nll_selected", "ranking_changed", "first_changed", "later_changed", "sequence_changed"))
            lines.append(f"| {task} | {cell['forecast']} / {cell['policy']} | {values} | "
                         f"{number(cell['action_changed_terminal_same_conditional'])} |")
    lines += ["", "## R2.7 Dependence, interactions and abstention", ""]
    for task, task_report in summary.items():
        lines.append(f"- {task}: reference-presence x baseline-versus-fixed interaction in local utility: "
                     f"{interval(task_report['reference_presence_x_baseline_vs_fixed'])}. This compares a planner "
                     "that stops when forecasts are absent with fixed, which ignores them; it is not a "
                     "WorldV2 interaction or superiority over an acting fixed policy.")
        physical = task_report["physical_dependence"]
        lines.append(f"- {task}: {physical['distinct_treatment_plates']} distinct treatment plates; "
                     f"{physical['components_from_shared_treatment_plates']} connected dependency component(s). "
                     f"Adding the registered shared control-calibration strata gives "
                     f"{controls[task]['components_including_shared_controls']} combined component. "
                     "Physical plate/batch CI is not estimable from independent clusters. Chemical CIs "
                     "condition on this assay and do not quantify physical replication; see `physical_controls.json`.")
    lines += ["", "Chemical intervals use 2,000 paired cluster-bootstrap draws at seed 20260930 on the exact "
        "frozen skeleton/component grouping, never cells/wells/episode rows as independent draws. Cost, "
        "errors, abstentions and correctness have their own cluster intervals in JSON. Matched acted "
        "episodes and jointly decided episodes report both policies' correctness, risk and costs at "
        "the same subset coverage. The jointly decided subset is outcome-selected and descriptive; "
        "it is not a deployable pre-action abstention rule or a risk guarantee. No matching is possible "
        "when none/constant abstains everywhere. A lower unconditional error rate alone is not general "
        "decision improvement.", "",
        "## R2.8 Historical WorldV2 review, kept separate", "",
        "Cached nested-model forecasts were rescored on identical previously acquired steps, with no "
        "new model calls. These models and purchased histories differ from the intervention freeze. "
        "They do not supply a full-menu forecast bank and cannot establish a forecast-swap effect.", ""]
    for task, values in cached["tasks"].items():
        lines.append(f"- {task}: {values['rows']} matched step records; with a purchased prompt, "
                     f"WorldV2-reference NLL {interval(values['purchased_prompt_steps']['delta_nll'])}.")
    lines += ["", "## R2.9 STATE interface", "",
        "The inherited 14 served query/output pairs were independently checked: controls and labels "
        "stay fixed, embeddings match saved vectors, and six expression-perturbation seeds / three "
        "plate-label variants remain invariant. Nine new inferences repeat baseline, permutation and "
        "replacement at inference seeds 42, 77, 123: every perturbation is byte-identical to its own "
        "seed's baseline. This does not assert cross-seed equality.", "",
        "| Target rows | Existing query | Relative L2 change from 378-row baseline |",
        "|---:|---|---:|"]
    for arm in state["inherited_verified"]:
        if arm["arm"].startswith("rows_"):
            lines.append(f"| {arm['target_rows']} | {arm['arm']} | {arm['relative_l2']:.6f} |")
    lines += ["", "Row deletion was independently retried and returned `unsupported_query` before inference, "
        "with no prediction. STATE action-ranking impact is unidentified: SciPlex3 B / L1000 LT have no "
        "registered STATE context and no consuming selector. This behavior is restricted to NCI-H596, "
        "registered Adagrasib 0.05 uM, fixed control and checkpoint. It establishes no support for unmeasured "
        "chemistry, new time or new dose. Checkpoint SHA-256, query/output hashes and exact inference commands "
        "are in `state/state_summary.json`.", "",
        "## R2.10 Execution ledger, limitations and reproduction", "",
        "Executed: source/raw-hash verification; all 39,408 episode-cell replays; four-arm cost-corrected "
        "reviews; reading/selected-action quality; ranking/action/terminal attribution; paired fixed contrasts; "
        "conservative unresolved-source bounds; matched-subset risk/cost; forecast-presence interaction; "
        "separate physical-connectivity analysis; cached WorldV2 reading review; STATE inheritance verification "
        "and nine fresh inferences; contract and existing planner/selector/state tests.", "",
        "Not executed: WorldV2 forecast swap or WorldV2 x policy interaction; case-memory on this incompatible "
        "population; true-state-gain experiment; model training; external evaluation; production changes. "
        "Unidentified: physical-cluster CI, general decision improvement from abstention, STATE-to-action "
        "ranking, new-domain performance and source-comparable point effects on unresolved paths.", "",
        "All output is under `outputs/identifiability_round2_20260930/`. `artifact_ledger.json` records input, "
        "output and source hashes, environment and commands; `predeclared.json` records the original run "
        "version, and resume receipts preserve the helper corrections. Review-stage failures were an extra "
        "argument to `fixed_star` and serialization of a structural validator infinity. Completed traces "
        "were preserved; no model/selector repair or production runtime defect was identified. An initial "
        "STATE comparison treated categorical dictionary changes as cell-value changes; comparing actual "
        "values confirmed control invariance. Failed attempts remain recorded.", "",
        "Environment: `D:/anaconda/envs/maestro/python.exe`, Python 3.11.16; exact package versions in the "
        "run manifest and final ledger. Native numerical libraries were limited to one thread for the "
        "intervention run. New files use exclusive creation; to reproduce in another directory, run "
        "the source replays into that directory first, then use the same `--out` for all stages.", "",
        "```powershell",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.lineage_sciplex3 --out outputs/identifiability_round2_20260930/round1_replay/sciplex3_B",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.lineage_l1000 --out outputs/identifiability_round2_20260930/round1_replay/l1000_LT",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.unified_score --out outputs/identifiability_round2_20260930/round1_replay/unified_score",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2 verify",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2 run",
        "# --resume was used only after the documented review failures; never overwrites completed task traces.",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2 analyse",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2_cached_world",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.state_round2",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2_physical_controls",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2_validate",
        "& 'D:\\anaconda\\envs\\maestro\\python.exe' -m research.identifiability_audit.round2_report",
        "```", ""]
    lines += ["## R2.11 Conditional risk and matched coverage supplement", "",
        "`matched_risk_summary.json` adds chemical-cluster 95% intervals for wrong-among-decided risk. "
        "Zero-decision cells have undefined conditional risk. The jointly decided subset has equal coverage "
        "for both arms but is outcome-selected; its costs and correctness are descriptive, not a new abstention policy.", "",
        "| Task | policy with reference | decided coverage | wrong among decided (95% CI) |",
        "|---|---|---:|---|"]
    for task, cells in risks["tasks"].items():
        for policy in ("fixed", "baseline", "discrimination", "risk_select"):
            risk = cells["reference|" + policy]["whole_replay"]
            lines.append(f"| {task} | {policy} | {number(risk['coverage'])} | "
                         f"{number(risk['risk'])} [{number(risk['ci95'][0])}, {number(risk['ci95'][1])}] |")
    lines += ["", "On L1000, risk-select reduces unconditional errors while its conditional wrong-among-decided "
        "risk is higher than fixed. A lower error count caused by lower decision coverage is not a general "
        "decision gain. Matched acted and jointly decided correctness/risk/cost summaries are retained for each cell.", "",
        "Additional executed command: `python -m research.identifiability_audit.round2_risk`. Final scoped contract "
        "and log-layout checks: 15 passed (`delivery_tests.xml`), after the earlier 50-test planner/selector/STATE "
        "run. The complete production suite was not rerun because no production code changed.", ""]
    return "\n".join(lines)


def generate(out: Path):
    section = render(out)
    log = R.ROOT / "log/20260930/README.md"
    if "# Round 2:" in log.read_text():
        raise FileExistsError("Round 2 dated section already exists")
    with (out / "ROUND2_REPORT.md").open("x", encoding="utf-8") as f:
        f.write(section)
    with log.open("ab") as f:
        f.write(section.encode())


if __name__ == "__main__":
    generate(R.OUT)
