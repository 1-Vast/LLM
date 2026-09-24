"""Pin structured tool contracts, bounded routing and declaration-only analyses."""
from __future__ import annotations

import hashlib
import itertools
import json
import random
from pathlib import Path

import pytest

from agent.context import ContextPacket, TaskIntent
from agent.tool_runtime import LocalToolCatalog, ToolBudget, ToolExecutionState, ToolRouter, ToolRuntimeError
from maestro.models import EvidenceKind
from maestro.tool_analysis import ModalityRecord, evidence_bundle_optimize, multimodal_alignment
from maestro.tool_contracts import TOOL_SCHEMA_VERSION, check_schema, json_dumps, json_loads, json_value, validate_schema


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class SequenceClient:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.messages = []

    def complete_json(self, messages, **kwargs):
        self.messages.append(messages)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response, object()


def context():
    return ContextPacket(TaskIntent("analysis_planning", "Inspect.", (), (), None, None, (), (), (), False), (), (), "Inspect.")


def selection(tool_id="data_profile", **arguments):
    return {"tool_id": tool_id, "dataset_id": "dataset_1", "arguments": arguments, "rationale": "Inspect declared data."}


def write_json(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json_dumps(value), encoding="utf-8")
    return path


def custom_tool(tmp_path, *, cost=0, body=None, evidence_kind="derived_analysis", source_files=None):
    root = tmp_path / "tools"
    directory = root / "custom"
    directory.mkdir(parents=True)
    manifest = {
        "id": "custom", "name": "Custom", "description": "Test adapter.", "entrypoint": "tool.py",
        "required_parameters": ["dataset_path"], "optional_parameters": [],
        "evidence_kind": evidence_kind, "estimated_cost": cost,
    }
    if source_files is not None:
        manifest["source_files"] = source_files
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "tool.py").write_text(body or "def run(parameters): return {'schema_version': '1.0', 'payload': {'ok': True}}\n", encoding="utf-8")
    return root, directory


def test_adapters_are_registered_typed_and_source_versioned():
    descriptors = LocalToolCatalog(TOOLS).discover()
    assert {item.identifier for item in descriptors} == {
        "data_profile", "column_summary", "table_filter", "evidence_bundle_optimize", "multimodal_alignment", "virtual_cell_query",
    }
    for item in descriptors:
        assert item.parameter_schema and item.schema_version == TOOL_SCHEMA_VERSION
        if item.identifier == "virtual_cell_query":
            assert item.evidence_kind is EvidenceKind.MODEL_PREDICTION
            assert ROOT / "src/virtual_cell/interface.py" in item.source_files
        else:
            assert item.evidence_kind is EvidenceKind.DERIVED_ANALYSIS
            assert ROOT / "src/maestro/tool_analysis.py" in item.source_files
            assert len(item.entrypoint.read_text(encoding="utf-8").splitlines()) <= 12


