"""Write FREEZE.json (one time, before the final stage).  Hashes every file that the final run executes or that fixed a choice."""
import hashlib, json, sys, time
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import ptv_data as D

EXCLUDE_PY = {"make_freeze.py", "verify.py", "build_report.py"}
files = [p for p in HERE.glob("*.py") if p.name not in EXCLUDE_PY]
files += [HERE / n for n in ("PROTOCOL.md", "CENSUS.json", "SOURCE_MANIFEST.json")]
for sub in ("RUN/programs", "RUN/selection", "RUN/episodes", "RUN/sel_eval", "dev_scripts"):
    files += [p for p in (HERE / sub).rglob("*") if p.is_file()]
files += [HERE / "RUN" / "llm_ledger.jsonl"]
for sub in ("RUN/sel", "RUN/sel30", "RUN/dev"):
    files += [p for p in (HERE / sub).glob("*") if p.is_file()]
frozen = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}

res = {"gpu_s": 0.0, "cpu_s": 0.0}
for sub in ("dev", "sel", "sel30"):
    for j in (HERE / "RUN" / sub).glob("*.json"):
        r = json.loads(j.read_text())
        res["gpu_s" if "cuda" in r.get("device", "") else "cpu_s"] += r["seconds"]
led = [json.loads(l) for l in (HERE / "RUN" / "llm_ledger.jsonl").read_text().splitlines()]
fz = {
    "study": "dual_core_innovation_validation_20261021", "frozen_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "statement": "Protocol, code, programs, selection artefacts and episode caches are frozen. The final stage (7 held-out lineages) has not been opened; no final outcome was read.",
    "code_sha256": D.code_hash(), "frozen_files": frozen,
    "config": {"partition_salt": D.SALT, "partition": D.partition(), "pool_label_rate": [0.2, 0.8], "k_nomination": 5, "budget": 5.0, "lambda": 0.5,
               "world_models": {"hidden": 16, "lr": 5e-4, "batch": 32, "lambda_bce": 0.8, "weight_decay": 1e-4, "epochs": {"M1": 30, "M2": 30, "M3": 45}, "seeds": [0, 1], "primary_seed": 0},
               "M0": "logistic direct predictor", "C_star": "B1",
               "Q": {"support": 3, "update": {"steps": 10, "lr": 1e-4}, "kernel_kappa": 0.25},
               "A0": "static top-5 by W (kappa 0)", "search": {"generations": 3, "llm_requests_cap": 8, "llm_tokens_cap": 50000, "candidates_cap": 8},
               "margins": {"delta_T_prec5": 0.09, "delta_E_hits": 0.40}, "bootstrap": {"B": 10000, "seed": 20261021, "unit": "lineage, with multiplicity"},
               "llm_model": "deepseek-flash"},
    "pre_freeze_resources": {"gpu_seconds_model_training": round(res["gpu_s"]), "cpu_seconds_model_training": round(res["cpu_s"]), "llm_requests": len(led),
                             "llm_tokens": sum(r.get("total_tokens", 0) for r in led), "llm_failures": sum(r["outcome"] != "OK" for r in led)},
}
(HERE / "FREEZE.json").write_text(json.dumps(fz, indent=1), encoding="utf-8")
print(len(frozen), "files frozen;", fz["pre_freeze_resources"])
