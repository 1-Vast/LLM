"""Frozen evaluation of the acquisition factorial through the production contracts.

Arms per evaluation line and half-menu (identical menus, budgets, start information, update and
final rules, cache policy):
  A simple world + knowledge gradient     B STATE world + knowledge gradient
  C simple world + LLM acquisition        D STATE world + LLM acquisition   (only if gates passed)
  plus controls: no-acquisition in each world, and purchase-swap replays.
Every forecast is served by a receipt backend through PredictionCoordinator; every first-well
profile and every validation reveal is a planned action with an imported RETRIEVED_SOURCE result in
CaseStore (public replay, not a new experiment). Validation values are read only after the flag set
is committed. Requires AGENT_FREEZE.json matching AGENT_PROTOCOL.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE)]

from agent.case_store import CaseState, CaseStore, MeasurementResult  # noqa: E402
from agent.memory import RunLogger  # noqa: E402
from agent.prediction import PredictionCoordinator  # noqa: E402
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind  # noqa: E402
from virtual_cell.interface import (Intervention, ModelCapabilities, PredictionCache, PredictionRequest,  # noqa: E402
                                    QueryAssessment, QuerySupport, StatePrediction, SystemContext)

import agent_policy as ap  # noqa: E402

ENDPOINT = "root_deviation_energy_replicate_well"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def cid(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()[:12]


class WorldForecasts:
    """Receipt backend: serves one world's frozen prior for exact (context, label, plate_B) queries."""

    def __init__(self, line, rows, world, mean, sd, version):
        self.line, self.world, self.version = line, world, version
        self.rows = {cid(r["label"]): (r, float(m), float(s)) for r, m, s in zip(rows, mean, sd)}
        self.name = f"zeroshot_world:{world}:{version[:12]}"

    def capabilities(self):
        return ModelCapabilities("zeroshot-context-deviation", self.version, "frozen panel and STATE features",
                                 "exact categorical drug-dose label", ("chemical",), True, False, False,
                                 "development-line calibration")

    def assess_query(self, request):
        item = self.rows.get((request.observation_context or {}).get("candidate"))
        ok = item is not None and request.context.identifier == self.line and \
            request.observation_context.get("plate") == item[0]["plate_B"] and request.readouts == (ENDPOINT,) and \
            request.intervention.identifier == item[0]["drug"] and request.intervention.dose == item[0]["dose_uM"]
        return QueryAssessment(QuerySupport.SUPPORTED if ok else QuerySupport.UNSUPPORTED, (),
                               () if ok else ("condition_receipt_mismatch",), self.capabilities())

    def predict(self, request):
        row, mean, sd = self.rows[request.observation_context["candidate"]]
        return StatePrediction(True, {ENDPOINT: mean}, sd, ("RNA deviation energy only; no viability or efficacy claim",
                               "reference panel and STATE context forecasts; zero-shot context"),
                               supported_variables=(ENDPOINT,), request_id=request.request_id, model_version=self.version,
                               confidence=None, in_distribution=None,
                               uncertainty_components={"prior_sd": "development-line residual SD on the root scale"},
                               compute_cost=0.0)


def request_for(line, row, case_id, plan_version, version):
    return PredictionRequest(f"{case_id}-{plan_version}-{cid(row['label'])}", case_id, "zeroshot-deviation", plan_version,
                             Intervention(row["drug"], "chemical", (), float(row["dose_uM"]), "uM", 24.0),
                             SystemContext(line, "Held-out Tahoe context (documented zero-shot test cell type)",
                                           dataset_id=f"{line}:{row['plate_B']}", control_dataset_id=f"{row['plate_B']}:DMSO_TF"),
                             (ENDPOINT,), version, observation_context={"candidate": cid(row["label"]), "plate": row["plate_B"]})


def action_for(line, row, role):
    plate = row["plate_A"] if role == "screen" else row["plate_B"]
    return EvidenceAction(f"{role}-{cid(row['label'])}",
                          "Retrieve first-well public RNA profile" if role == "screen" else "Reveal committed replicate-well RNA profile",
                          1.0, (), kind=EvidenceActionKind.EVIDENCE_REVIEW, time_hours=24.0,
                          expected_conditions={"label": row["label"], "plate": plate, "well_role": "A" if role == "screen" else "B",
                                               "assay": "single_cell_RNA"},
                          execution_context=line, readout=ENDPOINT)


def purchase(store, case_id, line, row, role, value, prediction=None):
    action = action_for(line, row, role)
    snap = store.record_plan(case_id, [action], ready_to_measure=True, context_identifier=line)
    if snap.state is not CaseState.AWAITING_RESULT:
        raise RuntimeError("budget_or_plan_refused")
    if prediction is not None:
        store.record_prediction(case_id, snap.plan_version, action.identifier, prediction[0].request_id,
                                {"request": prediction[0].to_dict(), "prediction": asdict(prediction[1])})
    result = MeasurementResult(action.identifier, "Retrieved public Tahoe replicate-well RNA profile; not a new experiment",
                               f"State-Tahoe-Filtered:{line}:{row['label']}:{action.expected_conditions['plate']}", line, 24.0,
                               1, True, conditions=action.expected_conditions, metrics={ENDPOINT: repr(float(value))},
                               evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
                               limitations=("one well per role; pooled-line design shares wells across lines",
                                            "retrospective public data previously sampled by this study"),
                               result_id=f"{case_id}-{snap.plan_version}-{action.identifier}", plan_version=snap.plan_version)
    imported = store.import_measurement(case_id, result)
    if not imported.created:
        raise RuntimeError("duplicate_result_import")
    return {"action": action.identifier, "plan_version": snap.plan_version, "role": role, "label": row["label"],
            "replay_access_units": 1, "laboratory_wells_equivalent": 1}


