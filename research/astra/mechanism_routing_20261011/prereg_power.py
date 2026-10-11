"""Pre-registration aid: projected power of each registered contrast on the confirmation tier.

Uses the development rehearsal (``rehearsal/dev_llm/RESULTS.json``, open drugs only).
* The development estimate is taken as the true effect.
* Its 95% cluster-bootstrap half-width / 1.96 gives the standard error.
* The standard error is scaled by sqrt(n_dev / n_conf), where n_conf is the expected confirmation
  count: the 421 confirmation drugs times the development killer rate (only the count of
  confirmation drugs is known before the freeze).
* The family-wise two-sided level is the one ``evaluate.py`` uses.

Writes ``power`` into each contrast of PROTOCOL_CONFIG.json and sets ``predicted`` to the verdict
with the largest projected probability (PASS, HARM or NOT_SUPPORTED).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
N_CONFIRMATION_DRUGS = 421


def main():
    cfg_path = HERE / "PROTOCOL_CONFIG.json"
    P = json.loads(cfg_path.read_text(encoding="utf-8"))
    R = json.loads((HERE / "rehearsal" / "dev_llm" / "RESULTS.json").read_text(encoding="utf-8"))
    rate_killer = R["n_killers"] / R["n_queries"]
    for c in P["contrasts"]:
        r = R["contrasts"][c["id"]]
        k = sum(1 for x in P["contrasts"] if x["family"] == c["family"])
        zf = norm.ppf(1 - P["alpha"] / k / 2)
        n_dev = r["n"]
        n_conf = N_CONFIRMATION_DRUGS * (rate_killer if c["kind"] == "paired" else 1.0)
        if c["a"].startswith("secondary:"):
            n_conf *= n_dev / R["n_killers"]  # share of killers with a secondary profile
        se = (r["ci95"][1] - r["ci95"][0]) / (2 * 1.96) * np.sqrt(n_dev / n_conf)
        est = r["estimate"]
        p_pass = float(norm.sf((zf * se - est) / se))
        p_harm = float(norm.cdf((-zf * se - est) / se))
        probs = {"PASS": p_pass, "HARM": p_harm, "NOT_SUPPORTED": 1 - p_pass - p_harm}
        c["development"] = {"estimate": round(est, 4), "ci95": [round(x, 4) for x in r["ci95"]],
                            "ci_family": [round(x, 4) for x in r["ci_family"]], "n": n_dev}
        c["power"] = {"expected_n": round(n_conf, 1), "se_projected": round(float(se), 4),
                      "family_z": round(float(zf), 3), **{f"p_{k_}": round(v, 3) for k_, v in probs.items()}}
        c["predicted"] = max(probs, key=probs.get)
    P["power_note"] = ("predicted = the most probable verdict if the development estimate were the true effect and the "
                       "standard error shrank with the expected confirmation count; it is a forecast, not a decision rule")
    cfg_path.write_text(json.dumps(P, indent=1) + "\n", encoding="utf-8")
    return P


if __name__ == "__main__":
    P = main()
    for c in P["contrasts"]:
        print(c["id"], c["predicted"], c["power"])
