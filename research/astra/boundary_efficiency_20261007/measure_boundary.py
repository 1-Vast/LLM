"""15-call same-public-input policy overhead comparison after canonical run completion."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import time
import tracemalloc
from types import SimpleNamespace

import numpy as np

from .benchmark import study

HERE = Path(__file__).resolve().parent
BOUNDARY = HERE.parent / "boundary_acquisition_20261007"


def main():
    summary = BOUNDARY / "run1/SUMMARY.json"
    if not summary.is_file():
        raise RuntimeError("Canonical replay must finish before timing")
    source = BOUNDARY / "method.py"
    spec = importlib.util.spec_from_file_location("timed_boundary_method", source)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    packet = BOUNDARY / "packet2/public_prior.npz"
    with np.load(packet, allow_pickle=False) as p:
        mean, covariance, noise = p["PANC_1__M2"], p["cov"], p["obsvar"]
    method.validate_inputs(mean, covariance, noise)
    belief = SimpleNamespace(mean=mean, cov=covariance, obs_var=noise)
    normals = np.random.default_rng(42).standard_normal(64)
    calls = {"old_KG64": lambda: (study.kg_values(belief, 5, range(146), normals), None),
             "analytic_boundary": lambda: method.boundary_scores(mean, covariance, noise, range(146))}
    results = {}
    for name, call in calls.items():
        reference, _ = call()
        assert all(np.isfinite(list(reference.values())))
        choice = max(reference, key=lambda i: (reference[i], -i))
        timings = []
        for _ in range(15):
            start = time.perf_counter()
            scores, _ = call()
            timings.append(time.perf_counter() - start)
            assert scores == reference
            assert max(scores, key=lambda i: (scores[i], -i)) == choice
        tracemalloc.start()
        call()
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        results[name] = dict(median_seconds=statistics.median(timings), samples=timings,
                             peak_python_bytes=peak, exact_repeat_scores=True, argmax=choice,
                             finite_scores=True)
    artifacts = [source, packet, summary, BOUNDARY / "PROTOCOL.json", BOUNDARY / "FREEZE.json"]
    output = dict(menu=146, flags=5, old_KG_draws=64, serial_calls=15, results=results,
                  source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
                  private_outcomes_read=False, policies_mathematically_different=True,
                  excludes="Database purchases, nested training, validation eigendecomposition, GPU and provider work")
    with (HERE / "BOUNDARY_BENCHMARK.json").open("x") as handle:
        json.dump(output, handle, indent=2)
    print(json.dumps({k:{x:y for x,y in v.items() if x != "samples"} for k,v in results.items()}))


if __name__ == "__main__":
    main()
