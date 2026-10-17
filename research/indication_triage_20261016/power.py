"""Power of the sealed H1 test and the development gate, from DEVELOPMENT.json only (POWER.json).

File summary
- Path: research/indication_triage_20261016/power.py
- Purpose: fix, before any sealed outcome exists locally, how many campaigns and active compounds
  H1 needs, whether the sealed tier is worth opening, and the minimum active count below which
  H1 reads INCONCLUSIVE_UNDERPOWERED.
- Core points:
  - Unit: the campaign. The development effect is the per-campaign difference in follow-up hits,
    maestro_loop minus the tuned comparator, at the primary budget, on estimation folds 2-4.
  - Sealed size: 1,229 eligible compounds in campaigns of 64, i.e. 20 campaigns (19 full).
  - Two power estimates at one-sided alpha 0.025:
    - normal approximation, power = Phi(mean x sqrt(n) / sd - z);
    - resampling: 20 development campaign differences drawn with replacement, each draw tested
      with the registered sign-flip test; power = share of draws that reject.
  - Activity shift: if the sealed release has a fraction r of the development active share, the
    mean difference is scaled by r and its SD by sqrt(r) (counts scale like Poisson). Reported for
    r in {0.5, 0.75, 1.0}; this is an assumption, not a measurement.
  - Development gate (all three must hold before the sealed outcome file may be requested):
    - G1: development contrast > 0 with one-sided sign-flip p < 0.05;
    - G2: resampling power at 20 campaigns >= 0.80;
    - G3: certificate violations of the loop's yield bound in development do not exceed the 99th
      percentile of Binomial(campaigns, 0.05).
- Output: POWER.json in this folder.
"""
from __future__ import annotations

import json
import math

import numpy as np

from common import CAMPAIGN, HERE, SEALED_CENSUS, SEED, write_json

ALPHA = 0.025
Z_ALPHA = 1.959964
Z_POWER = 0.841621
GATE_P = 0.05
GATE_POWER = 0.80


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sign_flip_p(d: np.ndarray, signs: np.ndarray) -> float:
    obs = d.mean()
    null = (signs * d).mean(1)
    return float((1 + (null >= obs - 1e-12).sum()) / (len(null) + 1))


def resampled_power(d: np.ndarray, n: int, draws: int = 2000, flips: int = 2000, scale: float = 1.0) -> float:
    rng = np.random.default_rng(SEED)
    signs = np.random.default_rng(SEED + 1).choice([-1, 1], size=(flips, n))
    mean, centred = d.mean(), d - d.mean()
    rejections = 0
    for _ in range(draws):
        sample = mean * scale + centred[rng.integers(0, len(d), n)] * math.sqrt(scale)
        rejections += sign_flip_p(sample, signs) < ALPHA
    return rejections / draws


def binom_quantile(n: int, p: float, q: float) -> int:
    cdf = 0.0
    for k in range(n + 1):
        cdf += math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        if cdf >= q:
            return k
    return n


def main() -> None:
    dev = json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    census = json.loads(SEALED_CENSUS.read_text(encoding="utf-8"))
    comparator = dev["primary_contrast"]["comparator"]
    per = dev["per_campaign_primary"]
    d = np.array(per["maestro_loop"], float) - np.array(per[comparator], float)
    mean, sd = float(d.mean()), float(d.std(ddof=1))
    eligible = census["eligible_compounds"]
    n_sealed = math.ceil(eligible / CAMPAIGN)
    pop = dev["population"]
    dev_compounds = sum(v["compounds"] for v in pop.values())
    dev_active = sum(v["active"] for v in pop.values())
    share = dev_active / dev_compounds
    n_required = math.inf if mean <= 0 else ((Z_ALPHA + Z_POWER) * sd / mean) ** 2
    normal = phi(mean * math.sqrt(n_sealed) / sd - Z_ALPHA) if sd > 0 else float(mean > 0)
    shift = {str(r): resampled_power(d, n_sealed, scale=r) if mean > 0 else 0.0 for r in (0.5, 0.75, 1.0)}
    resampled = shift["1.0"]
    cert = dev["estimation"][str(dev["primary_w"])]["maestro_loop"]["certificate"]
    campaigns_dev = len(d)
    allowed = binom_quantile(campaigns_dev, 0.05, 0.99)
    gate = {
        "G1_development_contrast": {"mean": mean, "p": dev["primary_contrast"]["p"],
                                    "pass": bool(mean > 0 and dev["primary_contrast"]["p"] < GATE_P)},
        "G2_power_at_sealed_size": {"resampled_power": resampled, "threshold": GATE_POWER,
                                    "pass": bool(resampled >= GATE_POWER)},
        "G3_certificate_validity": {"violations": cert["violations"], "allowed": allowed,
                                    "pass": bool(cert["violations"] <= allowed)},
    }
    verdict = "PASS" if all(g["pass"] for g in gate.values()) else "FAIL"
    min_active = None if not math.isfinite(n_required) else math.ceil(math.ceil(n_required) * CAMPAIGN * share)
    write_json(HERE / "POWER.json", {
        "reads": "DEVELOPMENT.json and SEALED_CENSUS.json only",
        "comparator": comparator, "dev_campaigns": campaigns_dev,
        "dev_mean_difference": mean, "dev_sd_difference": sd,
        "dev_active_share": share, "sealed_eligible": eligible, "sealed_campaigns": n_sealed,
        "expected_sealed_active": eligible * share,
        "campaigns_required_80": None if not math.isfinite(n_required) else math.ceil(n_required),
        "min_active": min_active,
        "power_normal": normal, "power_resampled": resampled,
        "power_resampled_by_active_share_ratio": shift,
        "gate": gate, "gate_verdict": verdict,
        "assumptions": "campaign differences as in development; sealed campaigns exchangeable with development "
                       "campaigns; one-sided alpha 0.025; activity shift scales mean by r and SD by sqrt(r)",
    })
    print("gate", verdict, "mean", round(mean, 3), "sd", round(sd, 3), "power", round(resampled, 3),
          "campaigns_required", n_required)


if __name__ == "__main__":
    main()
