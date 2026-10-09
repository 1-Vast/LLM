# Experiment record: viability-contrast-8 pilot (2026-10-08, evening)

> **File summary**
> - **Path**: `log/20261008/VIABILITY_CONTRAST_V8_PILOT.md`
> - **Purpose**: Dated record of the protocol-8 fold-0 pilot (LMM marginal LLR +
>   conformal risk-control certification), designed by the three-agent synthesis
>   recorded below. The pilot gate FAILED; per the registered protocol the global
>   5-fold phase is BLOCKED.
> - **Core points**: (1) The CRC layer produced the first near-valid decision policy
>   of the series: held-out wrong-decision rate 0.070 (target 0.05) at coverage
>   0.165, with the selected lambda at the grid ceiling (12) - a measurable
>   calibration-to-held-out unit shift of about +0.02 above the calibration-side
>   risk bound. (2) The scalar-loading LMM marginal LLR is NOT a valid e-process
>   either (held-out conditional wrong 0.41; shuffled decide-true 0.40): the fourth
>   failed statistic family. (3) The reading oracle still errs 0.327 - the
>   information constraint persists (median information budget 4.54, borderline).
>   (4) tau2 MoM estimates (median 0.013 raw units^2) are consistent with the
>   probe's 0.7 z-units given typical template scales. (5) World-guided acquisition
>   helps coverage under the e-process rule (+0.070 vs random) but not under CRC.
> - **Interfaces / data**: `research/viability_contrast/{protocol8.json, run8.py,
>   freeze8.json}`; outputs `outputs/viability_contrast_20261008/run8_pilot/`.
> - **Depends on**: `log/20261008/{README.md, VIABILITY_CONTRAST_V7.md}`,
>   `protocol8.json`.

## 1. Record control

- **Synthesis (2026-10-08, three agents).** Statistics agent: LMM marginal LR with
  the compound random effect integrated out (rank-1 O(1) updates) as the top model
  route; information-budget criterion I(pair) >= 4.0; betting-at-budget-48 killed
  by the probe's power analysis. Literature agent: conformal risk control
  (arXiv:2208.02814) and Learn-Then-Test (arXiv:2110.01052) as the
  distribution-free certification route; within-episode adaptivity confirmed not
  to break episode exchangeability (arXiv:2602.03814 as direct precedent).
  Repository agent: ICC median 0.487, scalar tau2 ~ 0.7 z-units; corr errors
  concentrated in the first 1-3 purchases.
- **Pre-registration.** `protocol8.json` written before any v8 episode was scored.
- **Deviation (disclosed per discipline).** The first pilot run crashed 13 s in
  (float-index on an empty purchase set) before ANY scored output was written; the
  incomplete freeze was deleted, the bug fixed, an edge case verified, and
  `freeze8.json` re-frozen at 2026-10-08T10:08:55Z. No scored number was read
  before the re-freeze. Synthetic smoke `tmp/smoke8.py` exercised all paths.
- **Scope.** Fold 0 only: 115 held-out episodes per arm (117 heldout, 2 skipped
  for missing rival), 211 calibration episodes per acquisition policy. Runtime
  137 s (registered estimate < 480 s). $0, 0 wells, 0 downloads.

## 2. Results (outputs/viability_contrast_20261008/run8_pilot/)

Pilot gate: FAILED (P1 false, P2 false, P3 true); proceed_to_global = false.

| Arm (stopping) | Coverage | Wrong-decision rate | CP UCB95 | Cond. wrong |
|---|---|---|---|---|
| lmm_ginfo (crc) | 0.165 | 0.070 | 0.122 | 0.421 |
| lmm_ginfo (eprocess) | 0.870 | 0.357 | 0.437 | 0.410 |
| lmm_world (crc) | 0.070 | 0.035 | 0.078 | 0.500 |
| lmm_world (eprocess) | 0.730 | 0.278 | 0.355 | 0.381 |
| lmm_random (crc) | 0.261 | 0.087 | 0.143 | 0.333 |
| lmm_random (eprocess) | 0.661 | 0.261 | 0.337 | 0.395 |
| lmm_ginfo_shuffled (crc) | 0.104 | 0.052 | 0.100 | 0.500 |
| lmm_ginfo_shuffled (eprocess) | 0.930 | 0.530 | 0.610 | 0.570 |
| oracle_lmm (eprocess) | 0.930 | 0.304 | 0.383 | 0.327 |

