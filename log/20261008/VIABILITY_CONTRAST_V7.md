# Experiment record: viability-contrast-7 (2026-10-08, afternoon)

> **File summary**
> - **Path**: `log/20261008/VIABILITY_CONTRAST_V7.md`
> - **Purpose**: Dated record of protocol `viability-contrast-7`, the literature-driven
>   repair of the invalid v6 e-process. Continues the same day's v6 block
>   (`log/20261008/README.md`).
> - **Core points**: Gate v7 FAILED on G1 (validity) but with diagnostic structure.
>   The Huber density-floor clip (Saha-Ramdas LFD construction, winsorization at
>   |z| = 2) reduced the held-out conditional wrong rate from v6's 0.40-0.45 to
>   0.26-0.36 - a large improvement, far from the 0.05 target. The shrunk-correlation
>   joint LR did NOT help (0.40), so correlation modelling of template residuals is
>   not the binding fix. The bounded betting process was the most conservative family
>   (shuffled decide-true 0.012, the only arm passing the Type-I control) but decided
>   too few episodes (25) for its 0.08 wrong rate to certify (CP UCB 0.23). The
>   label-blind reading oracle still errs 0.302 at 3.8 measurements, localising the
>   binding constraint in BETWEEN-COMPOUND HETEROGENEITY around class templates,
>   which no registered statistic models. G2 PASSED: world-guided acquisition lifts
>   coverage +0.192 [+0.142, +0.243] over random on the same statistic - a measured
>   virtual-cell contribution to acquisition, inside an invalid-statistic regime.
> - **Interfaces / data**: protocol/digests in
>   `research/viability_contrast/{protocol7.json, freeze7.json}`; outputs in
>   `outputs/viability_contrast_20261008/run7/`.
> - **Depends on**: `log/20261008/README.md` (v6), `protocol6.json`, the frozen v1
>   pack (byte-identical).

## 1. Record control

- **Pre-registration.** `protocol7.json` written before any v7 episode was scored;
  `freeze7.json` (2026-10-08T08:52:29Z) digests protocol7, run7.py, its dependency
  run6.py and the frozen pack. v6 freeze re-verified intact after the freeze.py
  extension (all_match true).
- **Pre-freeze exposure.** Synthetic smoke (`tmp/smoke7.py`) exercised every
  statistic and arm path, shapes only. No pack score read before the freeze.
- **New literature (verified by retrieval 2026-10-08).** Saha and Ramdas,
  *Huber-robust likelihood ratio tests for composite nulls and alternatives*, IEEE
  Trans. Inf. Theory 2024 (arXiv:2408.14015): the floored-density LFD construction
  behind S_huber, valid at arbitrary stopping times under epsilon-contamination.
  Waudby-Smith and Ramdas, *Estimating means of bounded random variables by
  betting*, JRSS B 86(1):1-27, 2024 (doi:10.1093/jrsssb/qkad009): the bounded
  betting e-process behind S_bet.

## 2. Research questions and hypotheses

From `protocol7.json`:
1. Does the Huber clip restore e-process validity (M1, heavy tails)? (G1, huber_world)
2. Does shrunk-correlation modelling restore it (M2)? (G1, corr_world)
3. Does the betting process control Type-I empirically? (shuffled control)
4. Does world-guided acquisition help once the statistic is repaired? (G2)
5. Does a valid statistic pay an efficiency penalty below the invalid v6 baseline? (G3)

## 3. Materials, data and computational environment

- Frozen v1 pack (byte-identical, freeze-verified). No download. `maestro` env,
  CPU only. Runtime 788 s (registered estimate 600 s; overrun 31 percent; the
  per-fold world5b rank/weight selectors dominate, as in v6 - a caching candidate
  for future runs, reported not re-tuned). $0 API, 0 wells.

## 4. Experimental design and controls

Per `protocol7.json`: three statistic families (S_huber primary, S_corr, S_bet) at
the same fixed threshold log(20); acquisitions {fixed, random, world5b-guided};
label-blind realised-reading oracle on the Huber statistic; label-breaking shuffled
controls for each world arm; 515 episodes per arm over 5 folds; unit-cluster
bootstrap; CP one-sided UCB95 on every wrong rate. The virtual cell guides
acquisition only; no statistic uses the world (registered design, per the v6
masked-control measurement).

## 5. Experiment register and results

Gate v7 (`outputs/viability_contrast_20261008/run7/gate.json`): **FAILED**
(G1 false for both registered arms; G2 TRUE; G3 false).