def test_multistep_feeds_structured_payload_receipts_and_stops_on_null(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("x\n1\n3\n", encoding="utf-8")
    client = SequenceClient(selection(), selection("column_summary", column="x"), None)
    executions = ToolRouter(client, TOOLS).select_and_execute_many(context(), [path], max_steps=5, plan_version="p2")
    assert len(executions) == 2 and len(client.messages) == 3
    state = json_loads(client.messages[1][1]["content"].split("EXECUTION_STATE\n")[1])
    prior = state["previous_executions"][0]
    assert prior["payload"]["columns"] == ["x"]
    assert prior["schema_version"] == "1.0"
    assert prior["receipt"]["state"] == "committed"
    assert prior["receipt"]["input_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert prior["receipt"]["plan_version"] == "p2"
    assert state["cost_basis"] == "declared_tool_cost_not_token_billing"
    assert executions[1].payload["statistics"]["mean"] == 2
    assert json_loads(json_dumps(executions[1].to_dict()))["evidence_kind"] == "derived_analysis"


def test_repeat_with_approved_dataset_alias_does_not_execute_twice(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("x\n1\n", encoding="utf-8")
    first = selection()
    second = selection(dataset_path=path.name)
    second["dataset_id"] = "dataset_2"
    client = SequenceClient(first, second, selection("column_summary", column="x"))
    executions = ToolRouter(client, TOOLS).select_and_execute_many(context(), [path, path], max_steps=4)
    assert len(executions) == 1
    assert len(client.messages) == 2


@pytest.mark.parametrize("stop", [None, {"tool_id": None}])
def test_null_stops_without_execution(tmp_path, stop):
    path = write_json(tmp_path, "data.json", {})
    assert ToolRouter(SequenceClient(stop), TOOLS).select_and_execute_many(context(), [path]) == ()


@pytest.mark.parametrize("max_steps", [-1, 33, True, 1.0, float("nan")])
def test_step_bound_rejects_invalid_values(max_steps):
    with pytest.raises(ToolRuntimeError, match="max_steps"):
        ToolRouter(SequenceClient(), TOOLS).select_and_execute_many(context(), [], max_steps=max_steps)


def test_step_limit_and_zero_never_request_an_extra_selection(tmp_path):
    path = write_json(tmp_path, "data.json", {})
    client = SequenceClient(selection())
    router = ToolRouter(client, TOOLS)
    assert len(router.select_and_execute_many(context(), [path], max_steps=1)) == 1
    assert router.select_and_execute_many(context(), [path], max_steps=0) == ()
    assert len(client.messages) == 1


@pytest.mark.parametrize("failure", [selection("unknown"), RuntimeError("selection transport failed"), selection("column_summary", column="absent")])
def test_later_failures_preserve_completed_executions(tmp_path, failure):
    path = tmp_path / "data.csv"
    path.write_text("x\n1\n", encoding="utf-8")
    with pytest.raises(ToolRuntimeError) as raised:
        ToolRouter(SequenceClient(selection(), failure), TOOLS).select_and_execute_many(context(), [path])
    assert len(raised.value.completed_executions) == 1
    assert raised.value.completed_executions[0].receipt.state is ToolExecutionState.COMMITTED
    if isinstance(failure, dict) and failure["tool_id"] == "column_summary":
        assert raised.value.receipt.state is ToolExecutionState.FAILED


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), -1, True, "1", 10 ** 400])
def test_budget_is_finite_numeric_and_nonnegative(bad):
    with pytest.raises(ValueError):
        ToolBudget(bad)
    with pytest.raises(ValueError):
        ToolBudget(2).reserve(bad)


def test_shared_budget_and_failed_reservation_preserve_completed(tmp_path):
    root, _ = custom_tool(tmp_path, cost=1)
    first = write_json(tmp_path, "first.json", {})
    second = write_json(tmp_path, "second.json", {})
    other = selection("custom")
    other["dataset_id"] = "dataset_2"
    budget = ToolBudget(1)
    router = ToolRouter(SequenceClient(selection("custom"), other), root, budget=budget)
    with pytest.raises(ToolRuntimeError, match="budget is exhausted") as raised:
        router.select_and_execute_many(context(), [first, second])
    assert len(raised.value.completed_executions) == 1
    assert raised.value.receipt.cost == 0
    assert budget.spent == 1
    assert raised.value.failure_trace.violated_contracts == ("budget_available",)


def test_failed_execution_keeps_reserved_cost_and_default_budget_is_zero(tmp_path):
    root, _ = custom_tool(tmp_path, cost=1, body="def run(parameters): raise ValueError('adapter failed')\n")
    path = write_json(tmp_path, "data.json", {})
    with pytest.raises(ToolRuntimeError, match="budget is exhausted"):
        ToolRouter(SequenceClient(selection("custom")), root).select_and_execute(context(), [path])
    budget = ToolBudget(1)
    with pytest.raises(ToolRuntimeError, match="adapter failed") as raised:
        ToolRouter(SequenceClient(selection("custom")), root, budget=budget).select_and_execute(context(), [path])
    assert budget.spent == 1 and raised.value.receipt.cost == 1


