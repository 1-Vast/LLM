# Experiment record: viability-contrast v5 (2026-09-28, evening)

> - **Path**: `log/20260928/VIABILITY_CONTRAST_V5.md`
> - **Purpose**: Record block 2 of the day (protocol `viability-contrast-5`), continuing the
>   viability_contrast block whose v1-v4 arc ran earlier the same day. The owner's brief: keep
>   the dual core (agent + virtual cell) central, prefer the most novel registered option,
>   use cheap already-local data, allow the .env API for verification, and keep upgrading the
>   existing framework rather than starting new scaffolding. The full block record is
>   `research/viability_contrast/README.md`; this file is the dated experiment record.
> - **Core points**: v5 ran the three registered v4 follow-ups plus the gated genetic tier:
>   a learned low-rank completion world (rank-16 SVD basis, exact Gaussian posterior, precision
>   blend with the class templates), MI and Thompson acquisition against the v4 margin rule on
>   the same world, an extended tau grid (to 55), and a CRISPR buyable-measurement tier gated
>   on a finite realistic tau. Gate v5 FAILED: no realistic arm certifies in any fold; the
>   certification frontier (min wrong rate where >= 20 calibration episodes decide) is
>   0.55-0.81 against the 0.05 target, while the imported oracle stays at 0.988 correct at
>   0.002 wrong with 2.3 measurements. Non-margin acquisition reduces margin inflation in the
>   registered direction (MI: 63-70% wrong at tau 8 vs margin's 77-88%) but does not approach
>   certification. Phase G5 never activated, so the genetic arms and the llm_agent unlock
>   remain registered-blocked; the genetic channel fit is reported unconditionally with a
>   disclosed baseline flaw and a post-hoc fair-baseline refit. Conclusion registered: the
>   bottleneck is no longer the world's point predictions; the next iteration is a
>   reformulation (a statistic the acquisition cannot game, or the native two-compound
>   contrast), not a fourth world model. Nothing promoted; `src/`, `tools/`, production
>   defaults unchanged; $0, 0 wells, no download.

## 1. Record control

- **Tree as found.** The day's earlier record (`log/20260928/README.md`, dual_core_v2) and the
  v1-v4 viability_contrast freezes (`freeze{,2,3,4}.json`, 07:37-08:08Z) untouched on disk.
- **Pre-registration.** `research/viability_contrast/protocol5.json` written before any v5
  episode was scored; `freeze5.json` (2026-09-28T10:28:35Z) digests the protocol, prepare5.py,
  world5.py, run5.py and the pack (including the new `genetic.npz` / `class_gene.json`).
- **Pre-freeze exposure.** A synthetic smoke run (`tmp/smoke5.py`) exercised every arm's code
  path including the genetic-purchase branch, printing shapes only; no pack score was read
  before the freeze. Descriptive pack statistics (39/39 classes mapped to a primary gene, 37
  CRISPR-mapped genes, 370 lines, density 1.0) were computed by `prepare5.py`, which builds
  the addition without reading outcomes.
- **Owner decisions.** Scope: the most innovative registered option (three-piece core + CRISPR
  tier). LLM arm: unlock if and only if a realistic arm reaches a finite tau (approved).

## 2. Research questions and hypotheses

From `protocol5.json`, treated as hypotheses:
1. Does a learned in-context completion world (precision blend) certify where the kNN channel
   could not? (v4 registered target)
2. Does a non-margin acquisition objective (MI / Thompson) restore margin calibration under
   planning? (the Goodhart mechanism measured in v2/v3)
3. Does the extended tau grid expose a qualifying region the v4 grid could not see?
4. (Gated) Does a buyable CRISPR dependency channel earn budget against viability curves?
5. (Unconditional) Does the genetic regression channel beat the class template on training
   log-likelihood, under the keep-if-it-helps discipline?

## 3. Materials, data and computational environment

- **Data.** PRISM Repurposing secondary curves (local since 2026-08-23; 517 compounds x 443
  lines, 39 classes, 490 units; the frozen v1 pack, byte-identical) and DepMap
  `CRISPRGeneEffect.csv` (370 menu lines x 37 mapped class genes, density 1.0). No download.
- **Environment.** `maestro` conda env (Python 3.11.16), CPU only. Runtime 38 min for the
  frozen run; the .env DeepSeek API was not called (the llm_agent unlock never activated).

## 4. Experimental design and controls

- **World5.** Per fold: median-centred, median-imputed truncated SVD basis (rank selected per
  fold from {4, 8, 16} by simulated-episode log-likelihood); exact Gaussian posterior over
  latent coefficients from purchased readings; precision blend of the class template with the
  completion per hypothesis and line. Registered approximations: basis median-imputation;
  one-of-~400-rows basis leakage during rank selection (held-out compounds never contribute).
- **Acquisition.** Three rules on the SAME world: margin (v4 port, Goodhart control), MI
  (expected class-entropy reduction, top-H = 8, K = 7 quadrature), Thompson (seeded
  sampled-class margin). Masked and shuffled controls per rule; tau per realistic arm per
  fold by the v2-v4 split-half rule; grid extended to (0..55).
- **Genetic tier (G5).** Annotation-only class-to-gene map (mode of the first-listed target
  symbol); per-class OLS of AUC on the line's dependency, kept if training LL improves;
  one-step value-of-information acquisition over a restricted menu; cost 1 budget unit
  (registered as a favourable-to-genetics bound). Gated per fold on a finite realistic tau —
  a calibration-side condition, so held-out outcomes never decide what runs.

## 5. Experiment register and results

- **Gate v5: FAILED.** `run5/gate.json`: no certifying arm; shuffled coverage check passed.
  All realistic and control arms: coverage 0.000 at tau = +inf; oracle imported unchanged.
- **Frontier.** Minimum calibration wrong rate with >= 20 decided: 0.55-0.81 across arms and
  folds (target 0.05). At tau >= 21 only 1-14 episodes decide per fold.
- **World fit.** Rank 16 selected in all folds; rank-LL differences <= 0.3% relative between
  ranks — the learned channel's gain is real but thin.
- **Goodhart, refined.** tau 8: margin 77-88% wrong (54-99 decided), MI 63-70% (54-63),
  Thompson 66-86% (59-66). Direction as registered, magnitude insufficient.
- **Genetic channel (unconditional).** Frozen fit: 195/195 class-fold models kept — a
  baseline flaw was discovered when reading the output (pooled one-mean baseline). Post-hoc
  fair-baseline refit (`tmp/genetic_refit_posthoc.py`): 35-36/39 kept per fold, median gain
  ~0.1 nat/pair, still variance-model-sensitive. Mean-level information NOT established.

## 6. Deviations, failures and corrections

- **Genetic baseline flaw.** The frozen `world5.fit_genetic` compares the OLS against a
  pooled median, not the per-line template. Discovered while reading the unconditional
  channel report; no decision was affected (G5 never ran). Corrected only as a labelled
  post-hoc diagnostic; the registered correction belongs to any future re-registration.
- **Boundary regression note.** Fold 0, tau 21: v4 kNN 9 decided/1 wrong vs v5 margin 10/9.
  Tiny counts; registered as a mechanism hypothesis (tighter world variance strengthens
  margin selection pressure), not a finding.

## 7. Interpretation and claim boundaries

- **Measured.** The certification frontier does not move under three world models and three
  acquisition rules; non-margin objectives reduce margin inflation without restoring
  calibration; the learned channel's predictive gain is real but thin; phase G5 blocked.
- **Proposed.** The next iteration is a reformulation: certify on a statistic the acquisition
  does not optimise, or move to the native two-compound mechanism contrast (A vs B over one
  line panel), whose two-hypothesis space is one where budget-16 evidence can dominate.
- **Not established.** The genetic channel's mean-level information (variance-model-sensitive
  comparisons) and its decision value (tier never ran); whether any learnable world can
  certify on this task as registered (the required accuracy approaches clairvoyance, but no
  impossibility result is claimed).

