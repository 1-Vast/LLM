# Dual-core innovation validation on PTV-1 / ProteinTalks (public-data replay), 2026-10-21

**Decision: `STOP_THIS_TASK_CONFIGURATION`.** On this release, with the re-implemented ppODE world model (hidden width 16), a static strong program, and
a bounded LLM program-editing search, neither core adds a useful capability over strong conventional comparators, and the combined system is NOT_TESTED because no
agent edit was accepted. This is a local negative on one public release with 7 final lineages (an estimation pilot); it is not a universal rejection of world
models or self-modifying agents. Everything here is public-data replay of an exposed release, never prospective discovery.

Package: `PROTOCOL.md` (frozen text), `FREEZE.json` (161 file hashes; final stage opened once afterwards, `STAGE_LEDGER.json`), `RESULTS.json` (= `RUN/final_eval/RESULTS.json`),
`RESOURCES.json`, `SOURCE_MANIFEST.json`, `CENSUS.json`, code `*.py`, `verify.py` (43 checks pass, no retraining, no further final outcomes), `test_study_software.py` (11 synthetic invariant tests pass).

## Data and design in brief
Source: ProteinTalks / PTV-1 (Nature paper, GitHub repo, Google Drive CSVs, SI; URLs, retrieval lines, commit and sha256 in `SOURCE_MANIFEST.json`). 18 stocks / 17 lineages,
63 single drugs, 59 pairs, 1,535 cell-by-perturbation units. Label = authors' published 24 h sensitive/resistant call (missing is missing; threshold, dose, replicate ids not in
the release; the pair label is a different, unauthenticated endpoint -> pair tasks NOT_TESTABLE_ON_THIS_ASSET). Lineages were assigned dev 5 / sel 5 / final 7 by hash before
labelled analysis; the unit of inference is the lineage. All 7 final lineages (BT20, HCC1187, HCC1395, HCC38, HCC70, MDA-MB-436, T47D) had a valid pool. The contested pool
(training label rate in [0.2, 0.8]) is the same 14 drugs in every final background, so backgrounds differ only in baseline proteome and labels (positives 3 to 10). Checkpoint
training exposure of the released model is UNKNOWN; it was not used. All data are exposed (public), dev/sel outcomes were used freely, the final outcomes were read once.

## Results (final stage, 7 lineages, 95% cluster bootstrap over lineages; margins delta_T = 0.09 precision@5, delta_E = 0.40 hits)

| Question | Estimate [95% CI] | Label |
|---|---|---|
| P1 T: M1 (ppODE) - B1 (strongest conventional, similarity-weighted prior), precision@5 | -0.229 [-0.286, -0.200] (M1 0.514, B1 0.743, oracle 0.886) | NO_USEFUL_GAIN_WITHIN_RESOLUTION (significantly worse) |
| M1 - M0 (logistic direct predictor on the same information), precision@5 | -0.171 [-0.200, -0.114] | NO_USEFUL_GAIN (worse) |
| M1 - M2 (no trajectory pathway); M1 - M3 (no fingerprint shortcut), precision@5 | -0.171 [-0.200, -0.114]; -0.086 [-0.200, 0.000] | NO_USEFUL_GAIN |
| M1 - B1 AUROC on pool; Brier improvement | -0.232 [-0.343, -0.119]; -0.068 [-0.135, +0.006] (M1 Brier higher) | NO_USEFUL_GAIN; INCONCLUSIVE |
| P2 Q: functional feedback update - no update, precision@5 | -0.029 [-0.086, 0.000] | NO_USEFUL_GAIN |
| Q: molecular feedback update - no update | 0.000 [0.000, 0.000] (the molecular update does not move the phenotype head) | NO_USEFUL_GAIN |
| Q: functional update - ordinary kernel update of the same model; - ordinary kernel update of B1 | -0.114 [-0.171, -0.029]; -0.229 [-0.286, -0.200] | NO_USEFUL_GAIN |
| Q: ordinary kernel update vs none (W, B1), precision@5 | +0.086 [0.029, 0.171]; 0.000 [-0.086, 0.086] | INCONCLUSIVE; NO_USEFUL_GAIN |
| P3 E: Aconv (conventional program edit) - A0, hits (W1) | +0.14 [-0.57, +0.86] | INCONCLUSIVE |
| E: A1 / A2 (LLM chains) - A0 | exactly 0 (accepted LLM edits: none) | NOT_TESTED as an effect (programs identical) |
| P4 E: A0 on W1 - static confirmation of B1's top 5 (same budget) | -1.14 [-1.43, -1.00] hits (2.57 vs 3.71; ceiling 4.43, random 2.45) | NO_USEFUL_GAIN (significantly worse) |
| E: W1 - W0 under A0 | -0.86 [-1.00, -0.57] | NO_USEFUL_GAIN |
| H_C combined (A1 with W1 vs A0 with W0/B1) | no accepted agent edit | NOT_TESTED |

