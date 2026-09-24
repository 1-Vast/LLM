"""CLI for isolated, resumable evidence replay evaluation.

File summary
- Path: src/evaluation/cli.py
- Purpose: Drive the leakage-bounded replay evaluation from the command line.
- Core points:
  - Loads frozen cases and runs selected baseline or MAESTRO policies to completion.
  - Writes a hashed, resumable report without exposing private scoring answers.
  - Optional laboratory-unit costing, a recorded pre-registration digest, and the section 37 score table with its section 29 exit verdict.
- Interfaces: `main`
- Depends on: agent.configuration, agent.llm, agent.orchestrator, evaluation.baselines, evaluation.cases, evaluation.lab_cost, evaluation.prediction_controls, evaluation.runner, evaluation.score_table, evaluation.tracking
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.configuration import MAESTROSettings
from agent.llm import DeepSeekChatClient
from agent.orchestrator import MAESTROOrchestrator

from .baselines import (
    ExpertWorkflowPolicy,
    LLMActionPolicy,
    MAESTROCorePolicy,
    MAESTROOrchestratorPolicy,
    OutcomeAwareSelectionPolicy,
    PredictionValuePolicy,
    RandomLegalEditPolicy,
    RepairDisabledPolicy,
)
from .capabilities import load_capability_registry
from .cases import CaseRepository
from .lab_cost import load_costing_profile
from .llm_rows import ExplicitHypothesesLLMPolicy
from .provider_spend import SpendLedger
from .prediction_controls import (
    RemovedPredictionValuePolicy,
    ShuffledPredictionFullSystemPolicy,
    ShuffledPredictionValuePolicy,
    is_identity,
)
from .proposal_arms import (
    LLMRegistryRepairPolicy,
    RegistryExpandedSelectionPolicy,
    RegistryRandomProposalPolicy,
    RegistryRepairRulePolicy,
)
from .runner import EvaluationRunner
from .score_table import build_score_table, exit_verdict, load_clusters, render_text
from .tracking import TrackingCompleter
from .voi_arm import SimpleModelVOIPolicy, fit_action_reliability

# The offline arms the protocol run evaluates: the section 9.3 ablations, and the
# prediction-input panel whose shuffled and removed controls section 37 requires.
PROTOCOL_ARMS = (
    "expert",
    "prediction",
    "prediction_shuffled",
    "prediction_removed",
    "maestro",
    "repair_disabled",
    "random_legal_edit",
    "outcome_aware",
)

# The offline arms of a package that offers a capability registry: three that cannot propose
# a repair at all, the directed proposal, and its two controls. The LLM proposal arm is paid
# and is therefore named explicitly rather than included here.
REPAIR_ARMS = (
    "expert",
    "outcome_aware",
    "maestro",
    "registry_repair_rule",
    "registry_expanded",
    "registry_repair_random",
)

# The offline section 37 rows. Rows 3 and 4 are provider-backed and are named explicitly, so
# running the offline rows never makes a paid call by accident.
ROW_ARMS = (
    "expert",
    "simple_model_voi",
    "maestro",
    "maestro_shuffled_predictions",
)


def main() -> int:
    """Run the MAESTRO replay evaluation CLI and return a process exit code."""

    parser = argparse.ArgumentParser(
        description="Run leakage-bounded replay evaluation. 'all' is offline; LLM policies are explicit."
    )
    parser.add_argument("--public-cases", type=Path, default=Path("data/evaluation/cases/public"))
    parser.add_argument("--private-results", type=Path, default=Path("data/evaluation/cases/private"))
    parser.add_argument("--output", type=Path, default=Path("evaluations"))
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--case-id", help="Evaluate one registered public case identifier.")
    parser.add_argument("--run-id", help="Safe identifier for a new isolated run, or the run to resume.")
    parser.add_argument("--resume", action="store_true", help="Resume the explicitly named --run-id; never resumes implicitly.")
    parser.add_argument("--mode", choices=("regression", "decision"), default="regression", help="Regression uses private rule triggers; decision independently scores policy submissions.")
    parser.add_argument("--maximum-steps", type=int, default=8)
    parser.add_argument(
        "--policy",
        choices=(
            "expert",
            "prediction",
            "prediction_shuffled",
            "prediction_removed",
            "maestro",
            "ordinary_llm",
            "maestro_llm",
            "maestro_llm_ruled",
            "repair_disabled",
            "random_legal_edit",
            "outcome_aware",
            "registry_repair_rule",
            "registry_expanded",
            "registry_repair_random",
            "registry_repair_llm",
            "simple_model_voi",
            "explicit_hypotheses_llm",
            "maestro_shuffled_predictions",
            "ablation",
            "protocol",
            "repair",
            "rows",
            "all",
        ),
        default="all",
        help=(
            "'protocol' runs the offline ablations with the prediction-input panel; 'repair' runs the "
            "capability-registry arms and their controls; 'all' keeps its original arm set."
        ),
    )
    parser.add_argument("--split", choices=("all", "development", "test"), default="all", help="Restrict to one manifest split; requires --manifest.")
    parser.add_argument(
        "--quality-dropout",
        default="",
        help=(
            "Comma-separated action identifiers whose revealed records are marked quality-failed "
            "for every policy in this run. A declared environment perturbation, not a data finding: "
            "it tests whether a policy notices that acquired evidence is uninterpretable."
        ),
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/evaluation/derived/real_case_manifest.json"), help="Evaluator-owned case manifest used for split selection and reporting.")
    parser.add_argument("--costing", type=Path, help="Costing overlay (maestro.costing.v1) pricing the menu in wells and turnaround days.")
    parser.add_argument(
        "--capabilities",
        type=Path,
        help=(
            "Capability registry (maestro.capabilities.v1). With one, a policy may propose a repair for a "
            "premise the menu cannot supply, and the verdict is also reported against what the registry "
            "makes reachable."
        ),
    )
    parser.add_argument("--state-root", type=Path, help="Directory for the isolated per-case ledgers; defaults to <output>/runs.")
    parser.add_argument("--preregistration", type=Path, help="A pre-registration written before this run; its digest is recorded and re-checked afterwards.")
    parser.add_argument("--score-table", action="store_true", help="Write the section 37 score table beside the evaluation report.")
    parser.add_argument(
        "--prior-total-usd",
        type=float,
        default=0.694763,
        help=(
            "Recorded campaign spend carried into this run, so the paid ceiling is enforced against "
            "the whole campaign rather than against one run."
        ),
    )
    parser.add_argument("--ceiling-usd", type=float, default=5.0, help="Authorised paid-call ceiling.")
    parser.add_argument(
        "--provider-case-estimate-usd",
        type=float,
        default=0.02,
        help=(
            "Expected paid cost per case for a provider-backed arm. The run is refused before its "
            "first call if this estimate times the case count would exceed the remaining ceiling."
        ),
    )
    parser.add_argument(
        "--row-arms",
        help=(
            "JSON mapping of section 37 row keys to evaluated arm names, declared for this run. "
            "A row with no arm stays 'not_run' with its reason; an arm is never assigned to a row "
            "merely because it exists."
        ),
    )
    arguments = parser.parse_args()
    if arguments.resume and not arguments.run_id:
        parser.error("--resume requires --run-id.")
    if arguments.maximum_steps < 1:
        parser.error("--maximum-steps must be positive.")
    started = datetime.now(timezone.utc)
    preregistration = None
    if arguments.preregistration is not None:
        if not arguments.preregistration.is_file():
            parser.error("--preregistration names no file.")
        preregistration = _preregistration_record(arguments.preregistration)
        # A filesystem modification time and the wall clock can disagree by a fraction of a
        # second, so a pre-registration written immediately before the run would otherwise look
        # like one edited during it. One second is far below the duration of any run this guard
        # protects, and the digest is re-checked after the run regardless.
        if datetime.fromisoformat(preregistration["modified_utc"]) > started + timedelta(seconds=1):
            parser.error("preregistration_modified_after_run_start: a pre-registration must exist before the run it governs.")

    run_id = arguments.run_id or _new_run_id()
    _safe_component(run_id)
    runs_root = arguments.output / "runs"
    state_root = arguments.state_root or runs_root
    run_directory = runs_root / run_id
    if arguments.resume:
        if not run_directory.is_dir():
            parser.error("The requested --run-id has no prior evaluation state.")
    elif run_directory.exists():
        parser.error("Run directory already exists; use a new --run-id or explicit --resume.")
    run_directory.mkdir(parents=True, exist_ok=True)

    costing = load_costing_profile(arguments.costing) if arguments.costing is not None else None
    registry = load_capability_registry(arguments.capabilities) if arguments.capabilities is not None else None
    if arguments.policy in {"registry_repair_rule", "registry_expanded", "registry_repair_random", "registry_repair_llm", "repair"} and registry is None:
        parser.error("the capability-registry arms require --capabilities")
    cases = CaseRepository(arguments.public_cases, arguments.private_results, costing=costing).load()
    training_cases = cases
    if arguments.split != "all":
        if not arguments.manifest.is_file():
            parser.error("--split requires an existing --manifest.")
        manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
        allowed = {entry["case_id"] for entry in manifest.get("cases", ()) if entry.get("split") == arguments.split}
        cases = tuple(item for item in cases if item[0].public.identifier in allowed)
        if not cases:
            parser.error(f"No registered case belongs to split '{arguments.split}'.")
    if arguments.case_id:
        cases = tuple(item for item in cases if item[0].public.identifier == arguments.case_id)
        if not cases:
            parser.error(f"No registered public case has identifier '{arguments.case_id}'.")
    dropout = tuple(item.strip() for item in arguments.quality_dropout.split(",") if item.strip())
    if dropout:
        cases = tuple((case, _quality_dropout(outcomes, dropout)) for case, outcomes in cases)
    policies = {
        "expert": ExpertWorkflowPolicy(),
        "prediction": PredictionValuePolicy(),
        # Sections 29 and 37: the same heuristic with its declared values moved to the
        # wrong actions, and with them switched off.
        "prediction_shuffled": ShuffledPredictionValuePolicy(),
        "prediction_removed": RemovedPredictionValuePolicy(),
        "maestro": MAESTROCorePolicy(),
        # Innovation.md section 9.3 ablations: is the gain from the repair, or from
        # simply being allowed to edit the plan several times?
        "repair_disabled": RepairDisabledPolicy(),
        "random_legal_edit": RandomLegalEditPolicy(),
        # Strongest honest alternative to directed repair: read the same public
        # declarations, but select once instead of checking and editing a plan.
        "outcome_aware": OutcomeAwareSelectionPolicy(),
        # Directed repair over a capability registry, and the two controls that price it:
        # the whole catalogue admitted in advance, and a proposal drawn without direction.
        "registry_repair_rule": RegistryRepairRulePolicy(),
        "registry_expanded": RegistryExpandedSelectionPolicy(),
        "registry_repair_random": RegistryRandomProposalPolicy(),
        # Section 37 row six for the full system: the same loop with its prediction input
        # deranged. An identity with `maestro` is the measurement, not a broken control.
        "maestro_shuffled_predictions": ShuffledPredictionFullSystemPolicy(),
    }
    # Section 37 row 2 needs an outcome model fitted on the development split, so the table is
    # built here from the manifest rather than declared. With no manifest the arm is refused
    # rather than run on an unfitted model.
    development_ids: tuple[str, ...] = ()
    if arguments.manifest.is_file():
        manifest_rows = json.loads(arguments.manifest.read_text(encoding="utf-8")).get("cases", ())
        development_ids = tuple(
            str(entry["case_id"]) for entry in manifest_rows if entry.get("split") == "development"
        )
    if development_ids:
        development_training_cases = tuple(
            item for item in training_cases if item[0].public.identifier in development_ids
        )
        if development_training_cases:
            policies["simple_model_voi"] = SimpleModelVOIPolicy(
                reliability=fit_action_reliability(development_training_cases, development_cases=development_ids)
            )
        elif arguments.policy in {"simple_model_voi", "rows"}:
            parser.error(
                "simple_model_voi_missing_development_cases: --manifest declares a development split, "
                "but no registered training case belongs to it; the arm is not run on an unfitted outcome model."
            )
    elif arguments.policy == "simple_model_voi":
        parser.error(
            "simple_model_voi requires a --manifest declaring a development split; the arm is not "
            "run on an unfitted outcome model."
        )
    ledger = SpendLedger.load(
        run_directory / "provider_spend.json",
        ceiling_usd=arguments.ceiling_usd,
        prior_total_usd=arguments.prior_total_usd,
        prior_note=(
            "0.590786 recorded on 2026-09-13, plus 0.058555 for an LLM arm never written back, "
            "plus 0.045422 recorded only in a concurrent session's notes"
        ),
    )
    tracker: TrackingCompleter | None = None
    if arguments.policy == "explicit_hypotheses_llm":
        settings = MAESTROSettings.from_workspace(arguments.workspace)
        tracker = TrackingCompleter(DeepSeekChatClient(settings))
        policies[arguments.policy] = ExplicitHypothesesLLMPolicy(tracker, ledger=ledger)
    if arguments.policy == "registry_repair_llm":
        settings = MAESTROSettings.from_workspace(arguments.workspace)
        tracker = TrackingCompleter(DeepSeekChatClient(settings))
        policies[arguments.policy] = LLMRegistryRepairPolicy(tracker)
    if arguments.policy in {"ordinary_llm", "maestro_llm", "maestro_llm_ruled"}:
        settings = MAESTROSettings.from_workspace(arguments.workspace)
        tracker = TrackingCompleter(DeepSeekChatClient(settings))
        if arguments.policy == "ordinary_llm":
            policies[arguments.policy] = LLMActionPolicy(tracker)
        else:
            def runtime_factory(case_directory: Path) -> MAESTROOrchestrator:
                return MAESTROOrchestrator.from_workspace(
                    arguments.workspace,
                    state_directory=case_directory,
                    enable_virtual_cell=False,
                    disable_case_store=True,
                    client=tracker,
                )
            # `maestro_llm` lets the model submit the terminal decision.
            # `maestro_llm_ruled` keeps the model in charge of composing and
            # acquiring, and hands the terminal decision to the deterministic
            # interpretation rule, which is the division of labour the
            # architecture actually specifies. Comparing them measures what the
            # model's own judgement adds, or costs, at the decision step.
            policies[arguments.policy] = MAESTROOrchestratorPolicy(
                decision_client=tracker if arguments.policy == "maestro_llm" else None,
                runtime_factory=runtime_factory,
            )
    if arguments.policy == "all":
        # The original offline set, named rather than read off the dictionary, so adding a
        # control arm never silently changes what 'all' runs.
        selected = tuple(policies[name] for name in ("expert", "prediction", "maestro", "repair_disabled", "random_legal_edit", "outcome_aware"))
    elif arguments.policy == "ablation":
        selected = (
            policies["maestro"],
            policies["repair_disabled"],
            policies["random_legal_edit"],
            policies["outcome_aware"],
        )
    elif arguments.policy == "protocol":
        selected = tuple(policies[name] for name in PROTOCOL_ARMS)
    elif arguments.policy == "repair":
        selected = tuple(policies[name] for name in REPAIR_ARMS)
    elif arguments.policy == "rows":
        # The offline section 37 rows: the fixed flow (row 1), the fitted model with value of
        # information (row 2), the full system (row 5) and its shuffled-prediction control
        # (row 6). The two provider-backed rows are named explicitly, never bundled here.
        missing = [name for name in ROW_ARMS if name not in policies]
        if missing:
            parser.error("rows requires " + ", ".join(missing))
        selected = tuple(policies[name] for name in ROW_ARMS)
    else:
        selected = (policies[arguments.policy],)
    # A ceiling enforced only per call still lets a long run walk up to it one case at a time
    # and stop half way through, which spends the budget and produces no comparable arm. The
    # projection is refused by the same named rule before the first call is made.
    if tracker is not None:
        projection = len(cases) * float(arguments.provider_case_estimate_usd)
        ledger.reserve(f"run_projection:{arguments.policy}:{len(cases)}_cases", projection)
    runner = EvaluationRunner(
        run_id=run_id,
        state_root=state_root,
        mode=arguments.mode,
        maximum_steps=arguments.maximum_steps,
        capability_registry=registry,
    )
    reports = [runner.evaluate(policy, cases) for policy in selected]
    # Arms that hold the ledger themselves have already charged their calls. For every other
    # provider-backed arm the tracker's usage records are priced here, so no paid call in a run
    # is left out of the ledger, and the ledger is written as its own artifact.
    if tracker is not None and not ledger.entries:
        for index, call in enumerate(tracker.calls):
            ledger.charge(f"{arguments.policy}:call{index}", dict(call.get("usage", {})), status="ok")
    if ledger.entries:
        ledger.write()
    if preregistration is not None:
        preregistration["unchanged_during_run"] = _sha256(arguments.preregistration) == preregistration["sha256"]
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "resume": arguments.resume,
        "mode": arguments.mode,
        "case_count": len(cases),
        "split": arguments.split,
        "quality_dropout": list(dropout),
        "public_cases": str(arguments.public_cases),
        "implementation_hashes": _implementation_hashes(arguments.workspace),
        "case_hashes": _case_hashes(arguments.public_cases, arguments.private_results, cases),
        "costing": (
            {"identifier": costing.identifier, "sha256": costing.sha256, "path": str(arguments.costing)}
            if costing is not None
            else None
        ),
        "capabilities": (
            {
                "identifier": registry.identifier,
                "sha256": registry.sha256,
                "path": str(arguments.capabilities),
                "offers": sorted(registry.offers),
            }
            if registry is not None
            else None
        ),
        "preregistration": preregistration,
        # Laboratory cost is wells and days; provider calls are reported here, separately,
        # and never enter the laboratory totals.
        "provider_calls": tracker.calls if tracker else [],
        "provider_spend": ledger.payload() if ledger.entries else None,
        "reports": [asdict(report) for report in reports],
    }
    suffix = f"_resume-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}" if arguments.resume else ""
    destination = run_directory / f"evaluation_{arguments.policy}_{arguments.mode}{suffix}.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destination)
    if arguments.score_table:
        declared_rows = json.loads(arguments.row_arms) if arguments.row_arms else None
        if declared_rows is not None and not isinstance(declared_rows, dict):
            parser.error("--row-arms must be a JSON object mapping row keys to arm names")
        table = build_score_table(
            payload["reports"],
            clusters=load_clusters(arguments.manifest),
            row_arms=declared_rows,
            provenance={
                "evaluation": destination.name,
                "run_id": run_id,
                "public_cases": str(arguments.public_cases),
                "manifest": str(arguments.manifest) if arguments.manifest.is_file() else None,
                "costing_identifier": costing.identifier if costing is not None else None,
                "costing_sha256": costing.sha256 if costing is not None else None,
                "preregistration_sha256": preregistration["sha256"] if preregistration is not None else None,
            },
        )
        by_policy = {str(report["policy"]): report for report in payload["reports"]}
        panel = ("prediction_value_heuristic", "prediction_value_removed", "prediction_value_shuffled")
        if all(name in by_policy for name in panel):
            table["exit_verdict"] = exit_verdict(
                input_name="declared prediction_value",
                informed=by_policy["prediction_value_heuristic"],
                removed=by_policy["prediction_value_removed"],
                shuffled=by_policy["prediction_value_shuffled"],
                declaration_reader=by_policy.get("outcome_aware_selection"),
            )
            table["prediction_shuffle_identity_cases"] = sum(1 for case, _ in cases if is_identity(case.public))
        table_path = run_directory / f"score_table_{arguments.policy}_{arguments.mode}{suffix}.json"
        table_path.write_text(json.dumps(table, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(render_text(table))
        print(table_path)
    return 0


def _preregistration_record(path: Path) -> dict[str, object]:
    """Digest and modification time of a pre-registration, so 'written before' is checkable."""

    return {
        "path": str(path),
        "sha256": _sha256(path),
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def _quality_dropout(outcomes, action_ids):
    """Mark the named revealed records as quality-failed for every policy alike.

    The record stays valid and still carries its outcome label, so a policy that
    reads the label without checking the declared quality check will act on an
    uninterpretable measurement. The perturbation is recorded in the run report
    and applied identically to every policy, so the comparison stays matched.
    """

    return {
        identifier: replace(outcome, biological_quality="failed") if identifier in action_ids else outcome
        for identifier, outcome in outcomes.items()
    }


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def _safe_component(value: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ValueError("run_id contains unsupported path characters.")


def _implementation_hashes(workspace: Path) -> dict[str, str]:
    paths = (
        workspace / "src" / "evaluation" / "cases.py",
        workspace / "src" / "evaluation" / "baselines.py",
        workspace / "src" / "evaluation" / "runner.py",
        workspace / "src" / "evaluation" / "scoring.py",
        workspace / "src" / "evaluation" / "lab_cost.py",
        workspace / "src" / "evaluation" / "prediction_controls.py",
        workspace / "src" / "evaluation" / "score_table.py",
        workspace / "src" / "evaluation" / "capabilities.py",
        workspace / "src" / "evaluation" / "proposal_arms.py",
        workspace / "src" / "evaluation" / "repair_replay.py",
        workspace / "src" / "agent" / "orchestrator.py",
        workspace / "src" / "agent" / "cases.py",
    )
    return {str(path.relative_to(workspace)): _sha256(path) for path in paths}


def _case_hashes(public_directory: Path, private_directory: Path, cases) -> dict[str, dict[str, str]]:
    return {
        case.public.identifier: {
            "public": _sha256(public_directory / f"{case.public.identifier.replace('-', '_')}.json") if (public_directory / f"{case.public.identifier.replace('-', '_')}.json").is_file() else _sha256(next(path for path in public_directory.glob("*.json") if json.loads(path.read_text(encoding="utf-8")).get("identifier") == case.public.identifier)),
            "private": _sha256(private_directory / f"{case.public.identifier}.results.json"),
        }
        for case, _ in cases
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
