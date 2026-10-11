"""Independent ledger arithmetic, access restrictions, and outcome-poisoning checks."""
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import campaign as C
import run as R

HERE = Path(__file__).resolve().parent


def guard_checks(library, data, cfg):
    groups = {role: {d[0].drug for d in data if d[0].role == role}
              for role in ("development", "confirmation")}
    reference = set(library.drug)
    assert not reference & groups["development"]
    assert not reference & groups["confirmation"]
    assert not groups["development"] & groups["confirmation"]
    assert not set(library.discovery) & set(library.targets)
    changed = 0
    cases = [d for d in data if d[0].role == "development"][:8]
    for query, primary, secondary in cases:
        source_pool = library.pool(query)
        assert query.drug not in set(library.drug[source_pool])
        assert query.moa not in set(library.moa[source_pool])
        p0 = C.ParticlePosterior(library, query, **cfg)
        predicted0, first0 = p0.predict(), p0.choose()
        poisoned = primary.copy()
        poisoned[query.targets] = 1e6 + np.arange(len(query.targets))
        clean = C.MeasuredEnvironment(library, query, primary, secondary)
        dirty = C.MeasuredEnvironment(library, query, poisoned, -secondary)
        _, ledger0 = C.run_policy(library, query, clean, "adaptive_dual", cfg)
        _, ledger1 = C.run_policy(library, query, dirty, "adaptive_dual", cfg)
        assert ledger0[-1]["purchases"] == ledger1[-1]["purchases"]
        assert ledger0[-1]["prediction"] == ledger1[-1]["prediction"]
        p1 = C.ParticlePosterior(library, query, **cfg)
        assert np.array_equal(predicted0, p1.predict()) and first0 == p1.choose()
        line = first0[0]
        p0.observe(line, float(primary[line]))
        p1.observe(line, float(primary[line] + 4))
        changed += int(p0.choose()[0] != p1.choose()[0])
        assert not np.array_equal(p0.predict(), p1.predict())
    if changed == 0:
        raise AssertionError("No evidence that action order depends on an acquired value")
    return {"n_development_cases": len(cases), "changed_second_actions": changed,
            "terminal_poisoning_trace_invariance": True, "initial_hidden_outcome_invariance": True,
            "source_class_exclusion": True, "disjoint_roles": True}


def verify_ledger(prefix, library, data):
    frame = pd.read_csv(HERE / f"{prefix}_ROWS.csv")
    frame = frame[frame.budget == 16].set_index(["drug", "arm"])
    lookup = {datum[0].drug: datum for datum in data}
    n = 0
    maximum = 0.0
    with (HERE / f"{prefix}_LEDGER.jsonl").open(encoding="utf-8") as stream:
        for raw in stream:
            ledger = json.loads(raw)
            query, primary, secondary = lookup[ledger["drug"]]
            lines = [int(p["line"]) for p in ledger["purchases"]]
            assert len(set(lines)) == len(lines) and len(lines) <= 16
            assert set(lines).issubset(query.menu) and not set(lines) & set(query.targets)
            prediction = np.array(ledger["prediction"])
            truth = primary[query.targets]
            b = library.basis[query.targets]
            # Independent least-squares arithmetic from source truth, no policy scoring call.
            residual = truth - b @ np.linalg.lstsq(b, truth, rcond=None)[0]
            assert np.allclose(residual, ledger["truth"], atol=1e-10)
            selected = np.argsort(prediction, kind="stable")[:10]
            utility = -residual[selected].mean()
            hits = set(np.argsort(residual, kind="stable")[:max(1, round(0.1 * len(residual)))])
            precision = np.mean([int(i) in hits for i in selected])
            row = frame.loc[(ledger["drug"], ledger["arm"])]
            maximum = max(maximum, abs(utility - row.utility), abs(precision - row.precision))
            assert maximum < 1e-10
            expected_selection = [str(library.lines[query.targets[j]]) for j in selected]
            assert expected_selection == ledger["selected"]
            if ledger["arm"] != "adaptive_feedback_shuffle":
                assert all(abs(p["observed"] - primary[p["line"]]) < 1e-12 for p in ledger["purchases"])
            else:
                expected = C.MeasuredEnvironment(library, query, primary, secondary, True)
                assert all(abs(p["observed"] - expected._feedback[p["line"]]) < 1e-12 for p in ledger["purchases"])
            n += 1
    return {"n_terminal_ledgers": n, "max_metric_error": maximum,
            "purchase_restrictions": True, "truthful_feedback_except_declared_shuffle": True}


def outcome_shuffle(prefix):
    records = [json.loads(raw) for raw in (HERE / f"{prefix}_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()]
    baseline = json.loads(R.CONFIG.read_text(encoding="utf-8"))["best_fixed"]
    arm_records = {arm: {r["drug"]: r for r in records if r["arm"] == arm}
                   for arm in ("adaptive_dual", baseline)}
    units = sorted(arm_records["adaptive_dual"])
    perm = np.random.default_rng(C.SEED + 32).permutation(len(units))
    differences = []
    for drug, other in zip(units, [units[int(i)] for i in perm]):
        donor = arm_records["adaptive_dual"][other]
        outcomes = dict(zip(donor["target_lines"], donor["truth"]))
        utilities = []
        for arm in ("adaptive_dual", baseline):
            selected = arm_records[arm][drug]["selected"]
            values = [outcomes[line] for line in selected if line in outcomes]
            utilities.append(-np.mean(values) if len(values) >= 5 else np.nan)
        differences.append(utilities[0] - utilities[1])
    return {"scope": "Frozen terminal choices scored on a different compound's recorded residuals; diagnostic only.",
            **R.paired_statistics(np.array(differences), units, C.SEED + 33)}


def main():
    with threadpool_limits(limits=1):
        C.verify_sources()
        frozen = R.verify_execution()
        library, data = C.load_data()
        report = {"source_hashes_match": True, "execution_hashes_match": True,
                  "guards": guard_checks(library, data, frozen["parameters"]),
                  "ledger": verify_ledger("TEST", library, data),
                  "outcome_shuffle_diagnostic": outcome_shuffle("TEST")}
        R.dump(HERE / "VERIFIED.json", report)
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