@pytest.mark.parametrize("text", ['{"a": 1, "a": 2}', '{"x": NaN}', '[Infinity]', '[1e999]'])
def test_strict_json_rejects_duplicates_and_nonfinite(text):
    with pytest.raises(ValueError):
        json_loads(text)


@pytest.mark.parametrize("value", [float("nan"), (1, 2), {1: "bad"}, {"x": object()}])
def test_strict_json_rejects_non_json_objects(value):
    with pytest.raises(ValueError):
        json_value(value)


def test_schema_validates_finite_types_ranges_and_unknown_keywords():
    schema = {"type": "number", "minimum": 0, "maximum": 2}
    check_schema(schema)
    for value in (True, float("nan"), float("inf"), -1, 3, "1"):
        with pytest.raises(ValueError):
            validate_schema(value, schema)
    with pytest.raises(ValueError, match="Unknown schema"):
        check_schema({"type": "string", "pattern": ".*"})
    with pytest.raises(ValueError, match="additional properties"):
        check_schema({"type": "object", "additionalProperties": True})


@pytest.mark.parametrize("arguments", [{"sample_rows": True}, {"sample_rows": 26}, {"sample_rows": float("nan")}, {"shell": "x"}])
def test_registered_parameter_schema_rejects_invalid_model_arguments(tmp_path, arguments):
    path = write_json(tmp_path, "data.json", {})
    with pytest.raises(ToolRuntimeError):
        ToolRouter(SequenceClient(selection(**arguments)), TOOLS).select_and_execute(context(), [path])


@pytest.mark.parametrize("body", [
    "def run(parameters): return {'schema_version':'1.0','payload':{'x':float('nan')}}\n",
    "def run(parameters): return {'schema_version':'2.0','payload':{}}\n",
    "def run(parameters): return {'schema_version':'1.0','payload':[], 'observations':['ok']}\n",
    "def run(parameters): return {'observations':['not enough']}\n",
    "def run(parameters): return {'schema_version':'1.0','payload':{},'evidence_kind':'real_measurement'}\n",
])
def test_invalid_output_fails_with_output_checked_receipt(tmp_path, body):
    root, _ = custom_tool(tmp_path, body=body)
    path = write_json(tmp_path, "data.json", {})
    with pytest.raises(ToolRuntimeError) as raised:
        ToolRouter(SequenceClient(selection("custom")), root).select_and_execute(context(), [path])
    assert raised.value.failure_trace.first_invalid_transition is ToolExecutionState.OUTPUT_CHECKED
    assert raised.value.receipt.state is ToolExecutionState.FAILED


def test_manifest_cannot_promote_analysis_to_real_measurement(tmp_path):
    root, _ = custom_tool(tmp_path, evidence_kind="real_measurement")
    with pytest.raises(ToolRuntimeError, match="forbidden"):
        LocalToolCatalog(root).discover()


@pytest.mark.parametrize("target", ["manifest", "entrypoint", "core"])
def test_source_hash_includes_manifest_entrypoint_and_declared_core(tmp_path, target):
    core = tmp_path / "core.py"
    core.write_text("VALUE = 1\n", encoding="utf-8")
    root, directory = custom_tool(tmp_path, source_files=["core.py"])
    old = LocalToolCatalog(root).discover()[0]
    changed = {"manifest": directory / "manifest.json", "entrypoint": directory / "tool.py", "core": core}[target]
    if target == "manifest":
        content = json_loads(changed.read_text(encoding="utf-8"))
        content["description"] = "Changed."
        changed.write_text(json_dumps(content), encoding="utf-8")
    else:
        changed.write_text(changed.read_text(encoding="utf-8") + "\n# version change\n", encoding="utf-8")
    new = LocalToolCatalog(root).discover()[0]
    assert old.tool_version_sha256 != new.tool_version_sha256
    with pytest.raises(ToolRuntimeError, match="version changed"):
        ToolRouter._invoke(old, {"dataset_path": "not-read"})


