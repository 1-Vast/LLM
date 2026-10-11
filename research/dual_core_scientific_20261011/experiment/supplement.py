"""Frozen secondary comparator: one batch, with the identical particle posterior."""
import datetime
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import campaign as C
import run as R

HERE = Path(__file__).resolve().parent


def plan_batch(posterior):
    """Gaussian-moment batch design from exactly this particle prior, without outcomes."""
    q = posterior.query
    w = posterior.w
    Rt, Rc = posterior.Rt, posterior.Rc
    terminal_mean = posterior.predict()
    observation = Rc + posterior.nuisance_mean @ posterior.Bc.T
    observed_mean = w @ observation
    target_centered = Rt - terminal_mean
    observation_centered = observation - observed_mean
    cross = target_centered.T @ (w[:, None] * observation_centered)
    covariance = observation_centered.T @ (w[:, None] * observation_centered)
    covariance += posterior.Bc @ posterior.nuisance_cov @ posterior.Bc.T
    plan = []
    values = []
    for _ in range(16):
        variance = np.diag(covariance) + posterior.sigma ** 2
        evsi = C.knowledge_gradient(terminal_mean, cross, variance)
        evsi[plan] = -np.inf
        index = int(np.argmax(evsi))
        values.append(float(evsi[index]))
        plan.append(index)
        factor = covariance[:, index].copy()
        target_factor = cross[:, index].copy()
        cross -= np.outer(target_factor, factor) / variance[index]
        covariance -= np.outer(factor, factor) / variance[index]
    return [int(q.menu[index]) for index in plan], values


def run_one(library, datum, cfg):
    start = time.perf_counter()
    query, primary, secondary = datum
    posterior = C.ParticlePosterior(library, query, **cfg)
    plan, evsi = plan_batch(posterior)
    environment = C.MeasuredEnvironment(library, query, primary, secondary)
    rows, ledgers = [], []
    for step, (line, value) in enumerate(zip(plan, evsi), start=1):
        outcome = environment.measure(line, value)
        posterior.observe(line, outcome)
        if step in C.BUDGETS:
            score, ledger = environment.score(posterior.predict())
            rows.append(dict(score, drug=query.drug, moa=query.moa, role=query.role,
                             arm="batch_particle_kg", budget=step, spent=step,
                             rounds=1, seconds=time.perf_counter() - start))
            ledgers.append(dict(ledger, drug=query.drug, moa=query.moa, arm="batch_particle_kg", budget=step))
    return rows, ledgers


def main():
    frozen = R.verify_execution()
    freeze_path = HERE / "SUPPLEMENT_FREEZE.json"
    if not freeze_path.exists():
        R.dump(freeze_path, {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "scope": "Added after primary algorithm freeze while primary test was executing, before reading any test outcome values or metrics.",
               "sha256": {name: C.sha256(HERE / name) for name in ("SUPPLEMENT_PROTOCOL.json", "supplement.py", "CALIBRATION_FREEZE.json")}})
    receipt = json.loads(freeze_path.read_text(encoding="utf-8"))
    for name, expected in receipt["sha256"].items():
        assert C.sha256(HERE / name) == expected
    if (HERE / "SUPPLEMENT_ROWS.csv").exists():
        raise RuntimeError("SUPPLEMENT_ALREADY_EXECUTED")
    with threadpool_limits(limits=1):
        library, data = C.load_data()
        rows = []
        start = time.perf_counter()
        with (HERE / "SUPPLEMENT_LEDGER.jsonl").open("w", encoding="utf-8") as stream:
            for index, datum in enumerate(data):
                result, ledgers = run_one(library, datum, frozen["parameters"])
                rows.extend(result)
                stream.write(json.dumps(ledgers[-1], allow_nan=False) + "\n")
                if index % 50 == 0:
                    print(f"same-posterior batch {index}/{len(data)} seconds={time.perf_counter() - start:.1f}", flush=True)
        pd.DataFrame(rows).to_csv(HERE / "SUPPLEMENT_ROWS.csv", index=False)
        R.dump(HERE / "SUPPLEMENT_RECEIPT.json", {"n_campaigns": len(data), "seconds": time.perf_counter() - start,
               "rows_sha256": C.sha256(HERE / "SUPPLEMENT_ROWS.csv"), "ledger_sha256": C.sha256(HERE / "SUPPLEMENT_LEDGER.jsonl"),
               "freeze_sha256": C.sha256(freeze_path), "llm_api_calls": 0})


if __name__ == "__main__":
    main()
