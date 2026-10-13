"""Small matched DeepSeek reasoning pilot; never passes unacquired outcomes to the LLM."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import os
import threading
import time

import numpy as np
from experiment import HERE, ROOT, interval, score_choices, write
from agent.case_store import CaseStore, MeasurementResult
from agent.llm import DeepSeekChatClient, MAESTROSettings, LLMError
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
from tools.evaluation.costs import SpendLedger

SOURCES = {
    "S1": "PRESAGE doi:10.1101/2025.06.03.657653: measured cross-system perturbations can transfer; source choice matters.",
    "S2": "Systema doi:10.1038/s41587-025-02777-8: shared systematic response may inflate prediction quality.",
    "S3": "GeneAgent doi:10.1038/s41592-025-02748-6: database verification supports functional descriptions, not causal proof.",
    "S4": "Repurposing Hub/MAP annotations are weaker than measured responses; tissue-specific target dependence is not established here.",
    "S5": "Activity is a vehicle-norm threshold in L1000, NOT viability. Two different activity labels do not establish a mechanism.",
}
TISSUES = {"A375": "melanoma", "HA1E": "immortalized kidney", "HELA": "cervical cancer",
           "HT29": "colorectal cancer", "MCF7": "breast cancer, ER+", "PC3": "prostate cancer, AR-", "YAPC": "pancreatic cancer"}
LOCK = threading.Lock()


class Provider:
    def __init__(self):
        os.environ["MAESTRO_LOG_DIRECTORY"] = str(HERE / "provider_logs")
        settings = MAESTROSettings.from_workspace(ROOT)
        if settings.chat_model != "deepseek-flash":
            raise ValueError("UNAUTHORIZED_MODEL")
        self.settings = replace(settings, timeout_seconds=45, max_tokens=1400)
        self.ledger = SpendLedger.load(HERE / "api_ledger.json", ceiling_usd=1.)
        self.pending = 0.

    def ask(self, name, messages):
        key = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        path = HERE / "llm_cache" / (key + ".json")
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            return json.loads(path.read_text())
        with LOCK:
            self.ledger.reserve(name, self.pending + .01)
            self.pending += .01
        usage, error, obj = {}, None, None
        try:
            obj, response = DeepSeekChatClient(self.settings).complete_json(messages, max_tokens=1400)
            usage = {**response.usage, "model": response.model}
        except LLMError as exc:
            error = getattr(exc, "code", type(exc).__name__)
        with LOCK:
            self.pending -= .01
            self.ledger.charge(name, usage, status="failed" if error else "ok", reserved_usd=.01,
                note="Flash usage retained; historical deepseek-chat rates are inapplicable. $0.01/call budget estimate, not invoice.")
            self.ledger.write()
        rec = {"key": key, "object": obj, "error": error, "usage": usage}
        path.write_text(json.dumps({**rec, "messages": messages}, indent=2), encoding="utf-8")
        return rec


def archive_observations(store, case, indices, lines, z, meta, stage):
    actions = [EvidenceAction(identifier=f"{stage}:{i}:{t}", description="Retrieve recorded L1000 profile",
        cost=1., distinguishes=("context_dependent_activity", "shared_activity"),
        kind=EvidenceActionKind.EVIDENCE_REVIEW, context_bound=False, time_hours=24,
        expected_conditions={"dose": "10 uM", "line": meta["lines"][t]}) for i,t in zip(indices, lines)]
    recorded = set(store.recorded_action_identifiers(case))
    if all(action.identifier in recorded for action in actions):
        return
    plan = store.record_plan(case, actions, ready_to_measure=True, context_identifier=None)
    for action, i, t in zip(actions, indices, lines):
        store.import_measurement(case, MeasurementResult(action_identifier=action.identifier,
            statement="Recorded L1000 landmark response norm divided by vehicle threshold",
            source_id="GSE70138:BlockQ:development-exposed", context_identifier=None,
            time_hours=24, independent_units=None, quality_passed=True,
            conditions={"dose": "10 uM", "line": meta["lines"][t]},
            metrics={"norm_ratio": str(float(z["ratio"][i,t]))},
            evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
            limitations=("Processed consensus; independent culture count unknown; no new laboratory experiment",),
            result_id=case+":"+action.identifier, plan_version=plan.plan_version))


def run_batch(provider, arm, batch, ids, z, meta):
    case = f"{arm}:{batch}"
    folder = HERE / "agent_traces"
    folder.mkdir(exist_ok=True)
    completed = folder / f"{arm}_{batch}.json"
    if completed.exists():
        return json.loads(completed.read_text())
    integrated = arm != "D_conventional"
    style = ("Form competing biological explanations, identify evidence gaps and source IDs. After observed feedback, revise your hypotheses and select discriminating observations. Treat VC disagreement as a question, not a cause. Preserve a concise research memory."
             if integrated else "Use the supplied scientific knowledge and virtual-cell tool results to investigate the compounds and choose useful follow-up observations. Keep concise notes between stages.")
    system = ("You are a scientific research agent. " + style +
        " Objective: maximize the number of compounds with one recorded active and one inactive line in two profile retrievals each. "
        "The first line is fixed by transfer coverage. Choose exactly one different available second line per compound after the first observation. "
        "All numeric optimization, outcome scoring and budgets are external. Never claim viability or causality. Return JSON only.")
    library = [{"id": str(i), **meta["compounds"][i], "available_lines": [meta["lines"][t] for t in np.flatnonzero(z["grid"][i])],
                "first_line": meta["lines"][int(z["first"][i])]} for i in ids]
    initial = {"sources": SOURCES, "tissues": TISSUES, "compounds": library,
               "task": "Before seeing feedback, give two competing explanations for this batch and note evidence gaps. Return {hypotheses: [...], evidence_gaps: [...], memory: string}. Maximum 250 words."}
    messages = [{"role":"system","content":system},{"role":"user","content":json.dumps(initial)}]
    pre = provider.ask(case+":hypotheses", messages)
    store = CaseStore(HERE / "case_state.sqlite")
    store.open_case(case, budget=2*len(ids))
    archive_observations(store, case, ids, z["first"][ids], z, meta, "first")
    feedback = []
    for i in ids:
        s = int(z["first"][i])
        raw = z["truth"][i,s]
        order = np.argsort(raw)
        candidates = []
        for t in np.flatnonzero(z["grid"][i]):
            if t == s:
                continue
            item = {"line":meta["lines"][t], "empirical_p_active":round(float(z["p_emp"][i,t]),4),
                    "norm_neighbour_p_active":round(float(z["p_knn"][i,t]),4)}
            if arm != "C_agent_only":
                item.update(rkt_p_active=round(float(z["p_rkt"][i,t]),4),
                            rkt_expected_cosine_if_active=round(float(z["expected"][i,t]),4),
                            rkt_specific_refusal=bool(z["refusal"][i,t]))
            candidates.append(item)
        feedback.append({"id":str(i), "observed_line":meta["lines"][s],
            "observed_norm_ratio":round(float(z["ratio"][i,s]),4),
            "observed_active":bool(z["ratio"][i,s]>1),
            "up_landmarks":z["genes"][order[-4:][::-1]].tolist(),
            "down_landmarks":z["genes"][order[:4]].tolist(), "candidates":candidates})
    messages += [{"role":"assistant","content":json.dumps(pre["object"] or {"error":pre["error"]})},
                 {"role":"user","content":json.dumps({"feedback":feedback,
                  "task":"Revise your research memory using observed feedback. Choose one second line for every id. Return {choices: [{id: string, line: string, reason: string, source_ids: [string]}], revised_memory: string, unresolved: [string]}. Reasons <=20 words each."})}]
    post = provider.ask(case+":feedback", messages)
    proposed = {}
    obj = post["object"] or {}
    for choice in obj.get("choices", []):
        if isinstance(choice, dict):
            proposed[str(choice.get("id"))] = choice.get("line")
    chosen, fallbacks = [], []
    for i in ids:
        label = proposed.get(str(i))
        t = meta["lines"].index(label) if label in meta["lines"] else -1
        if t < 0 or not z["grid"][i,t] or t == z["first"][i]:
            p = z["p_emp"][i]
            t = int(np.nanargmax(1-p if z["ratio"][i,z["first"][i]]>1 else p))
            fallbacks.append(i)
        chosen.append(t)
    # Save action choices before any second outcome is read by the adjudicator.
    choice_record = {"arm":arm,"batch":batch,"indices":ids,"second":chosen,"fallbacks":fallbacks,
                     "initial":pre,"revision":post}
    (folder / f"{arm}_{batch}_choices.json").write_text(json.dumps(choice_record,indent=2),encoding="utf-8")
    archive_observations(store, case, ids, chosen, z, meta, "second")
    first = z["first"][ids]
    hits, robust = score_choices(z["ratio"][ids], first, np.array(chosen))
    choice_record.update(hits=hits.astype(int).tolist(), margin_hits=robust.astype(int).tolist(),
        spent_slots=store.snapshot(case).spent)
    store.record_decision(case, status="deferred")
    completed.write_text(json.dumps(choice_record,indent=2),encoding="utf-8")
    print(case, "hits",int(hits.sum()),"fallbacks",len(fallbacks),flush=True)
    return choice_record


def main():
    results = json.loads((HERE / "RESULTS.json").read_text())
    if not results["pilot_gate_passed"]:
        raise ValueError("FEASIBILITY_GATE_FAILED")
    t0 = time.perf_counter()
    z = dict(np.load(HERE / "replay.npz"))
    meta = json.loads((HERE / "metadata.json").read_text())
    provider = Provider()
    jobs = [(arm,b,meta["pilot"][b*7:(b+1)*7]) for b in range(12)
            for arm in ("C_agent_only","D_conventional","E_integrated")]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run_batch,provider,a,b,ids,z,meta) for a,b,ids in jobs]
        records = [f.result() for f in futures]
    write("agent_results.json", {"records": records, "runtime_seconds":time.perf_counter()-t0})


if __name__ == "__main__":
    main()