def run_arm(arm, line, menu_id, rows, prior_mean, prior_sd, corr, obs, k, m, policy, out, version, policy_name):
    case_id = f"{arm}-{line.replace('/', '_').replace(' ', '_')}-{menu_id}"
    store = CaseStore(out / "cases.sqlite")
    store.open_case(case_id, budget=float(k + m))
    coordinator = PredictionCoordinator(WorldForecasts(line, rows, arm, prior_mean, prior_sd, version),
                                        RunLogger(out / "logs"), cache=PredictionCache())
    served = []
    for row in rows:
        _, prediction = coordinator.predict(request_for(line, row, case_id, 1, version), case_id)
        if not prediction.applicable:
            raise RuntimeError("forecast_refused")
        served.append(prediction.state_change[ENDPOINT])
    if not np.allclose(served, prior_mean):
        raise RuntimeError("served forecasts differ from frozen prior")
    a, b, obs_sd = obs
    belief = ap.Belief(np.array(served), np.outer(prior_sd, prior_sd) * corr, np.full(len(rows), obs_sd ** 2), b, a)
    log, receipts = [], []
    started = time.perf_counter()

    def buy(i):
        receipts.append(purchase(store, case_id, line, rows[i], "screen", rows[i]["y_A"]))
        return rows[i]["y_A"]
    flags, order = ap.run_episode(belief, None, k, m, policy, on_purchase=buy, log=log)
    plan_version = store.snapshot(case_id).plan_version
    validated = []
    for i in flags:
        req = request_for(line, rows[i], case_id, plan_version + 1, version)
        pred = StatePrediction(True, {ENDPOINT: float(belief.mean[i])}, float(np.sqrt(max(belief.cov[i, i], 0))),
                               ("posterior after purchased first-well profiles",), supported_variables=(ENDPOINT,),
                               request_id=req.request_id, model_version=version, confidence=None, in_distribution=None,
                               uncertainty_components={"posterior_sd": "Gaussian belief on the root scale"}, compute_cost=0.0)
        receipts.append(purchase(store, case_id, line, rows[i], "validate", rows[i]["y_B"], (req, pred)))
        validated.append(rows[i]["y_B"])
    store.record_decision(case_id, status="decided")
    return {"arm": arm, "policy": policy_name, "line": line, "menu": menu_id, "case_id": case_id,
            "screens": [rows[i]["label"] for i in order], "flags": [rows[i]["label"] for i in flags],
            "V": float(np.sum(validated)), "validated_y_B": validated, "log": log, "receipts": receipts,
            "budget": store.budget_status(case_id), "seconds": round(time.perf_counter() - started, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", nargs="+", default=["A", "B", "noneA", "noneB", "C", "D"])
    args = parser.parse_args()
    protocol_path = HERE / "AGENT_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "AGENT_FREEZE.json").read_text(encoding="utf-8"))
    if freeze["protocol_sha256"] != hashlib.sha256(protocol_path.read_bytes()).hexdigest():
        raise PermissionError("agent protocol changed after freeze")
    out = HERE / "agent_eval"
    out.mkdir(exist_ok=True)
    episodes = json.loads((HERE / "agent_eval_inputs" / "EPISODES.json").read_text(encoding="utf-8"))
    corr_all = np.array(protocol["correlation"]["matrix"])
    label_index = {l: i for i, l in enumerate(protocol["correlation"]["labels"])}
    results_path = out / "arm_results.jsonl"
    done = set()
    if results_path.exists():
        done = {(r["arm"], r["line"], r["menu"]) for r in map(json.loads, results_path.read_text().splitlines())}
    client = None
    for ep in episodes:
        rows = ep["rows"]
        li = [label_index[r["label"]] for r in rows]
        corr = corr_all[np.ix_(li, li)]
        for arm in args.arms:
            if (arm, ep["line"], ep["menu"]) in done:
                continue
            world = "simple" if arm in ("A", "C", "noneA") else "state"
            mean, sd = np.array(ep["prior"][world]["mean"]), np.array(ep["prior"][world]["sd"])
            version = digest({"world": world, "line": ep["line"], "menu": ep["menu"], "mean": ep["prior"][world]["mean"]})
            if arm in ("C", "D"):
                if not protocol["llm_arms_enabled"]:
                    continue
                from agent_llm import LLMAcquisition
                if client is None:
                    from agent.llm import DeepSeekChatClient, MAESTROSettings
                    client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
                cands = [{"drug": r["drug"], "dose_uM": r["dose_uM"], "targets": r.get("targets"), "moa": r.get("moa"),
                          "prior_mean": float(mm)} for r, mm in zip(rows, mean)]
                policy = LLMAcquisition(client, ep["cell"], cands, protocol["design"]["m"], out / f"llm_{arm}.jsonl")
                name = "llm"
            elif arm.startswith("none"):
                policy, name = ap.choose_none, "none"
            else:
                policy, name = ap.choose_kg, "kg"
            res = run_arm(arm, ep["line"], ep["menu"], rows, mean, sd, corr, tuple(ep["obs"]), protocol["design"]["k"],
                          protocol["design"]["m"], policy, out / arm, version, name)
            if name == "llm":
                res["llm_receipts"] = policy.receipts
            with results_path.open("a", encoding="utf-8") as h:
                h.write(json.dumps(res) + "\n")
            print(json.dumps({k: res[k] for k in ("arm", "line", "menu", "V", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