@pytest.mark.parametrize("paths", [["../outside.py"], ["core.py", "core.py"], ["missing.py"]])
def test_declared_source_paths_cannot_escape_or_duplicate(tmp_path, paths):
    (tmp_path / "core.py").write_text("x = 1\n", encoding="utf-8")
    root, _ = custom_tool(tmp_path, source_files=paths)
    with pytest.raises(ToolRuntimeError):
        LocalToolCatalog(root).discover()


def bundle(actions=None):
    return {"schema_version": "1.0", "budget": 4, "cost_unit": "declared_units", "context": "cell-A", "time_hours": 2,
            "required": ["h1", "h2"], "sources": [{"id": "s1", "independence_group": "g1"}],
            "actions": actions if actions is not None else [action("a", 2, ["h1"]), action("b", 3, ["h2"])]}


def action(identifier, cost, distinguishes, **extra):
    return {"id": identifier, "cost": cost, "cost_unit": "declared_units", "distinguishes": distinguishes,
            "source_ids": ["s1"], "context": "cell-A", "time_hours": 2, "independent_unit": "u1",
            "quantity": "proximal_activity", **extra}


def optimize(tmp_path, data):
    return evidence_bundle_optimize({"dataset_path": str(write_json(tmp_path, "bundle.json", data))})["payload"]


def test_fixed_candidate_solver_matches_independent_exhaustive_oracle(tmp_path):
    rng = random.Random(704)
    for _ in range(20):
        required = ["h1", "h2", "h3"]
        actions = [action(f"a{i}", rng.randrange(5), [key for key in required if rng.choice([True, False])],
                          prerequisites=["unknown"] if i == 0 else []) for i in range(7)]
        data = bundle(actions)
        data.update(required=required, budget=rng.randrange(8), weights={"h1": 2, "h2": 1, "h3": 3})
        candidates = []
        for size in range(len(actions) + 1):
            for subset in itertools.combinations(actions, size):
                if any(item["prerequisites"] for item in subset) or sum(item["cost"] for item in subset) > data["budget"]:
                    continue
                covered = {key for item in subset for key in item["distinguishes"]}
                rank = (-sum(data["weights"][key] for key in covered), sum(item["cost"] for item in subset),
                        len(subset), tuple(item["id"] for item in subset))
                candidates.append((rank, covered))
        expected, covered = min(candidates)
        actual = optimize(tmp_path, data)
        assert actual["selected_action_ids"] == list(expected[3])
        assert actual["covered"] == sorted(covered)
        assert actual["total_cost"] == expected[1]
        assert actual["independent_measurement_count"] is None
        assert actual["missing_prerequisites"] == ["unknown"]


def test_order_invariance_and_shared_sources_do_not_inflate_coverage(tmp_path):
    data = bundle([action("b", 1, ["h1", "h2"]), action("a", 1, ["h1", "h2"])])
    assert optimize(tmp_path, data)["selected_action_ids"] == ["a"]
    data["actions"].reverse()
    assert optimize(tmp_path, data)["coverage_score"] == 2
    assert optimize(tmp_path, data)["selected_action_ids"] == ["a"]


@pytest.mark.parametrize("field,value", [("context", "other"), ("time_hours", 3), ("source_ids", ["unknown"]),
                                          ("cost_unit", "other"), ("quantity", "unspecified"), ("cost", True)])
def test_bundle_rejects_wrong_scope_units_or_unknown_capability(tmp_path, field, value):
    data = bundle()
    data["actions"][0][field] = value
    with pytest.raises(ValueError):
        optimize(tmp_path, data)


def test_bundle_nan_and_candidate_bound_are_rejected(tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({**bundle(), "budget": float("nan")}), encoding="utf-8")
    with pytest.raises(ValueError, match="Non-finite"):
        evidence_bundle_optimize({"dataset_path": str(path)})
    with pytest.raises(ValueError, match="at most 16"):
        optimize(tmp_path, bundle([action(f"a{i}", 1, ["h1"]) for i in range(17)]))