Calibration on pooled pool predictions (n = 98): B1 Brier 0.207, slope 1.31; M0 0.218, 1.23; M1 0.275, slope 0.26 (strongly over-confident/uninformative); M2 0.275, 0.27; M3 0.268, 2.57.
Seed spread is large (M1 pool AUROC 0.57 / 0.59; M3 0.67 / 0.72). Headroom over the strongest comparator under the same contract: T 0.886 - 0.743 = 0.143 precision@5 (about
1.6 times the margin); E 4.43 - 3.71 = 0.71 hits (about 1.8 times the margin), with a noisy, optimistic ceiling, so even a perfect method could show only a modest useful gain here.
Interval half-widths: 0.04-0.10 precision@5 for the R and Q contrasts against B1, 0.21 hits for A0@W1 vs static B1, 0.71 hits for Aconv vs A0; the negatives against B1 are resolved, the Aconv contrast is not.

Molecular intervention response (1,293 authentic held-out treated single-drug proteomes, quantified proteins only): M1 predicts the CHANGE from baseline with correlation 0.23
(24 h: 0.227) versus 0.139 for baseline + mean shift and 0.127 for baseline + drug-specific shift (C2, C3), but its MSE is worse than copying the baseline (24 h: 0.0086 vs 0.0040;
scale error) and on target-node proteins it equals persistence (0.0073 vs 0.0073), so there is weak direction skill and no accuracy gain; M3's trajectory is unstable on target proteins
(MSE 0.83). Baseline reconstruction (copying x) is already accurate; this separates it from intervention skill. No claim of single-cell heterogeneity, arbitrary dosing or dynamics.

## The ten questions
1. **Exact innovation implemented.** (a) W: the published ProteinTalks `ppODE` (pointwise per-protein neural ODE over baseline abundance and a drug-target node flag, phenotype head over
   baseline + 6/24/48 h channels + fingerprint branch) re-implemented and retrained from scratch (hidden 16, not 64; masked losses; NaN fingerprints zeroed); (b) a feedback update
   (fine-tune on revealed support labels/proteomes); (c) a sandboxed executable-program environment with outside evaluator, legality and cost accounting; (d) a bounded LLM chain
   (A1) and restart (A2) editing program source, a conventional menu optimiser (Aconv), and a 2x2 of worlds x programs.
2. **New vs standard.** All components are standard (neural-ODE proteomics model, direct predictors, kernel updating, LLM code editing, menu search). The only study-specific pieces are the
   contracts, leakage controls and the environment. W is not a renamed multi-task model in architecture, but it performs worse than the direct predictor on the same information, so no
   algorithmic novelty is claimed or established.
3. **Did W add useful capability?** No, on this task. It is worse than the prior-based comparator for nominations (-0.229 precision@5), for calibrated probabilities and as a confirmation score
   (-1.14 hits); the trajectory pathway does not help (M2 is better than M1) and the extra molecular supervision does not translate into decisions. Weak direction skill for protein change exists
   (correlation 0.23 vs 0.13-0.14). Distinguishing evidence for the cause: the direct features (drug label-rate prior, baseline-similarity neighbour rate) explain the label; auxiliary supervision
   without the ODE was not built, so a mechanism-vs-supervision attribution is not possible.
4. **Did executable self-modification add useful capability?** No. The LLM chain returned the incumbent or tied/lost on development validation in all 3 generations; the restart returned one duplicated
   answer 3 times; nothing was accepted; A1 = A2 = A0 byte-for-byte, so the effect is exactly zero and no patch behaviour could be shown. The conventional menu found a +0.18 validation gain that
   is +0.14 hits [-0.57, +0.86] on the final lineages (INCONCLUSIVE, below margin). A tie is not improvement; no LLM-specific claim is made.
5. **Did inheritance improve subsequent tasks at matched cumulative resources?** NOT_TESTED: with no accepted program there is nothing inherited. A1 used 3 requests, A2 used 3 requests (6 requests,
   16,782 tokens in total, 0 failures) and the same evaluation compute.
6. **Did the combined system add value?** H_C NOT_TESTED. The exploratory conventional-edit x world interaction is +0.43 hits [0.14, 0.86] on 7 lineages, but it is a difference of small effects (the edit is -0.29 on W0 and +0.14 on W1), a positive interaction and not mutual learning, and the combined arm remains below the strongest conventional confirmation (-1.00 [-1.57, -0.29] for Aconv on W1 vs A0 on B1).
   Directional A->W and W->A learning: NOT_TESTED.
