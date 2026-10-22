"""Collect the resource ledger and a compact machine-readable summary after the final run (reads stored results only)."""
import json
from pathlib import Path
HERE = Path(__file__).parent

tr = {"gpu_seconds": 0.0, "cpu_seconds": 0.0, "runs": {}}
for sub in ("dev", "sel", "sel30", "final"):
    n = g = c = 0
    for j in (HERE / "RUN" / sub).glob("*.json"):
        q = json.loads(j.read_text()); n += 1
        if q.get("device", "cpu").startswith("cuda"): g += q["seconds"]
        else: c += q["seconds"]
    tr["runs"][sub] = {"n": n, "gpu_seconds": round(g), "cpu_seconds": round(c)}
    tr["gpu_seconds"] += g; tr["cpu_seconds"] += c
rows = [json.loads(l) for l in (HERE / "RUN" / "llm_ledger.jsonl").read_text().splitlines()]
ev = {}
for sub in ("sel_eval", "final_eval"):
    p = HERE / "RUN" / sub / "RESULTS.json"
    if p.exists(): ev[sub] = json.loads(p.read_text())["wall_seconds"]
out = {"note": "No monetary prices are asserted. Units: GPU/CPU seconds measured per run record; molecular and functional units are reported separately in RESULTS.json; API tokens are provider-reported.",
       "model_training": {k: (round(v) if isinstance(v, float) else v) for k, v in tr.items()},
       "evaluation_wall_seconds": ev,
       "llm": {"requests": len(rows), "tokens": sum(r.get("total_tokens", 0) for r in rows), "failures": sum(r["outcome"] != "OK" for r in rows),
               "retries": "not separately observable through the maintained client; requests are logical requests", "model": "deepseek-flash", "caps": {"requests": 8, "tokens": 50000}},
       "hardware": "RTX 4060 Laptop 8 GB (CUDA 13, torch 2.11.0+cu128) for selection and final training; 28 CPU cores for dev-stage training (CPU torch) and program evaluation"}
(HERE / "RESOURCES.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