def test_composition_uses_existing_core_without_certifying_gate_or_joint_optimality(tmp_path):
    data = bundle([
        action("gate", 2, [], supplies=["functional:activity"]),
        action("readout", 3, ["h1", "h2"], interpretation_gate="functional:activity", expected_outcomes={"h1": "up", "h2": "down"}),
    ])
    data["composition"] = {"id": "declared_shared_control", "shared_control_saving": 1}
    result = optimize(tmp_path, data)
    assert result["selected_action_ids"] == [] and result["uncovered"] == ["h1", "h2"]
    composed = result["composition"]
    assert composed["preferred_plan_id"] == "plan[gate|readout]"
    assert composed["joint_set_cover_optimization"] is False
    candidate = composed["ranked_candidates"][0]
    assert candidate["total_cost_if_gate_passes"] == 4
    assert candidate["worst_declared_case_residual"] == 1
    assert candidate["premise_status"] == "unknown" and candidate["confirmed"] is False
    assert candidate["continue_only_if_gate_passes"] is True
    data["actions"][0]["independent_unit"] = "other-unit"
    invalid = optimize(tmp_path, data)["composition"]
    assert invalid["preferred_plan_id"] is None
    assert invalid["rejected"][0]["reason"] == "independent_unit_mismatch"


def modality(identifier, kind="transcript", **extra):
    quantities = {"transcript": "rna_abundance", "protein": "protein_abundance", "activity": "proximal_activity",
                  "occupancy": "target_occupancy", "morphology": "morphology_feature"}
    return {"id": identifier, "pair_id": "p1", "modality": kind, "source_id": "s1", "context": "cell-A",
            "time_hours": 2, "independent_unit": "u1", "replicate": "r1", "quantity": quantities[kind], "entity": "target-A",
            "contrast_id": "treated-vs-control", "feature": "declared-feature", "unit": "declared-unit", "value": 2,
            "reference_value": 1, **extra}


def align(tmp_path, records):
    data = {"schema_version": "1.0", "sources": [{"id": "s1", "independence_group": "g1"}], "records": records}
    return multimodal_alignment({"dataset_path": str(write_json(tmp_path, "paired.json", data))})["payload"]


def test_typed_paired_records_retain_quantities_and_only_report_review_candidates(tmp_path):
    first = modality("rna")
    assert isinstance(ModalityRecord.from_dict(first), ModalityRecord)
    result = align(tmp_path, [first, modality("activity", "activity", value=0)])
    assert len(result["alignment_qc"]["aligned_groups"]) == 1
    assert result["alignment_qc"]["declared_independent_unit_count"] == 1
    assert result["alignment_qc"]["verified_independent_measurement_count"] is None
    candidate = result["contradiction_candidates"][0]
    assert candidate["quantities"] == ["rna_abundance", "proximal_activity"]
    assert candidate["requires_review"] is True
    assert candidate["expected_direction_relation"] == "not_assumed"


@pytest.mark.parametrize("field,value", [("context", "cell-B"), ("time_hours", 3), ("replicate", "r2"),
                                          ("independent_unit", "u2"), ("entity", "target-B"), ("contrast_id", "another")])
def test_wrong_pairing_scope_never_produces_cross_context_discordance(tmp_path, field, value):
    result = align(tmp_path, [modality("rna"), modality("activity", "activity", value=0, **{field: value})])
    assert result["contradiction_candidates"] == []
    assert result["alignment_qc"]["aligned_groups"] == []
    assert field in result["alignment_qc"]["mismatches"][0]["fields"]


