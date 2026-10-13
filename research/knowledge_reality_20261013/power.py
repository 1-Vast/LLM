"""Power of the sealed confirmation for H1, from the development effect size (POWER.json).

File summary
- Path: research/knowledge_reality_20261013/power.py
- Purpose: fix `min_active`, the smallest number of active sealed compounds at which H1 is
  powered, before the freeze. It reads DEVELOPMENT.json and SEALED_CENSUS.json only.
- Core points:
  - Effect: the development `know_full` minus `chem_full` mean Δr on active compounds.
  - Its standard error comes from the family-cluster bootstrap interval:
    (upper - lower) / (2 x 1.96). It is scaled to another sample size by sqrt(n_dev / n).
  - Required actives for 80% power at one-sided α = 0.025:
    n = n_dev x ((z_0.975 + z_0.8) x SE / effect)^2.
  - Expected sealed actives: eligible compounds times the development active share. This is an
    assumption: REP.1M may differ in composition.
- Output: POWER.json in this folder.
"""
from __future__ import annotations

import json
import math

from sources import HERE, write_json

Z_ALPHA = 1.959964          # one-sided 0.025
Z_POWER = 0.841621          # 80% power


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def main() -> None:
    dev = json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    sealed = json.loads((HERE / "SEALED_CENSUS.json").read_text(encoding="utf-8"))
    g1 = dev["comparisons"]["know_full-chem_full:active"]
    effect = g1["difference"]
    se = (g1["ci95"][1] - g1["ci95"][0]) / (2 * Z_ALPHA)
    n_dev = g1["units"]
    share = dev["population"]["active"] / dev["population"]["compounds"]
    expected = sealed["eligible_compounds"] * share
    n_req = n_dev * ((Z_ALPHA + Z_POWER) * se / effect) ** 2
    power = phi(effect / (se * math.sqrt(n_dev / expected)) - Z_ALPHA)
    write_json(HERE / "POWER.json", {
        "reads": "DEVELOPMENT.json and SEALED_CENSUS.json only",
        "effect_dev": effect, "se_dev": se, "n_dev_active": n_dev,
        "dev_active_share": share, "sealed_eligible": sealed["eligible_compounds"],
        "expected_sealed_active": expected,
        "min_active": math.ceil(n_req),
        "power_at_expected_active": power,
        "assumptions": "effect and per-compound spread as in development; clusters scale like compounds; one-sided alpha 0.025; "
                       "80% power",
    })
    print("min_active", math.ceil(n_req), "expected", round(expected), "power", round(power, 3))


if __name__ == "__main__":
    main()
