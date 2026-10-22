"""Verification without retraining and without opening any further final outcome.  Reads FREEZE.json, STAGE_LEDGER.json, the LLM ledger, stored CSV/JSON results
and recomputes the reported contrasts, yields and resource sums.  Exit code 0 = every check passed.  usage: python verify.py"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd

fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("PASS " if ok else "FAIL ") + msg)


sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ---- 1. freeze integrity ------------------------------------------------------------------------------------------------------------------
fz = json.loads((HERE / "FREEZE.json").read_text())
changed = [n for n, h in fz["frozen_files"].items() if not (HERE / n).exists() or sha(HERE / n) != h]
check(not changed, f"all {len(fz['frozen_files'])} frozen files unchanged since the freeze" + (f" (changed: {changed[:3]})" if changed else ""))
led = json.loads((HERE / "STAGE_LEDGER.json").read_text()) if (HERE / "STAGE_LEDGER.json").exists() else []
fin = [e for e in led if e["stage"] == "final"]
check(len(fin) == 1, "final stage claimed exactly once")
if fin:
    check(fin[0]["freeze_sha256"] == sha(HERE / "FREEZE.json"), "stage ledger records the sha256 of the FREEZE.json in force")
check(len(led) == len({e["stage"] for e in led}), "stage ledger has no duplicate claims")

# ---- 2. LLM ledger vs caps and the freeze --------------------------------------------------------------------------------------------------
rows = [json.loads(l) for l in (HERE / "RUN" / "llm_ledger.jsonl").read_text().splitlines()]
tok = sum(r.get("total_tokens", 0) for r in rows)
check(len(rows) <= 8 and tok <= 50000, f"LLM requests {len(rows)} <= 8 and tokens {tok} <= 50000")
check(len(rows) == fz["pre_freeze_resources"]["llm_requests"] and tok == fz["pre_freeze_resources"]["llm_tokens"], "no LLM request after the freeze")
check(all("api_key" not in json.dumps(r).lower() for r in rows), "LLM ledger carries no credential field")

# ---- 3. models trained without final lineages ---------------------------------------------------------------------------------------------
import ptv_data as D
final_lin = {l for l, p in D.partition().items() if p == "final"}
mj = sorted((HERE / "RUN" / "final").glob("*.json"))
check(len(mj) == 6, f"six final model runs recorded ({len(mj)})")
leak = [j.name for j in mj if final_lin & {D.lineage_of(c) for c in json.loads(j.read_text())["train_cells"]}]
check(not leak, "no final-lineage background in any final model's training set")
check(all(json.loads(j.read_text())["device"].startswith("cuda") for j in mj), "final models trained on the GPU")

# ---- 4. stored results vs CSVs -------------------------------------------------------------------------------------------------------------
res = json.loads((HERE / "RUN" / "final_eval" / "RESULTS.json").read_text())
import final_eval as FE
A = pd.read_csv(HERE / "RUN" / "final_eval" / "A_yields.csv")
check(bool((A.hits <= A.oracle).all()) and bool((A.f_used + 0.5 * A.m_used <= 5.0 + 1e-9).all()), "yields never exceed the oracle ceiling; spend never exceeds the 5.0 budget")
check(A.error.isna().all(), "no program error or runner fault in the final yields")
for c in res["A"]["contrasts"]:
    (w1, p1), (w2, p2) = [x.split("@")[::-1] for x in (c["a"], c["b"])]
    a = A[(A.world == w1) & (A.program == p1)].set_index("cell").hits; b = A[(A.world == w2) & (A.program == p2)].set_index("cell").hits
    d = (a - b).dropna(); lo, hi = FE.ci(d.values, [D.lineage_of(x) for x in d.index])
    check(abs(d.mean() - c["diff_hits"]) < 1e-9 and abs(lo - c["ci95"][0]) < 1e-9 and abs(hi - c["ci95"][1]) < 1e-9, f"recomputed contrast {c['a']} - {c['b']} matches the stored one")
for nm in ("A1", "A2"):
    check((HERE / "RUN" / "programs" / f"{nm}.py").read_text() == (HERE / "RUN" / "programs" / "A1_g1_incumbent.py").read_text(), f"{nm} is byte-identical to A0 (no accepted LLM edit)")
R = pd.read_csv(HERE / "RUN" / "final_eval" / "R_decision_table.csv")
pool = R[R.prec_at_k_pool.notna()]
for c in res["R"]["contrasts"]:
    if c["metric"] != "prec_at_k_pool": continue
    d = FE.contrast(pool, c["a"], c["b"], "prec_at_k_pool", FE.DELTA_T)
    check(abs(d["diff"] - c["diff"]) < 1e-9 and d["ci95"] == c["ci95"], f"recomputed R contrast {c['a']} - {c['b']} (prec@5) matches")
Qd = pd.read_csv(HERE / "RUN" / "final_eval" / "Q_per_background.csv")
for c in res["Q"]["contrasts"]:
    if c["metric"] != "prec5": continue
    d = FE.contrast(Qd.assign(score=Qd.arm), c["a"], c["b"], "prec5", FE.DELTA_T)
    check(abs(d["diff"] - c["diff"]) < 1e-9 and d["ci95"] == c["ci95"], f"recomputed Q contrast {c['a']} - {c['b']} (prec@5) matches")

# ---- 5. resource ledger ---------------------------------------------------------------------------------------------------------------------
rl = HERE / "RESOURCES.json"
if rl.exists():
    r = json.loads(rl.read_text())
    s = {"gpu": 0.0, "cpu": 0.0}
    for sub in ("dev", "sel", "sel30", "final"):
        for j in (HERE / "RUN" / sub).glob("*.json"):
            q = json.loads(j.read_text()); s["gpu" if q.get("device", "cpu").startswith("cuda") else "cpu"] += q["seconds"]
    check(abs(r["model_training"]["gpu_seconds"] - s["gpu"]) < 1 and abs(r["model_training"]["cpu_seconds"] - s["cpu"]) < 1, "resource ledger training seconds equal the per-run records")
    check(r["llm"]["requests"] == len(rows) and r["llm"]["tokens"] == tok, "resource ledger LLM totals equal the LLM ledger")
else:
    check(False, "RESOURCES.json missing")

print("\n".join(notes + fails))
print(f"\n{len(notes)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