def test_occupancy_and_morphology_are_qc_only_not_activity(tmp_path):
    records = [modality("rna"), modality("occupancy", "occupancy", value=0), modality("image", "morphology", value=0)]
    result = align(tmp_path, records)
    assert len(result["alignment_qc"]["aligned_groups"]) == 1
    assert result["contradiction_candidates"] == []
    records[2]["quantity"] = "proximal_activity"
    with pytest.raises(ValueError, match="Modality/quantity mismatch"):
        align(tmp_path, records)


def test_missing_values_and_ambiguous_replicates_are_not_imputed(tmp_path):
    result = align(tmp_path, [modality("rna", value=None), modality("protein", "protein", value=0)])
    assert result["records"][0]["value"] is None
    assert result["contradiction_candidates"] == []
    result = align(tmp_path, [modality("rna1"), modality("rna2"), modality("protein", "protein", value=0)])
    assert result["alignment_qc"]["ambiguous_groups"]
    assert result["contradiction_candidates"] == []
    result = align(tmp_path, [modality("rna", context=None), modality("protein", "protein", value=0)])
    assert result["alignment_qc"]["excluded_record_ids"] == ["rna"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "2"])
def test_typed_record_rejects_nan_and_wrong_numeric_types(value):
    with pytest.raises(ValueError):
        ModalityRecord.from_dict(modality("rna", value=value))


def test_legacy_display_strings_and_structured_filter_counts_are_both_preserved(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("x\n1\n2\n3\n", encoding="utf-8")
    result = ToolRouter(SequenceClient(selection("table_filter", column="x", operator="greater_than", value="1", max_rows=1)), TOOLS).select_and_execute(context(), [path])
    assert "matched 2 rows" in result.observations[0]
    assert result.payload["matched_count"] == 2
    assert result.payload["sample_rows"] == [{"x": "2"}]
    assert result.payload["sample_truncated"] is True
    assert result.evidence_kind is EvidenceKind.DERIVED_ANALYSIS


def test_csv_numeric_nan_is_rejected_instead_of_silently_counted(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("x\nNaN\n", encoding="utf-8")
    with pytest.raises(ToolRuntimeError, match="Non-finite"):
        ToolRouter(SequenceClient(selection("column_summary", column="x")), TOOLS).select_and_execute(context(), [path])


def test_explicit_default_is_the_same_call_as_omitting_it(tmp_path):
    path = write_json(tmp_path, "data.json", {})
    client = SequenceClient(selection(), selection(sample_rows=5))
    executions = ToolRouter(client, TOOLS).select_and_execute_many(context(), [path])
    assert len(executions) == 1
    assert executions[0].receipt.parameters["sample_rows"] == 5
    assert len(client.messages) == 2


def test_invalid_schema_default_is_rejected_at_registration():
    with pytest.raises(ValueError, match="schema.default"):
        check_schema({"type": "integer", "minimum": 1, "default": False})
    with pytest.raises(ValueError, match="Non-finite schema bound"):
        check_schema({"type": "number", "maximum": 10 ** 400})


def test_dataset_json_cannot_self_certify_a_measured_prerequisite(tmp_path):
    data = bundle()
    data["measured_fields"] = {"functional:activity": True}
    with pytest.raises(ValueError, match="unknown fields"):
        optimize(tmp_path, data)


def test_strict_json_bounds_recursive_objects():
    value = []
    value.append(value)
    with pytest.raises(ValueError, match="nesting"):
        json_value(value)


def test_receipt_output_hash_covers_payload_not_just_observations(tmp_path):
    root, directory = custom_tool(tmp_path)
    path = write_json(tmp_path, "data.json", {})
    first = ToolRouter(SequenceClient(selection("custom")), root).select_and_execute(context(), [path])
    (directory / "tool.py").write_text("def run(parameters): return {'schema_version':'1.0','payload':{'ok':False}}\n", encoding="utf-8")
    second = ToolRouter(SequenceClient(selection("custom")), root).select_and_execute(context(), [path])
    assert first.observations == second.observations
    assert first.receipt.output_sha256 != second.receipt.output_sha256
    assert first.receipt.tool_version_sha256 != second.receipt.tool_version_sha256