## 8. Reproduction and artifact ledger

- Code/protocol: `research/viability_contrast/{protocol5.json, prepare5.py, world5.py,
  run5.py, freeze5.json}` (digests in freeze5.json; `--v5 --verify` passes).
- Outputs: `outputs/viability_contrast_20260928/run5/{episodes.csv, summary.json, gate.json,
  world_fit.json}`; pack addition `prepared/{genetic.npz, class_gene.json}`.
- Post-hoc (outside the freeze, labelled): `tmp/genetic_refit_posthoc.py`; smoke: `tmp/smoke5.py`.
- Block record: `research/viability_contrast/README.md` section 3.6 (this file is the dated
  record; the README is the accumulating block record).

## 9. Open items and next experiments

- Reformulation (i): a certification statistic dual to the margin that acquisition cannot
  game (design question: what statistic is both decision-sufficient and selection-invariant?).
- Reformulation (ii): a two-compound contrast task on the same pack (registered candidate for
  protocol 6); the framework's native estimand `K = (h_i, h_j, delta, q, a, Y, rho, D)`.
- The tau-gated llm_agent arm (DeepSeek via .env) remains registered-blocked until any
  realistic arm reaches a finite tau on this or the reformulated task.
- If the genetic tier is re-registered: fix the keep-if-it-helps baseline to the per-line
  template with a shared variance model before any channel claim.

## 10. Curation provenance

Written by the WorkBuddy session of 2026-09-28 evening from the frozen outputs only. Sources
read: `run5/{summary,gate,world_fit}.json`, the v3/v4 frozen outputs (imported arms), and the
block README. No file of the v1-v4 arc was modified; `src/` and `tools/` untouched.