- lambda_crc selected: ginfo 12.0 (grid ceiling), world 12.0, random 5.42;
  calibration-side risk at the selected lambda was within the CRC bound.
- lambda_ltt: ginfo 2.87, world 0.5 (conditional-risk selection; reported only).
- tau2: per-class median 0.0133 raw units^2, pooled 0.0153 - consistent with the
  probe's 0.7 z-units at typical template scales (not an estimation bug).
- Information flag: pairs with I < 4.0 have CRC coverage 0.135 vs 0.190 for
  I >= 4.0 (direction correct, weak).

## 3. Interpretation and claim boundaries

- **Measured.** (a) CRC is the first decision policy of the series whose held-out
  wrong-decision rate approaches the target (0.070 vs 0.05) at non-trivial
  coverage, with NO model-correctness assumption - but it does not meet the gate,
  and the excess over the calibration-side bound (+0.02) matches the registered
  training-unit to held-out-unit shift. (b) The scalar-loading LMM marginal LLR is
  invalid as an e-process (shuffled decide-true 0.40; held-out conditional wrong
  0.41) - worse than v7's per-line Huber (0.26-0.36); rank-1 marginalisation makes
  early joint deviations MORE coherent, and the median-MoM tau2 is likely
  underestimated under winsorization. (c) The oracle binds at 0.327 wrong: at
  median information budget 4.54, a large share of pairs cannot certify at 16
  readings by any method. (d) Under the invalid e-process rule the virtual cell
  raises coverage (+0.070 vs random); under CRC the world arm's coverage collapses
  (0.070) because the risk-controlling lambda is at the ceiling for all arms.
- **Proposed (registered v9 candidates, in order).** (i) Unit-matched CRC:
  unit-stratified / weighted-conformal calibration (Barber et al. 2023) to close
  the measured +0.02 shift, plus an extended lambda grid beyond 12 and both-half
  calibration pooling to raise n from 211. (ii) LMM with line-specific loadings
  (leading eigenvector of the MoM covariance matrix) and a t-distributed compound
  effect (the protocol-7 registered amendment), re-estimated with unwinsorized
  tails. (iii) Accept and certify at a coarser decision: aggregate pairs by
  information budget and certify only I >= 4.0 pairs (the flag worked
  directionally; a registered eligibility rule would raise both coverage and
  validity where certification is feasible).
- **Not established.** Any certified decision at alpha = 0.05 on this task; the
  LMM route's viability even with better loadings (two failed model-based
  attempts); the global phase (blocked).

## 4. Reproduction and artifact ledger

- `... -m research.viability_contrast.freeze --v8 --verify` then
  `... -m research.viability_contrast.run8 --pilot`.
- Code/protocol: `research/viability_contrast/{protocol8.json, run8.py,
  freeze8.json}`; smoke `tmp/smoke8.py`; synthesis probes `tmp/v8probe_*.py`.
- Outputs: `outputs/viability_contrast_20261008/run8_pilot/{episodes.csv,
  summary.json, gate.json}`.

## 5. Curation provenance

Written by the WorkBuddy session of 2026-10-08 from the frozen pilot outputs and
the three agents' reports (statistics, conformal literature, repository empirics;
the reports are summarized in section 1 and were produced read-only or with
scratch confined to tmp/v8probe_*). No v1-v7 file was modified; `src/` and
`tools/` untouched. $0, 0 wells, 0 downloads.
