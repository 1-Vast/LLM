"""Regression tests for saved-log accounting and the missing primary decision gate."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "pi_audit_statistics", ROOT / "research/routes/functional_prediction/procedure_inheritance_20261020_audit1/audit_statistics.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_task_cpu_includes_first_batch_and_excludes_anchors():
    rows = [{"role": "task", "arm": "plan", "budget_arm": 3, "batch": batch,
             "cpu_s": 10.0 if batch == 1 else 1.0} for batch in range(1, 5) for _ in range(4)]
    rows += [{"role": "anchor", "arm": "plan", "budget_arm": 3, "cpu_s": 1000.0},
             {"role": "task", "arm": "plan", "budget_arm": 4, "cpu_s": 1000.0}]
    assert AUDIT.task_cpu(rows, "plan", 3) == {"n_tasks": 16, "cpu_s": 52.0}


def test_repeated_arms_and_budgets_do_not_create_independent_novel_backgrounds():
    rows = [("novel_1", {"role": "task", "arm": arm, "regime": 5, "bg": bg,
                          "budget_arm": budget, "exit_unknown": False})
            for bg in (20, 21) for arm in ("f1_kg1", "f1_kg2", "f1_plan", "f1_distill") for budget in (3, 4)]
    result = AUDIT.exits_for(rows)
    assert result["novel_all_four_arms"] == {"logged_campaigns": 16, "unique_backgrounds": 2, "unknown_exits": 0}
    assert result["novel_plan_only"]["logged_campaigns"] == 4
    assert result["novel_plan_only"]["unique_backgrounds"] == 2


def decision_fixture(reference_at_four):
    means, anchors = {}, {}
    for i in range(8):
        row = {}
        for budget in (3, 4):
            row.update({("f1_plan", budget): 0.70, ("f1_kg1", budget): 0.67,
                        ("f1_kg2", budget): 0.68, ("f1_distill", budget): 0.68,
                        ("f1_plan_nobranch", budget): 0.68, ("f1_plan_xplant", budget): 0.68})
        row[("f1_kg2", 4)] = reference_at_four
        means[str(i)] = row
        anchors[str(i)] = {(arm, checkpoint): 0.70 for arm in ("f1_plan", "f1_kg1") for checkpoint in range(4)}
    return means, anchors


def test_failed_primary_saving_cannot_advance_despite_uniqueness_and_ablations():
    means, anchors = decision_fixture(0.73)
    original = AUDIT.original_decider()(means, anchors)
    assert original["label"] == "ADVANCE_TO_POWERED_INDEPENDENT_DESIGN"
    assert original["primary_unit_saving_holds"] is False
    corrected = AUDIT.decide_corrected(means, anchors)
    assert corrected["label"] == "INCONCLUSIVE_DEVELOPMENT"


def test_advance_is_retained_when_primary_and_other_gates_pass():
    means, anchors = decision_fixture(0.70)
    corrected = AUDIT.decide_corrected(means, anchors)
    assert corrected["primary_unit_saving_holds"] is True
    assert corrected["label"] == "ADVANCE_TO_POWERED_INDEPENDENT_DESIGN"


def test_current_saved_label_is_preserved_and_cost_correction_is_traceable():
    result = AUDIT.audit()
    assert result["decision_review"]["current_label_unchanged"] is True
    assert result["original_decision"]["label"] == "CLOSE_NO_PRACTICAL_BENEFIT_OVER_FRESH_ONE_STEP_PLANNING"
    assert result["costs_original_vs_corrected"]["f1_kg2@3"]["corrected_full_16_tasks"]["total_cpu_s"] == pytest.approx(2.16015625)
    assert result["costs_original_vs_corrected"]["f1_plan@3"]["corrected_full_16_tasks"]["total_cpu_s"] == pytest.approx(1.873046875)
    assert result["exit_denominators"]["novel_all_four_arms"]["unique_backgrounds"] == 4
    assert result["family_and_seed_block_contrasts"]["all"]["n_seed_blocks"] == 2
