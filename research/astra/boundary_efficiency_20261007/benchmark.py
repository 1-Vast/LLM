"""Same public 146-candidate inputs; no evaluator-private reads or outcomes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import time
import tracemalloc
from types import SimpleNamespace

import numpy as np

from .kernel import gains, kg_values

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "decision_opportunity_20261007"
spec = importlib.util.spec_from_file_location("kg_predecessor", PRIOR / "run.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def measure(run):
    times = []
    for _ in range(21):
        start = time.perf_counter()
        run()
        times.append(time.perf_counter() - start)
    tracemalloc.start()
    run()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return dict(median_seconds=statistics.median(times), samples=times, peak_python_bytes=peak)


def main():
    path = PRIOR / "compact_packet2/public_prior.npz"
    normals = np.random.default_rng(42).standard_normal(64)
    with np.load(path, allow_pickle=False) as public:
        endpoint = "curated_transcript_projection"
        belief = SimpleNamespace(mean=public["PANC_1__" + endpoint + "__M2__B"],
                                 cov=public[endpoint + "__cov"], obs_var=public[endpoint + "__obsvar"])
    indices = list(range(146))
    before = study.kg_values(belief, 5, indices, normals)
    after = kg_values(belief, 5, indices, normals)
    assert before == after
    directions = np.array([belief.cov[:, i] / np.sqrt(belief.cov[i, i] + belief.obs_var[i]) for i in indices])
    results = {"baseline": measure(lambda: study.kg_values(belief, 5, indices, normals)),
               "batched": measure(lambda: kg_values(belief, 5, indices, normals)),
               "directions_only": measure(lambda: gains(belief.mean, directions, normals, 5))}
    record = dict(public_source=str(path), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  menu=146, draws=64, flags=5, exact_scores=True,
                  exact_choice=max(before, key=lambda i: (before[i], -i)), results=results,
                  private_outcomes_read=False, gpu_calls=0, provider_calls=0)
    with (HERE / "BENCHMARK_STREAM.json").open("x") as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps({name: {k:v for k,v in result.items() if k != "samples"} for name,result in results.items()}))


if __name__ == "__main__":
    main()