| Arm | Coverage | Cond. wrong | CP UCB95 | Measurements | cc/measurement |
|---|---|---|---|---|---|
| huber_fixed | 0.864 | 0.362 | 0.401 | 7.27 | 0.076 |
| huber_random | 0.517 | 0.199 | 0.244 | 12.79 | 0.032 |
| huber_world | 0.709 | 0.260 | 0.301 | 9.84 | 0.053 |
| huber_world_shuffled | 0.600 | 0.417 | 0.466 | 10.89 | (decide-true 0.350) |
| corr_fixed | 0.944 | 0.383 | 0.420 | 4.36 | 0.134 |
| corr_world | 0.891 | 0.403 | 0.442 | 5.74 | 0.093 |
| corr_world_shuffled | 0.932 | 0.556 | 0.594 | 5.19 | (decide-true 0.414) |
| bet_fixed | 0.109 | 0.179 | 0.284 | 15.41 | 0.006 |
| bet_world | 0.049 | 0.080 | 0.231 | 15.82 | 0.003 |
| bet_world_shuffled | 0.025 | 0.538 | 0.776 | 15.93 | (decide-true 0.012) |
| oracle_huber (ceiling) | 0.983 | 0.302 | 0.338 | 3.77 | 0.182 |

Registered contrasts:
- coverage(huber_world) - coverage(huber_random): +0.192 [+0.142, +0.243] (G2 PASS)
- coverage(corr_world) - coverage(corr_fixed): -0.052 [-0.083, -0.019]
- G3: huber_world cc/measurement 0.053 < v6 marg_fixed 0.165 (FAIL; the v6
  "efficiency" was bought by invalid overconfidence, as expected)

## 6. Deviations, failures and corrections

- Runtime 788 s vs the 600 s registration (+31 percent). Cause: the per-fold
  world5b rank/weight selection (select_rank/select_weight) dominates; reported,
  not re-tuned. Registered as a caching candidate for any v8.
- The S_bet e_minus/lambda logic was corrected once during pre-freeze authoring
  (before any episode ran); the frozen file holds the corrected version.

## 7. Interpretation and claim boundaries

- **Measured.** (a) The Huber clip moves the conditional wrong rate from 0.40-0.45
  (v6) to 0.26-0.36: heavy tails are a real but not the binding mechanism.
  (b) Shrunk-correlation modelling of template residuals does not improve on Huber
  (0.40): M2 as operationalised in S_corr is not binding either. (c) The betting
  family is the only one whose label-breaking control respects the Type-I bound
  (decide-true 0.012), at a large power cost (coverage 0.05); its 0.08 held-out
  wrong rate cannot certify (25 decisions, UCB 0.23). (d) The reading oracle still
  errs 0.302: the binding constraint is between-compound heterogeneity around the
  class templates - single-compound profiles deviate from their class template by
  more than every registered predictive allows, so ANY LR calibrated to the
  template is overconfident, and no acquisition can repair it. (e) World-guided
  acquisition improves coverage over random by +0.192 on identical statistics: the
  virtual cell finds informative lines (a real acquisition-level contribution,
  inside an invalid-statistic regime; decision value NOT established).
- **Proposed (registered v8 candidates).** (i) The mixed-model joint LLR with an
  explicit compound-level random effect integrated out (v6 register candidate (ii),
  now the top candidate: it is the only registered family that models
  between-compound heterogeneity directly). (ii) S_bet at a larger registered
  budget (e.g. 48) with a power analysis computed from the frozen v7 bet
  trajectories BEFORE registration - the only family with valid-looking Type-I
  behaviour deserves a fair power budget. (iii) Per-class or low-rank-plus-diagonal
  correlation for S_corr (the pooled shrunk R may dilute class structure).
- **Not established.** Any certified decision on this task family; decision-level
  value of the virtual-cell acquisition (G2 is a coverage result in an invalid
  regime); the LLM arm (Phase B remains registered-blocked on G1).

## 8. Reproduction and artifact ledger

- `... -m research.viability_contrast.freeze --v7 --verify` then
  `... -m research.viability_contrast.run7`.
- Code/protocol: `research/viability_contrast/{protocol7.json, run7.py,
  freeze7.json}`; freeze.py extended (version 8).
- Outputs: `outputs/viability_contrast_20261008/run7/{episodes.csv, summary.json,
  gate.json, world_fit.json}`; smoke: `tmp/smoke7.py`.

## 9. Curation provenance

Written by the WorkBuddy session of 2026-10-08 from the frozen outputs only. No
v1-v6 file was modified; `src/` and `tools/` untouched. $0, 0 wells, 0 downloads.
