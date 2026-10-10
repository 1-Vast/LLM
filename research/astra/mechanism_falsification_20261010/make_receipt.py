"""Assemble the dated machine receipt log/20261010/MECHANISM_FALSIFICATION.json from the study's records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> dict:
    R, V, F, P = load("RESULTS.json"), load("VERIFIED.json"), load("FREEZE.json"), load("PROTOCOL_CONFIG.json")
    B = f"B{R['budget']}"
    arms = {}
    for name, a in R["arms"].items():
        arms[name] = {pol: {k: v[B][k] for k in ("all", "referenced", "knowledge_only") if k in v[B]}
                      for pol, v in a["by_policy"].items()}
        for pol, v in a["by_policy"].items():
            arms[name][pol]["activity_tiers"] = {k: v[B][k] for k in v[B] if k.startswith("activity_")}
    rec = {
        "study": "research/astra/mechanism_falsification_20261010",
        "question": "Can an LLM agent plus a virtual-cell world model falsify mechanism hypotheses for a perturbation with a calibrated error rate, choose observations that falsify, and say when hypotheses cannot be separated or the set is inadequate?",
        "data": {"source": "GSE92742 LINCS L1000 Level 5 (MODZ), 978 landmark genes, 9 core lines x {6 h, 24 h}, 10 uM",
                 "ground_truth": "Drug Repurposing Hub 2020-03-24 single-mechanism annotations (non-commercial use)",
                 "units": {"reference": 726, "development": 358, "confirmation": R["n_queries"]}, "classes": 424},
        "frozen_utc": F["frozen_utc"], "protocol_config_sha256": R["protocol_sha256"],
        "budget_profiles": R["budget"], "alpha": P["alpha"],
        "confirmatory": {"arms": arms, "contrasts": R["contrasts"], "ranking": R.get("ranking"),
                         "identifiability": R.get("identifiability"), "revision": R.get("revision"),
                         "llm_arms": {k: v for k, v in R.get("llm_arms", {}).items() if k != "drugs"},
                         "decisions": R["decisions"]},
        "verification": V,
        "provider_spend_usd_ledger_total": json.loads((ROOT / "tmp/mechanism_falsification_spend.json").read_text(encoding="utf-8"))["total_usd"],
        "files": {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in
                  ("RESULTS.json", "VERIFIED.json", "FREEZE.json", "PROTOCOL.md", "PROTOCOL_CONFIG.json", "ROWS.json")},
    }
    out = ROOT / "log/20261010/MECHANISM_FALSIFICATION.json"
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    r = main()
    print("written", len(json.dumps(r)), "bytes")
