"""Verify the block N confirmation run (writes VERIFIED.json).

Checks:
1. Every file hashed in FREEZE.json is unchanged; every pre-freeze agent output is unchanged.
2. Both PRISM tiers match TIERS_RECEIPT.json; RESULTS.json is the sealed, agent-on, unpoisoned run of
   the frozen PROTOCOL_CONFIG.json, with 421 queries and row counts matching the CSVs.
3. Contrasts and verdicts recomputed from ROWS_killers.csv / ROWS_trust.csv equal RESULTS.json.
4. Every confirmation agent output that scoring needs exists, was absent at the freeze and was
   created after it.
5. No stored abstract for a confirmation drug matches the literature leak pattern.
6. The provider ledger stays within its ceiling.
7. Outcome poisoning on the confirmation tier (no agent, seed 1): no VC contrast passes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import evaluate as EV  # noqa: E402

LEDGER = ROOT / "tmp/mechanism_routing_spend.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def close(a, b, tol=1e-9) -> bool:
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return (a is None and b is None) or abs(float(a) - float(b)) <= tol
    return a == b


def main(run_poison: bool = True) -> dict:
    checks = {}
    F = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    changed = [f for f, h in F["files"].items() if not (HERE / f).exists() or sha(HERE / f) != h]
    checks["frozen_files_unchanged"] = {"ok": not changed, "n": len(F["files"]), "changed": changed}
    changed = [f for f, h in F["agent_outputs"].items() if not (HERE / f).exists() or sha(HERE / f) != h]
    checks["pre_freeze_agent_outputs_unchanged"] = {"ok": not changed, "n": len(F["agent_outputs"]), "changed": changed}

    import tiers as TI
    ok_tiers = True
    for t in ("open", "sealed"):
        try:
            TI.load(t)
        except Exception as error:  # digest mismatch is a named failure
            ok_tiers = False
            checks[f"tier_{t}"] = str(error)
    checks["tiers_match_receipt"] = {"ok": ok_tiers}

    R = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    K = pd.read_csv(HERE / "ROWS_killers.csv")
    T = pd.read_csv(HERE / "ROWS_trust.csv")
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))["units"]
    conf = sorted(d for d, u in split.items() if u["role"] == "confirmation")
    run_ok = (R["tier"] == "sealed" and R["with_llm"] and R["poison_seed"] is None
              and R["protocol_sha256"] == F["files"]["PROTOCOL_CONFIG.json"]
              and R["n_queries"] == len(conf) == len(T) and R["n_killers"] == len(K)
              and sorted(T["drug"].astype(str)) == conf)
    checks["results_identity"] = {"ok": bool(run_ok), "n_queries": R["n_queries"], "n_killers": R["n_killers"],
                                  "n_trust_rows": int(len(T)), "n_killer_rows": int(len(K))}

    P = EV.protocol()
    T2 = T.copy()
    cons = EV.contrasts(K, T2, P, with_llm=True)
    dec = EV.decide(cons, P)
    checks["recomputed_contrasts_match"] = {"ok": close(json.loads(json.dumps(cons)), R["contrasts"])
                                            and close(json.loads(json.dumps(dec)), R["decisions"])}

    frozen_at = F["frozen_utc"]
    L = P["llm"]
    need = [(arm, L["regime"], d) for arm in L["all_query_arms"] for d in conf]
    need += [(arm, L["regime"], d) for arm in L["killer_arms"] for d in K["drug"].astype(str)]
    need += [("explain_full", f"n{L['explain_size']}", d) for d in K["drug"].astype(str)]
    missing, pre, early, status = [], [], [], {}
    for arm, sub, d in need:
        rel = f"agent_outputs/{arm}/{sub}/{EV.slug(d)}.json"
        p = HERE / rel
        if not p.exists():
            missing.append(rel)
            continue
        if rel in F["agent_outputs"]:
            pre.append(rel)
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("created_utc", "") < frozen_at:
            early.append(rel)
        status.setdefault(arm, {}).setdefault(rec.get("status"), 0)
        status[arm][rec.get("status")] += 1
    checks["confirmation_agent_outputs"] = {"ok": not missing and not pre and not early, "n_expected": len(need),
                                            "missing": missing[:20], "n_missing": len(missing),
                                            "present_before_freeze": pre[:20], "created_before_freeze": early[:20],
                                            "status": status}

    import literature as LI
    leaks = []
    for d in conf:
        p = HERE / "literature" / f"{LI.slug(d)}.json"
        if not p.exists():
            continue
        for h in json.loads(p.read_text(encoding="utf-8")).get("hits", []):
            if LI.LEAK.search(f"{h.get('title', '')} {h.get('abstract', '')}"):
                leaks.append((d, h.get("pmid")))
    checks["literature_leak_scan"] = {"ok": not leaks, "leaks": leaks[:20]}

    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    checks["ledger_within_ceiling"] = {"ok": led["total_usd"] <= led["ceiling_usd"], "total_usd": round(led["total_usd"], 4),
                                       "ceiling_usd": led["ceiling_usd"], "results_ledger_usd": R.get("ledger_total_usd")}

    if run_poison:
        pr = EV.main("sealed", HERE / "verify_poison", poison_seed=1, with_llm=False)
        vc = {k: v["verdict"] for k, v in pr["decisions"].items() if k != "headline" and v.get("family") == "vc"}
        checks["outcome_poisoning_sealed"] = {"ok": all(v != "PASS" for v in vc.values()), "verdicts": vc,
                                              "estimates": {k: round(pr["contrasts"][k]["estimate"], 4) for k in vc}}

    out = {"all_ok": all(c.get("ok", False) for c in checks.values() if isinstance(c, dict) and "ok" in c),
           "checks": checks}
    (HERE / "VERIFIED.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = main("--no-poison" not in sys.argv)
    print(json.dumps({k: v.get("ok") if isinstance(v, dict) else v for k, v in r["checks"].items()}, indent=1))
    print("ALL OK" if r["all_ok"] else "FAILED")
