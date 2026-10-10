# A/B source and transfer audit

Study date: 9 October 2026. This is a frozen diagnostic analysis of already exposed development data. It does not score a new outer-target policy, certify biological efficacy, or identify all causes of measurement disagreement.

## Findings

The attached raw correlations reproduce exactly. Across 43 complete backgrounds, the median within-background Pearson correlation between candidate A and B responses is:

| Candidate group | Candidates | Median Pearson |
|---|---:|---:|
| Full menu | 146 | 0.162280 |
| 0.05 uM | 19 | -0.010175 |
| 0.5 uM | 20 | -0.022951 |
| 5 uM | 107 | 0.201749 |

These are correlations across drugs and doses within a background. They are not correlations of conditional residuals, repeatability estimates, or a test that every possible A observation is uninformative.

The historical source recipes and all 45 metadata-census hashes were verified from Git `91b0c10`. Every one of the 146 packet candidates pairs **two different plate groups**. Packet A/B do not refer to the within-well cell hash halves named `meanA` and `meanB` in the original source code. Confusing these two definitions would overstate independent repeat evidence.

Original responses subtract the reference-half DMSO mean from the same plate; basal DMSO cells are separate. Training treated summaries used at most 32 sampled cells per well, followed by full-QC selection. Candidate groups can therefore share reference-control errors within a plate. Original `precision_B` is the inverse mean sampling variance across 2,000 genes, not an authenticated variance of the 39-gene scalar endpoint. Per-gene covariance is needed to obtain the latter correctly.

The cached packet contains plate identities but does not preserve joined sample/culture-batch identifiers, scalar replicate noise, or authenticated treatment duration. The `24` hours in an earlier paid-replay action is **simulation metadata**, not established source exposure time. All 102 original upstream assets declared by the packet recipe are absent locally. Consequently, biological variability, plate/source effects, treated-cell sampling noise and control noise remain **not separately identifiable** from these scalar values. No variance fraction is attributed to them.

## Training-only transfer checks

For each of the original 387 outer-history episodes, three historical inner folds exclude both the outer background and the entire inner validation group from means, offsets and residual moments. The analysis never reads outer A/B for these transfer checks. It also does not evaluate an alternative-query policy.

At eight histories, the fixed boundary query has model-information rank **64** of 146 at the median; its pair-variance reduction is **0.242372** of the model maximum. Dose support reaches **8.364** of the nine frozen pairs on average. This reproduces the attached diagnosis. It establishes that the boundary rule is not generally the model's most informative query; it does not establish that maximizing this imperfect model proxy improves decisions.

| Histories | Zero-increment residual-pair MSE | Full old transfer | Old transfer at alpha 0.1 |
|---|---:|---:|---:|
| 4 | 0.000595672 | 0.022467294 | 0.000831643 |
| 8 | 0.000525264 | 0.000566513 | 0.000525301 |
| 16 | 0.000494709 | 0.000504533 | 0.000494479 |

These values describe historical inner-held **residual-pair prediction**, not terminal RNA utility. Full propagation is unstable, especially when inner fitting leaves only two or three backgrounds. This can arise from unreliable small-sample slopes and small A denominators; it cannot be assigned a biological cause from the packet alone.

The old support gate admits 0/516, 295/1,032 and 2,016/2,064 inner validation cases at 4/8/16 histories. A separately frozen conditional-diagnostic phase uses fixed public basal RBF geometry, continuous support, and independent fixed-ridge A/B mean adapters. The public geometry uses all 45 unlabeled basal rows, including outer public states: **it is transductive, not an independent external reference**. All available cases receive positive continuous weights, eliminating the old geometric collapse. Positive weight alone does not demonstrate valid transfer or safe updates.

The second phase recomputes both mean models and their residual banks before validating each inner-held group. A residual's own conditional prediction excludes its labels. Lambda is fixed at 10 for both A and B, so tuning cannot indirectly reuse a residual's own outcome. This phase includes baseline, molecule, MAP knowledge, Morgan and identity-permuted knowledge under the same procedure.

| Histories | MAP conditional zero-increment MSE | Old covariance, alpha 0.1 | Refit covariance, alpha 0.1 |
|---|---:|---:|---:|
| 4 | 0.000596264 | 0.000834860 | 0.000834820 |
| 8 | 0.000526443 | 0.000526461 | 0.000526442 |
| 16 | 0.000496795 | 0.000496559 | 0.000496550 |

At eight histories, correcting both means and refitting covariance barely changes residual-pair MSE. At sixteen histories, alpha 0.1 gives a descriptive reduction of roughly 0.05% relative to zero increment; similar small changes occur for the nonknowledge controls. This is not evidence of useful knowledge-specific transfer or a new target decision benefit. It does show that the software's mean/residual alignment can be repaired without assuming that the measurement has sufficient information.

## What remains solvable

1. Recover small source-repeat summaries, matched plate controls, cell counts and sample-to-plate joins before attempting a noise/source/batch decomposition. Large full-dataset downloads are unnecessary if those summaries can be authenticated.
2. Validate transfer slopes and their direction stability on complete held-background pipelines. Cross-fitting a slope on a residual matrix computed using validation labels would still leak information through its means; the whole pipeline must be refitted.
3. Treat coverage, residual-transfer reliability and purchase value as different questions. RBF effective sample count can be high because high-dimensional distances concentrate, so its continuous weight is a heuristic rather than proof of scientific support.
4. Compare zero propagation and strong shrinkage before selecting a high model-information query. Evaluate active acquisition only after its predictions, purchases and final commitments are frozen. Preserve the option of direct B verification or a different observable when this A proxy is unsuitable.

