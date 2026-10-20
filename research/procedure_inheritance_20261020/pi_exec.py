"""Official execution: all streams sequentially in ONE process and ONE numerical thread, then the transplant pass. Claims the stage ledger first (write-once).
`python pi_exec.py`                       the frozen evaluation (refuses without a valid freeze or if a stage was already claimed)
`python pi_exec.py --rehearsal OUT S1 S2` dress rehearsal of the same code path on non-evaluation seeds in OUT (no ledger, no freeze requirement; never reported as a result)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pi_freeze as FZ  # noqa: E402
import pi_run as R  # noqa: E402


def main(argv):
    cfg = json.loads((HERE / "CONFIG.json").read_text(encoding="utf-8"))
    kinds = cfg["streams"]["kinds"]
    if argv and argv[0] == "--rehearsal":
        run, seeds, official = Path(argv[1]), [int(argv[2]), int(argv[3])], False
    else:
        pr = FZ.check()
        if pr:
            raise SystemExit("freeze problems: " + "; ".join(pr))
        run, seeds, official = HERE / "RUN" / "eval", cfg["streams"]["seeds"], True
        FZ.claim_stage(HERE / "RUN", "eval", {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "streams": [f"{k}_{s}" for k in kinds for s in seeds]})
    t_wall, t_cpu = time.perf_counter(), time.process_time()
    per = {}
    for kind in kinds:
        for seed in seeds:
            t = time.perf_counter()
            R.run_stream(kind, seed, run)
            per[f"{kind}_{seed}"] = {"wall_s": time.perf_counter() - t}
            print(kind, seed, round(per[f"{kind}_{seed}"]["wall_s"], 1), "s", flush=True)
    if official:
        FZ.claim_stage(HERE / "RUN", "xplant", {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    for kind in kinds:
        R.run_xplant(kind, seeds[0], seeds[1], run)
        R.run_xplant(kind, seeds[1], seeds[0], run)
    res = {"total_wall_s": time.perf_counter() - t_wall, "total_process_cpu_s": time.process_time() - t_cpu, "elapsed_minutes": (time.perf_counter() - t_wall) / 60,
           "ceiling_minutes": cfg["budget"]["elapsed_minutes"], "numerical_threads": 1, "streams": per, "official": official}
    out = (HERE / "RUN" / "RESOURCES.json") if official else (run.parent / "RESOURCES.json")
    out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("done", round(res["elapsed_minutes"], 2), "min")


if __name__ == "__main__":
    main(sys.argv[1:])