7. **Real molecular acquisition tested?** Yes, as Experiment Q on authentic 24 h proteomes, separately from R. Molecular feedback changed nothing (identical to no update): in this architecture it
   acts only through target-flag proteins and the trajectory parameters do not feed a phenotype change. The conditional predictor with the same molecular information beat the update arms
   (g_mol imputation precision@5 0.686 vs 0.486-0.514), and ordinary same-data updating did as well as or better than the update arms. In the program setting no accepted program queried molecularly; the
   price sweep (lambda 0.1 to 1.0) shows molecular-screening variants never beat static confirmation of B1's top 5 (the best, 2.71 hits at lambda <= 0.5, is +0.14 over A0 and falls to 2.0, below A0, at
   lambda 1.0; it is 1.0 hit below the strongest baseline). Experiment R (predicted state) does not establish Q; neither was positive. Cost-ratio range: break-even versus A0 between 0.5 and 1.0, never versus B1.
8. **Did the system beat direct functional confirmation?** No. Static confirmation of B1's top 5 yields 3.71 hits per background versus 2.57 for A0 on W1 and 2.71 for Aconv on W1 (and 3.14 for
   Aconv on B1, a conventional program that lost 0.57 to the static one on the strongest score; exposed-selected).
9. **Cause of failure and distinguishing evidence.** (i) The task is nearly saturated by the drug prior (headroom over B1 0.14 precision@5, 0.71 hits); (ii) W has a weak phenotype signal beyond
   the prior (seed-unstable, over-confident, slope 0.26) and its mechanism path is not exercised for 23 of 63 drugs; (iii) the feedback update cannot reach the head except through target proteins; (iv) the
   program space is small enough that tuned static procedures tie. Distinguishing evidence: B1/M0 on the same lineages (P1), the M1-M2 comparison, the ordinary-update arms, the Aconv-vs-LLM
   identity, and the unchanged molecular-update arm. Capacity (hidden 16 vs the paper's 64), 1-2 seeds and 7 lineages limit a universal conclusion; not tested: a larger ppODE, cross-protein
   interaction, a model with the same supervision but no ODE.
10. **Retain / revise / stop.** STOP_THIS_TASK_CONFIGURATION: with this release and these contracts there is no supported capability to build on. The only retained engineering assets are the
    sealed-outcome ledger, the sandboxed program environment with outside accounting, and the leakage-safe contracts. A redesign would need an asset where the prior leaves large headroom, a
    structured pathway with molecular-to-phenotype coupling, and enough independent backgrounds to detect the stated margin (the margin was not attainable with 7 backgrounds unless the effect exceeds about twice the margin).

## Deviations, faults and limits (all disclosed)
- First program-search evaluations lost some worker processes (scored as zero); detected before any LLM result was accepted, fixed (retry, refuse to score), and conventional search and A1 acceptance re-run;
  the dev-stage kappa grid was reproduced unchanged. No LLM request was repeated.
- Dev models were CPU-trained, selection and final GPU-trained (GPU run-to-run differences up to 0.22 in probability; correlation 0.993-0.998). Hidden width 16, 1-2 seeds, one label definition,
  controls heterogeneous, no dose/replicate ids; the final pool is the same 14 drugs for every background; probability calibration beyond AUROC reported only on pooled pool predictions.
- The Aconv program and A0 rule were fitted on exposed development episodes; the final stage is the only confirmatory use and is now itself exposed.
- Unrelated repository test failure (not caused here): `tests/test_repository_shape.py::test_repository_has_one_scientific_report_and_no_retired_release_tree` fails because of the concurrent `.build-1024-dgm-revision`.

## Resources (no currency claim)
GPU 3,911 s (selection 2,902 s incl. sel30 824 s; final training 1,009 s), formal CPU model training 13,040 s (dev), plus 6,334.95 CPU seconds in eight aborted selection attempts; total observed model-training CPU time 19,374.95 s. Final evaluation 1,031 s wall, program evaluations in a numpy-only interpreter. Functional units: 5.0 per
background per program (all programs); molecular units: 0 in every accepted/frozen program (menu variants: up to 2 x lambda). API: 6 requests, 16,782 tokens, 0 failures (2 requests and about 33,000 tokens unused).

## Closest conventional explanation for every surviving claim
No claim of gain survives. For the observed weak change-direction skill of M1 the closest explanation is baseline-plus-mean-shift (C2/C3) with imperfect scaling; the distinguishing experiment is a model with
identical molecular supervision but no ODE.
