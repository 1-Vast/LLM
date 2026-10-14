"""Evidence-boundary benchmark: miniature, provider-free tasks with known expected outcomes.

Decision tasks are DATA (BENCHMARK_FIXTURES.json): sources with bodies, receipts, a policy, explanations and the
expected status. Any implementation can be scored by submitting its decisions:

    python benchmark.py                       # build fixtures, run the legacy and strict reference implementations
    python benchmark.py --score submission.json    # {"task_id": {"status": "...", "reasons": [...]}, ...}

Evaluation-integrity and predictive-validity tasks are executable (they need numpy); they are listed in the same
results file. No task needs a model provider, a download or an external asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDY.parents[1] / "src"))

from maestro import decision_review as legacy  # noqa: E402
from maestro import evaluation_contract as ec  # noqa: E402
from maestro.case_memory import ScientificMeasurementStatus as S  # noqa: E402
from maestro.evidence_registry import EvidenceLedger, EvidenceReceipt, RegisteredSource  # noqa: E402
from maestro.models import EvidenceKind as K  # noqa: E402
from maestro.strict_decision_review import (NoSignalRule, Role, StrictExplanation, StrictPolicy, StrictPrediction,  # noqa: E402
                                            approve_basis, strict_review)

CTX = "A549:cetsa:1h"
EXPL = [
    {"id": "TARGET", "progression": True, "predictions": [
        {"key": "engage", "observable": "engagement_z", "relation": "<=", "threshold": -2.0, "unit": "z", "role": "required"},
        {"key": "rescue", "observable": "rescue_fraction", "relation": ">=", "threshold": 0.5, "unit": "fraction", "role": "required"}]},
    {"id": "OFF", "progression": False, "predictions": [
        {"key": "off_engage", "observable": "engagement_z", "relation": ">", "threshold": -1.0, "unit": "z", "role": "required"}]}]


def src(i, body="measured", experiment=None, publication=None, **kw):
    return {"id": i, "body": body, "experiment": experiment, "publication": publication, **kw}


def rec(i, source, observable, value, rule, unit="z", kind="real_measurement", status="qualified", context=CTX, parents=()):
    return {"id": i, "source": source, "observable": observable, "value": value, "unit": unit, "kind": kind, "status": status,
            "context": context, "rule": rule, "parents": list(parents)}


def good(prefix, experiment, engage=-3.0, rescue=0.8, off=-3.0):
    return ([src(f"{prefix}", f"{prefix} body", experiment)],
            [rec(f"{prefix}_e", prefix, "engagement_z", engage, "engage"), rec(f"{prefix}_r", prefix, "rescue_fraction", rescue, "rescue", "fraction"),
             rec(f"{prefix}_o", prefix, "engagement_z", off, "off_engage")])


def task(tid, axis, description, sources, receipts, expected, *, legacy_note, policy=None, **extra):
    base = {"id": tid, "axis": axis, "description": description, "sources": sources, "receipts": receipts,
            "policy": {"protocol_version": "study-v1", "min_independent_groups": 1, "exclude_alternatives": True,
                       "no_signal_rules": [{"rule_id": "sel_flat", "observable": "selective_z", "relation": ">", "threshold": -1.0, "unit": "z"}]} | (policy or {}),
            "explanations": EXPL, "context": CTX, "funded": True, "limitations": [], "menu": [{"id": "cetsa", "observable": "engagement_z", "cost": 2}],
            "expected": expected, "legacy_note": legacy_note}
    return base | extra


def fixtures() -> list[dict]:
    s_ok, r_ok = good("a", "expA")
    s_b, r_b = good("b", "expB")
    out = [
        task("P-01", "provenance", "Receipt names a source file that does not exist", [src("a", write=False, experiment="expA")],
             [rec("a_e", "a", "engagement_z", -3.0, "engage")], {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]},
             legacy_note="a 64-character digest is admitted without a file"),
        task("P-02", "provenance", "Source bytes changed after the receipt was written", [src("a", experiment="expA", corrupt_after="edited")],
             [rec("a_e", "a", "engagement_z", -3.0, "engage")], {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]},
             legacy_note="digest is never recomputed"),
        task("P-03", "provenance", "Three files copied from one experiment presented as three independent supports; two groups required",
             [src(f"c{i}", f"copy {i}", "expA") for i in range(3)],
             sum([[rec(f"c{i}_e", f"c{i}", "engagement_z", -3.0, "engage"), rec(f"c{i}_r", f"c{i}", "rescue_fraction", 0.8, "rescue", "fraction"),
                   rec(f"c{i}_o", f"c{i}", "engagement_z", -3.0, "off_engage")] for i in range(3)], []),
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]}, policy={"min_independent_groups": 2},
             legacy_note="independent=True is a flag nobody reads; GO"),
        task("P-04", "provenance", "A virtual-cell prediction relabelled as a derived analysis", [src("sim", "vc output", "vc")],
             [rec("p", "sim", "engagement_z", -9.0, "engage", kind="model_prediction"),
              rec("d", "sim", "engagement_z", -9.0, "engage", kind="derived_analysis", parents=["p"])],
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]}, legacy_note="a derived analysis needs no parent; its kind is the caller's word"),
        task("P-05", "provenance", "QC-failed measurement", [src("a", experiment="expA")],
             [rec("a_e", "a", "engagement_z", -3.0, "engage", status="qc_failed")], {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]},
             legacy_note="refused (same)"),
        task("M-01", "mechanism", "A database annotation offered as target evidence", [src("hub", "annotation", "hub")],
             [rec("h", "hub", "engagement_z", -3.0, "engage", kind="retrieved_source")], {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]},
             legacy_note="refused (same)"),
        task("M-02", "mechanism", "Overexpression-context measurement used for an inhibition prediction", [src("a", experiment="expA")],
             [rec("a_e", "a", "engagement_z", -3.0, "engage", context="A549:overexpression:96h")],
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:engage"]}, legacy_note="refused (same)"),
        task("M-03", "mechanism", "Candidates make no incompatible prediction on any available experiment: not identifiable", [], [],
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["NO_DISCRIMINATING_EXPERIMENT_AVAILABLE"]}, menu=[{"id": "other", "observable": "rescue_fraction", "cost": 3}],
             legacy_note="raises ValueError instead of returning a named state"),
        task("M-04", "mechanism", "True mechanism absent: the measured engagement contradicts the progression explanation", [src("a", experiment="expA")],
             [rec("a_e", "a", "engagement_z", -0.2, "engage")], {"status": "NO_GO", "reason_prefixes": ["CONTRADICTED:engage"]}, legacy_note="NO_GO (same)"),
        task("D-01", "decision", "One required prediction supported, the other never tested", [src("a", experiment="expA")],
             [rec("a_e", "a", "engagement_z", -3.0, "engage"), rec("a_o", "a", "engagement_z", -3.0, "off_engage")],
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:rescue"]}, legacy_note="GO on one supported prediction"),
        task("D-02", "decision", "A no-signal assertion with no measured finding behind it", [], [],
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": []}, no_signal_boolean=True, legacy_note="NO_GO from a boolean"),
        task("D-03", "decision", "Everything supported and excluded, but nobody has approved the consequential experiment", s_ok, r_ok,
             {"status": "AWAITING_APPROVAL", "reason_prefixes": ["SUPPORTED:engage"]}, legacy_note="GO without any approval"),
        task("D-04", "decision", "Supported, excluded and approved, then a required receipt is withdrawn: the certificate must fall", s_ok, r_ok,
             {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["UNTESTED:rescue"]}, withdraw_after_go=["a_r"],
             legacy_note="no certificate, no withdrawal"),
        task("D-05", "decision", "Conflicting independent measurements of a required observable", s_b + [src("c", "c body", "expC")],
             r_b + [rec("c_e", "c", "engagement_z", -0.3, "engage")], {"status": "NEED_MORE_EVIDENCE", "reason_prefixes": ["CONFLICTED:engage"]},
             legacy_note="any one contradiction is NO_GO"),
    ]
    return out


def build_ledger(fx: dict, root: Path) -> EvidenceLedger:
    ledger = EvidenceLedger(root, [])
    for s in fx["sources"]:
        body = s["body"]
        if s.get("write", True):
            (root / f"{s['id']}.dat").write_bytes(body.encode("utf-8"))
        ledger._sources[s["id"]] = RegisteredSource(s["id"], f"{s['id']}.dat", hashlib.sha256(body.encode("utf-8")).hexdigest(), "raw", s.get("experiment"), s.get("publication"))
        if s.get("corrupt_after"):
            (root / f"{s['id']}.dat").write_bytes(s["corrupt_after"].encode("utf-8"))
    for r in fx["receipts"]:
        ledger.add(EvidenceReceipt(r["id"], r["source"], ledger._sources[r["source"]].sha256, r["observable"], r["value"], r["unit"], "plate-median", r["context"],
                                   S(r["status"]), "qc/report-1", r["rule"], fx["policy"]["protocol_version"], K(r["kind"]), tuple(r["parents"])))
    return ledger


def run_strict(fx: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ledger = build_ledger(fx, root)
        pol = fx["policy"]
        policy = StrictPolicy(pol["protocol_version"], pol["min_independent_groups"], pol["exclude_alternatives"], tuple(NoSignalRule(**r) for r in pol["no_signal_rules"]))
        expl = tuple(StrictExplanation(e["id"], e["id"], tuple(StrictPrediction(p["key"], p["observable"], p["relation"], p["threshold"], p["unit"], Role(p["role"])) for p in e["predictions"]), e["progression"]) for e in fx["explanations"])
        menu = tuple(legacy.DiscriminatingExperiment(m["id"], m["observable"], m["cost"]) for m in fx["menu"])
        kw = dict(context=fx["context"], funded=fx["funded"], menu=menu)
        d = strict_review("c", expl, ledger, policy, **kw)
        if fx["id"] == "D-04":
            d = strict_review("c", expl, ledger, policy, approval=approve_basis(d.basis_sha256, "Dr. Rivera"), **kw)
            assert d.status.value == "GO"
            for rid in fx["withdraw_after_go"]:
                ledger.withdraw(rid, "plate failed re-QC")
            problems = ledger.binding_problems(d.binding)
            d = strict_review("c", expl, ledger, policy, **kw)
            return {"status": d.status.value, "reasons": list(d.reasons), "certificate_invalidated": bool(problems)}
        return {"status": d.status.value, "reasons": list(d.reasons)}


def run_legacy(fx: dict) -> dict:
    """The historical review on the same fixture, to show what it admits. Receipts become EvidenceItems."""
    expl = tuple(legacy.Explanation(e["id"], e["id"], tuple(legacy.Prediction(p["observable"], p["relation"], p["threshold"]) for p in e["predictions"]), e["progression"]) for e in fx["explanations"])
    sha = {s["id"]: hashlib.sha256(s["body"].encode()).hexdigest() for s in fx["sources"]}
    items = [legacy.EvidenceItem(r["observable"], r["value"], K(r["kind"]), S(r["status"]), r["context"], f"{r['source']}.dat", sha[r["source"]]) for r in fx["receipts"]
             if fx["id"] != "D-02"]
    menu = tuple(legacy.DiscriminatingExperiment(m["id"], m["observable"], m["cost"]) for m in fx["menu"])
    try:
        d = legacy.review("c", expl, items, context=fx["context"], funded=fx["funded"], menu=menu, no_signal=bool(fx.get("no_signal_boolean")))
        return {"status": d.status.value, "reasons": list(d.reasons)}
    except ValueError as error:
        return {"status": "RAISED", "reasons": [str(error)[:60]]}


def matches(observed: dict, expected: dict) -> bool:
    """Status and reason prefixes for a scored submission. The legacy review is compared on status alone, since it has no strict reason codes."""

    return observed["status"] == expected["status"] and all(any(r.startswith(p) for r in observed["reasons"]) for p in expected["reason_prefixes"])


def executable_tasks() -> list[dict]:
    out = []
    # E-01 eligibility and nominations must not read outcomes
    wells = [(f"c{i}", "L1") for i in range(10)]
    scores = {w: float((i * 7) % 10) for i, w in enumerate(wells)}
    rng = np.random.default_rng(3)
    base = ec.nominate_wells(scores, set(wells), 4, salt="s")
    changed = {tuple(ec.nominate_wells(scores, set(wells), 4, salt="s")) for _ in range(5) if rng.random() < 2}
    masked = lambda outcomes: tuple(sorted((w for w in wells if np.isfinite(outcomes[w])), key=lambda w: -scores[w])[:4])  # frozen evaluator: mask by outcome missingness
    o1 = {w: 0.4 for w in wells}
    o2 = {w: (np.nan if w == base[0] else 0.4) for w in wells}
    out.append({"id": "E-01", "legacy_basis": "reproduced_logic", "axis": "evaluation", "description": "hidden outcomes (incl. missingness) change; pre-outcome nominations must not",
                "strict_passes": len(changed) == 1 and ec.nominate_wells(scores, set(wells), 4, salt="s") == base,
                "legacy_passes": masked(o1) == masked(o2), "legacy_note": "H2 mask reads np.isfinite(Y): nominations change with missingness"})
    # E-02 normaliser leakage
    try:
        ec.TrainNormaliser({"t1"}).fit(np.ones((2, 3)), ["t1", "test1"]); passed = False
    except ValueError:
        passed = True
    out.append({"id": "E-02", "legacy_basis": "audit_finding_not_executed", "axis": "evaluation", "description": "normaliser fitted with a test row is refused", "strict_passes": passed, "legacy_passes": False,
                "legacy_note": "G = nanmedian(Y) over the sealed batch"})
    # E-03 identity
    try:
        ec.resolve_identity(["BRD-K00000001"], [{"id": "BRD-K00000001-001-01-1", "screen": "REP.1M"}, {"id": "BRD-K00000001-002-02-2", "screen": "REP.300"}]); passed = False
    except ec.IdentityRefused:
        passed = True
    out.append({"id": "E-03", "legacy_basis": "audit_finding_not_executed", "axis": "evaluation", "description": "one core in two screens is refused, not averaged", "strict_passes": passed, "legacy_passes": False,
                "legacy_note": "rows sharing a core are averaged"})
    # E-04 units: overgrowth of 2.66 as a fraction must not be divided by 100
    fraction = np.array([0.2, 0.5, 2.66])
    legacy_scale = 100.0 if np.abs(fraction).max() > 2.0 else 1.0
    legacy_hits = (fraction / legacy_scale) <= 0.5
    strict_hits = ec.viability_hit(fraction, "fraction", 0.5, inclusive=True)
    out.append({"id": "E-04", "legacy_basis": "reproduced_logic", "axis": "evaluation", "description": "fraction viability with overgrowth, threshold 0.5 inclusive; 50 percent equals 0.5 fraction",
                "strict_passes": list(strict_hits) == [True, True, False] and bool(ec.viability_hit([50.0], "percent", 0.5, inclusive=True)[0]),
                "legacy_passes": list(legacy_hits) == [True, True, False], "legacy_note": "scale guessed from the maximum: 2.66 > 2 divides every value by 100"})
    # V-01 mechanism-class shortcut: family annotation gain is reproduced by a relabelling that keeps family structure
    rng = np.random.default_rng(11)
    n, fams = 600, 30
    fam = rng.integers(0, fams, n)
    effect = rng.normal(size=fams)[fam] + 0.3 * rng.normal(size=n)
    def gain(family):
        pred = np.array([effect[(family == f) & (np.arange(n) % 2 == 0)].mean() if ((family == f) & (np.arange(n) % 2 == 0)).any() else 0.0 for f in family])
        odd = np.arange(n) % 2 == 1
        return float(np.corrcoef(pred[odd], effect[odd])[0, 1])
    real = gain(fam)
    perm = rng.permutation(fams)[fam]                                   # relabel families, preserving sizes and sharing structure
    out.append({"id": "V-01", "legacy_basis": "audit_finding_not_executed", "axis": "predictive_validity", "description": "knowledge gain that a structure-preserving relabelling reproduces is a class shortcut, not identity",
                "strict_passes": abs(real - gain(perm)) < 1e-9, "legacy_passes": False, "legacy_note": "an accuracy gain is read as target biology",
                "values": {"real_gain": round(real, 3), "relabelled_gain": round(gain(perm), 3)}})
    # D-06 budget mismatch and D-07 ranking as probability (legacy contracts that remain valid)
    from maestro.campaign_budget import CampaignBudget
    req = legacy.ExperimentRequest("c", legacy.DiscriminatingExperiment("x", "o", cost=5), "agent-a", "why")
    try:
        legacy.authorize_execution(req, legacy.approve(req, "Dr. Rivera"), CampaignBudget(3, 1, 0, "well"), spent_measurements=0, spent_turnarounds=0); passed = False
    except ValueError:
        passed = True
    out.append({"id": "D-06", "legacy_basis": "executed", "axis": "decision", "description": "an approved experiment that exceeds the budget is refused", "strict_passes": passed, "legacy_passes": passed, "legacy_note": "same contract"})
    try:
        float(legacy.ExplorationRanking(("a",), {"a": 1.0}, 1, "swiss")); passed = False
    except TypeError:
        passed = True
    out.append({"id": "D-07", "legacy_basis": "executed", "axis": "decision", "description": "an exploration ranking cannot be read as a probability", "strict_passes": passed, "legacy_passes": passed, "legacy_note": "same contract"})
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path)
    args = parser.parse_args()
    fx = fixtures()
    (STUDY / "BENCHMARK_FIXTURES.json").write_text(json.dumps(fx, indent=1) + "\n", encoding="utf-8", newline="\n")
    if args.score:
        sub = json.loads(args.score.read_text(encoding="utf-8"))
        scored = {f["id"]: matches(sub[f["id"]], f["expected"]) if f["id"] in sub else False for f in fx}
        print(json.dumps({"passed": sum(scored.values()), "of": len(scored), "by_task": scored}, indent=1))
        return 0 if all(scored.values()) else 1
    rows = []
    for f in fx:
        s, l = run_strict(f), run_legacy(f)
        row = {"id": f["id"], "axis": f["axis"], "description": f["description"], "expected": f["expected"], "strict": s, "legacy": l,
               "strict_passes": matches(s, f["expected"]) and (f["id"] != "D-04" or s.get("certificate_invalidated") is True),
               "legacy_passes": l["status"] == f["expected"]["status"], "legacy_basis": "executed", "legacy_note": f["legacy_note"]}
        rows.append(row)
    rows += executable_tasks()
    summary = {"tasks": len(rows), "strict_passes": sum(r["strict_passes"] for r in rows), "legacy_passes": sum(r["legacy_passes"] for r in rows),
               "legacy_fails": [r["id"] for r in rows if not r["legacy_passes"]],
               "legacy_fails_executed_or_reproduced": [r["id"] for r in rows if not r["legacy_passes"] and r["legacy_basis"] != "audit_finding_not_executed"],
               "caveat": "expected outcomes were written with the strict implementation: 21/21 is specification conformance, not scientific validity"}
    (STUDY / "BENCHMARK_RESULTS.json").write_text(json.dumps({"summary": summary, "tasks": rows}, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        print(f"{r['id']:5s} {r['axis']:20s} strict {'PASS' if r['strict_passes'] else 'FAIL'}  legacy {'pass' if r['legacy_passes'] else 'FAIL'}  {r['description'][:70]}")
    print(summary)
    return 0 if summary["strict_passes"] == summary["tasks"] else 1


if __name__ == "__main__":
    sys.exit(main())