The endpoint remains a mean of 39 mapped transcript changes, including both pro- and anti-apoptotic gene-set members. Residual-pair MSE has squared endpoint units; pair regret has endpoint units; terminal top-five utility is a sum of five endpoints. None is a measured apoptosis rate, viability outcome or monetary utility. Repeated seeds, candidate pairs and overlapping inner fits do not create additional independent biological units. STATE pretraining exposure is unchanged.

## Reproduction and integrity

Run from the isolated worktree root:

```powershell
python research/decision_value/pairwise_v3/p0/audit.py run --freeze FREEZE2.json
python -m research.decision_value.pairwise_v3.p0.conditional run
```

Both producers refuse to overwrite their output directories. A fresh reproduction must use an isolated checkout/output location containing the declared assets. `PORTABLE_CLOSURE.json` enumerates exact source/input/output files and hashes. Scalar-cache arithmetic is reproducible without raw Tahoe assets; fresh raw biological reconstruction remains blocked.

Outputs are in `outputs/decision_value/pairwise_v3_p0/`, with corrected-mean training diagnostics in its `conditional/` subdirectory. Each successful phase has a receipt containing output hashes. Neither phase changes the old study or production code.

The first original-channel attempt reached diagnostic serialization but failed on a NumPy integer count. Its producer, freeze and partial output directory are preserved. `AMENDMENT.json` discloses the native-integer serialization correction; `FREEZE2.json` freezes the revised producer. No formulas, splits, source values or diagnostic endpoints changed.

## Verified methodological sources

Small primary-source receipts, abstracts and HTTP response hashes are in `LITERATURE.json`:

- [Chernozhukov et al., Double/Debiased Machine Learning](https://arxiv.org/abs/1608.00060): motivates cross-fitting nuisance predictions; it does not make this predictive study a causal estimator or guarantee residual covariance accuracy.
- [Shah and Peters, The Hardness of Conditional Independence Testing and the Generalised Covariance Measure](https://arxiv.org/abs/1804.07203): clarifies residual-regression inference assumptions; near-zero covariance does not imply absence of all conditional information.
- [BATCHIE, A Bayesian active learning platform for scalable combination drug screens](https://www.nature.com/articles/s41467-024-55287-7): establishes active biological screening prior art and the need for task-specific prospective comparisons. It does not validate the present RNA proxy.

## Cheap source-recovery path

The pinned public [State-Tahoe-Filtered release](https://huggingface.co/datasets/arcinstitute/State-Tahoe-Filtered/tree/fdf87abece385feea6fa5e9944ab46e173b6af50) remains accessible through exact byte-range requests. A metadata-only probe selected the three smallest **complete-menu, previously exposed training** files: `c40.h5ad` (NCI-H661), `c44.h5ad` (SW 1088) and `c45.h5ad` (SW 1271). Twelve HTTP 206 reads downloaded **3,230,358 bytes** of drug-dose, plate, sample and QC codes. Every code-array hash matched the archived census. The smaller `c36` and `c39` files were excluded because their menus are incomplete.

The recovery plan then reacquired metadata for `c40` and `c44` to select exact DMSO reference-cell rows. Cumulative actual metadata transfer was **5,083,146 bytes in 20 authenticated range reads**; no expression byte was requested. The selected plate6/plate14 pair appears in 92/146 original candidate bindings. The plan enumerates eight source sample groups, 250 full-QC reference cells, and exact 8,000-byte X_hvg ranges. Their future RNA payload is **2,000,000 bytes**; metadata already read plus that proposed payload totals **7,083,146 bytes**, below the 10 MB pilot cap. Sample identity and common plate membership do not establish independent cultures.

The planned 39-gene control-noise study remains **BLOCKED/GENE_AXIS_AUTHENTICATION**. Historical coordinates are declared in the old protocol, but the complete 1,969 named/31 null coordinate identity file and its original gene-by-gene verification receipt are unavailable. That mapping was authenticated by comparing X_hvg against log1p of raw X; it was not a native ordered-gene annotation that can be recovered by reading HDF5 metadata. Recover the original hash-matching identity file, or first register a bounded control-only raw-X/X_hvg equality audit. Preserve unresolved coordinates as null and never guess their names. No RNA variance estimate was produced, and no control or treated outcome was inspected. This blocks a **fresh scalar-noise reconstruction**, while the authenticated cached replay remains executable.

The concrete queue, byte receipts, cell counts and future row ranges are in `../data_availability/SOURCE_RECOVERY_PLAN.json`; `../data_availability/AVAILABILITY.json` contains the initial coverage census. Producer and receipt hashes are in `../data_availability/SOURCE_HASHES.json`. After axis recovery, the next frozen pilot should compare scalar endpoint variance with the diagonal-only weighted 39-gene variance, `sum(w_g^2 s_g^2)`, and examine both after division by 32. This isolates the within-control gene-covariance contribution. The old mean-of-2,000-gene-variances proxy should remain a separate diagnostic: it also differs in endpoint and scale. These checks cannot by themselves identify biological versus batch variation or demonstrate new decision value.
