# Experiment record: 2026-10-08

> **File summary**
> - **Path**: `log/20261008/README.md`
> - **Purpose**: Dated record of the viability-contrast-6 block (protocol
>   `viability-contrast-6`): the two-class e-process reformulation registered as the
>   next direction by the v5/v5b verdicts, plus the supporting literature survey.
> - **Core points**: Gate v6 FAILED on the primary validity check G1 (empirical
>   Type-I behaviour). The naive per-line LLR at the fixed a-priori threshold
>   log(1/alpha), alpha = 0.05, produced conditional wrong rates 0.40-0.45 across all
>   realistic arms (515 episodes/arm, 5 folds) - an eight-to-nine-fold inflation over
>   the nominal 0.05 - and the shuffled control decided-true at 0.173 (> 0.10 bound).
>   A labelled post-hoc diagnostic localised the mechanism: class-template residuals
>   correlate across lines at mean |rho| = 0.49 (98.6 percent of line pairs above
>   0.3), and 99.1 percent of held-out compounds carry at least one pool line at
>   |z| > 3 against their own class template (61.5 percent at |z| > 6). The
>   independence-assumption e-process is invalid on this data regardless of
>   acquisition: even the label-blind realised-reading oracle is 43.4 percent wrong.
>   G3 passed vacuously (the calibrated-tau comparator decides nothing, coverage 0).
>   The world completion channel again showed no compound-specific contribution
>   (masked within noise of real). Phase-B LLM arm stays registered-blocked.
> - **Interfaces / data**: protocol and digests in
>   `research/viability_contrast/{protocol6.json, freeze6.json}`; outputs in
>   `outputs/viability_contrast_20261008/run6/`; literature base in
>   `log/20261008/LITERATURE_SURVEY_20261008.md`.
> - **Depends on**: `log/20260928/VIABILITY_CONTRAST_V5.md`,
>   `log/20260928/VIABILITY_CONTRAST_V5B.md`, the frozen v1 pack (byte-identical).

## 1. Record control

- **Pre-registration.** `research/viability_contrast/protocol6.json` written before
  any v6 episode was scored; `freeze6.json` (2026-10-08T07:44:49Z) digests the
  protocol, `run6.py` and the frozen pack. `freeze.py` was extended (version 7)
  exactly as it was for v5b; v1-v5b freezes re-verified after the edit.
- **Pre-freeze exposure.** A synthetic smoke run (`tmp/smoke6.py`) exercised every
  arm's code path (both statistics x three acquisition rules, oracle, masked,
  shuffled, no-winsorization) printing shapes only; no pack score was read before
  the freeze. The rival-separation and residual-corr diagnostics were computed only
  AFTER the frozen run completed (`tmp/resid_corr_posthoc.py`, labelled post-hoc).
- **Tree state.** `src/`, `tools/`, production defaults untouched; the block is
  confined to `research/viability_contrast/`, `outputs/viability_contrast_20261008/`,
  `tmp/` and this log folder.

## 2. Research questions and hypotheses

From `protocol6.json`, treated as hypotheses:
1. Does the two-hypothesis LLR at a fixed a-priori threshold behave like an
   e-process on real data (conditional wrong <= 0.05, CP UCB95 <= 0.10, shuffled
   decide-true <= 0.10)? (G1)
2. Does world-guided acquisition raise coverage over random and cut information cost
   below the fixed-order baseline at that threshold? (G2)
3. Does the calibration-free threshold keep power against the v2-v5 calibrated-tau
   comparator? (G3)
4. Does conditioning the per-line predictive on purchased readings (stat_world)
   improve validity over the naive independent statistic (stat_marginal)?

## 3. Materials, data and computational environment

- **Data.** The frozen v1 pack (PRISM Repurposing secondary curves, 517 compounds x
  443 lines, 39 classes, 490 units; byte-identical; freeze-verified). No download.
- **Environment.** `maestro` conda env (Python 3.11.16), CPU only. Runtime 960 s
  (registered estimate: under 900 s; overrun 7 percent, inside the registered 3x
  diagnosis bound; the split-half calibration episodes dominate). $0 API, 0 wells.
  The .env DeepSeek API was not called (Phase B gated on G1, which failed).

## 4. Experimental design and controls

Per `protocol6.json`: each held-out episode contrasts the true class with its
nearest training-template rival (515 episodes per arm over 5 folds). Statistic:
per-line LLR between the two hypotheses, fixed thresholds +/- log(20), abstention at
budget 16. Factorial: statistic {marginal, world-conditional} x acquisition {fixed,
random, world-guided}; label-blind realised-reading oracle ceiling; masked and
label-breaking shuffled controls; a no-winsorization sensitivity arm; the v2-v5
split-half calibrated-tau stopping comparator on the world_world trajectories.
Unit-cluster bootstrap (10 000 draws) on contrasts; Clopper-Pearson one-sided 95
percent UCBs on every wrong rate.

## 5. Experiment register and results

Gate v6 (`outputs/viability_contrast_20261008/run6/gate.json`): **FAILED**
(G1 false, G2a false, G2b false, G3 true).

| Arm | Coverage | Cond. wrong | CP UCB95 | Measurements (decided) |
|---|---|---|---|---|
| marg_fixed | 0.969 | 0.397 | 0.434 | 3.15 |
| marg_random | 0.744 | 0.441 | 0.485 | 7.94 |
| marg_world | 0.971 | 0.448 | 0.486 | 3.07 |
| marg_nowin_world | 0.988 | 0.525 | 0.562 | 2.53 |
| world_fixed | 0.427 | 0.414 | 0.471 | 2.07 |
| world_random | 0.031 | 0.562 | 0.773 | 6.69 |
| world_world | 0.431 | 0.446 | 0.503 | 1.97 |
| world_world_masked | 0.447 | 0.426 | 0.482 | 2.03 |
| world_world_shuffled | 0.416 | 0.584 | 0.641 | 1.89 |
| oracle_reading (ceiling) | 0.998 | 0.434 | 0.471 | 1.20 |
| world_world_taucal | 0.000 | - | - | - |

Registered contrasts (unit-cluster bootstrap 95 percent CI):
- coverage(world_world) - coverage(marg_random): -0.313 [-0.367, -0.258] (G2a fails)
- measurements(world_world) - measurements(marg_fixed): +6.40 [+5.86, +6.94] (G2b
  fails on the registered direction; note the comparison is distorted by coverage:
  world_world decides only its easiest 43 percent, at 1.97 measurements)
- coverage(world_world) - coverage(taucal): +0.431 [+0.388, +0.474] (G3 passes
  vacuously; taucal has no qualifying tau in any fold, consistent with v5/v5b)
- coverage(world_world) - coverage(masked): -0.016 [-0.041, +0.008] (no
  compound-specific world contribution)
- coverage(world_world) - coverage(world_random): +0.400 [+0.357, +0.443]
  (acquisition matters given the world statistic)

Post-hoc mechanism diagnostic (labelled; `tmp/resid_corr_posthoc.py`, fold-0
training templates): class-template residuals correlate across pool lines at mean
|rho| = 0.492, q90 = 0.586, 98.6 percent of 1996 sampled pairs above 0.3; 99.1
percent of held-out compounds have at least one pool line at |z| > 3 against their
OWN class template (median max |z| = 7.7; 61.5 percent above 6).

## 6. Deviations, failures and corrections

- Runtime exceeded the 900 s registration by 60 s (7 percent); reported, not
  re-tuned. The dominant cost is the split-half calibration episodes for the taucal
  comparator, which returned coverage 0 - a candidate for removal in any v7.
- One crash of the post-hoc diagnostic (broadcast typo) before any number was read;
  fixed and re-run. No scored output was affected.

## 7. Interpretation and claim boundaries

- **Measured.** (a) The independence-assumption two-class LLR at threshold log(20)
  is not a valid e-process on this task: empirical conditional wrong 0.40-0.45
  versus nominal 0.05 across every realistic arm, shuffled decide-true 0.173.
  (b) The invalidity is a property of the STATISTIC, not the acquisition: the
  label-blind realised-reading ceiling is 43.4 percent wrong. (c) The mechanism is
  cross-line correlation (mean |rho| about 0.5) plus heavy-tailed residuals (median
  max |z| 7.7), which make single readings produce threshold-crossing increments;
  decisions land at 1-3 measurements. (d) Conditioning on purchased readings through
  the world5b completion narrows coverage (0.43 vs 0.97 marginal) without restoring
  validity, and the masked control shows no compound-specific contribution -
  consistent with the v5b retirement of the channel. (e) The calibrated-tau
  comparator qualifies nothing (coverage 0), so the e-threshold's nominal power
  advantage is real but vacuous given (a).
- **Proposed.** The reformulation survives as a direction but the e-variables must
  be valid under compound-level correlation and heavy tails. Registered v7
  candidates, in order: (i) bounded betting-style e-variables on winsorized or
  signed per-line scores (validity under misspecification by construction,
  Waudby-Smith and Ramdas line of work, cited in the survey); (ii) a joint
  linear-mixed-model LLR that integrates the compound-level random effect (the
  correlation structure the diagnostic measured); (iii) a decorrelated-line menu
  (select a maximal subset of pool lines with pairwise |rho| < eps on training
  residuals, then the naive product is closer to a martingale). Candidate (i) is the
  most assumption-light.
- **Not established.** Any certified decision on this task family; any decision
  value of the world completion channel (now negative in two task-policy pairs);
  the LLM arm's value (Phase B remains registered-blocked).

## 8. Reproduction and artifact ledger

- `cd D:/MAESTRO && "D:/anaconda/envs/maestro/python.exe" -m research.viability_contrast.freeze --v6 --verify`
  (all_match true), then
  `"D:/anaconda/envs/maestro/python.exe" -m research.viability_contrast.run6`.
- Code/protocol: `research/viability_contrast/{protocol6.json, run6.py,
  freeze6.json}`; freeze machinery extended in `freeze.py` (version 7).
- Outputs: `outputs/viability_contrast_20261008/run6/{episodes.csv, summary.json,
  gate.json, world_fit.json}`.
- Post-hoc (outside the freeze, labelled): `tmp/resid_corr_posthoc.py`; smoke:
  `tmp/smoke6.py`.
- Literature base: `log/20261008/LITERATURE_SURVEY_20261008.md` (two citation
  groups kept apart).

## 9. Open items and next experiments

- v7 candidate (i): bounded betting e-variables (register before any scoring).
- v7 candidate (ii): mixed-model joint LLR with an explicit compound random effect.
- v7 candidate (iii): decorrelated-line menu; report how much menu is lost.
- The tau-gated llm_agent arm (protocol.json phase B; protocol6 Phase B) stays
  registered-blocked until a realistic arm passes a validity gate on this or a
  successor task.
- F09-F15 of the 2026-09 audit: the audit records were consolidated in the
  2026-10-07 publication; their status needs re-derivation from the consolidated
  tree before any further remediation is claimed (this block did not touch them).

## 10. Curation provenance

Written by the WorkBuddy session of 2026-10-08 from the frozen outputs only.
Sources read: `run6/{summary,gate,world_fit}.json`, the labelled post-hoc
diagnostic output, the v5/v5b dated records, and the retrieval results listed in
`log/20261008/LITERATURE_SURVEY_20261008.md`. No v1-v5b file was modified; `src/`
and `tools/` untouched. $0, 0 wells, 0 downloads.

- Released MAP/STATE-SE follow-up: five official weight/embedding files acquired
  and hash-verified, complete 146-candidate structure coverage recovered, released
  knowledge correction tested and rejected by reference selection. Compatible
  full-checkpoint GPU forward and causal CLS input obstruction audited; native
  biological comparison remains blocked. See `MAP_RELEASE_TEST.json` and the
  canonical [evidence section](../../research/EVIDENCE.md#map-released-weights-20261008).
  Nine behavioral/arithmetic groups, 25 reconstructed target rows, exact numerical
  repeat and 422 default core tests pass. No production promotion or Git publication.

- MAP runtime repair: restored the public bidirectional/NoRoPE intent on the
  declared Transformers4.30.1 API and evaluation-mode SDPA behavior. Real-weight
  input-path audit preserves all 499 persistent tensors and restores drug/gene
  sensitivity. Unsupported dose/time and unresolved named outputs are refused
  through the existing dual-core contract. Eleven research tests, 422 core tests,
  22 repository-shape tests and exact fresh-process coordinate repeat pass.
  The small synchronized batch comparison is slower/more memory intensive, so it
  is not enabled. See `MAP_RUNTIME_REPAIR.json` and the
  [canonical evidence](../../research/EVIDENCE.md#map-runtime-repair-20261008).
