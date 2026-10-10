# P0.6: sentinel source-repeat audit and channel-selection shadow trial

**Status: design only. No treated expression was downloaded, no real measurement was purchased, and no decision improvement or LLM advantage was tested.** This prospective plan follows the exposed v3 study and the metadata-only census. It does not retrofit v3 or preregister an already observed RNA outcome. A separate execution protocol and immutable freeze are required before any proposed treated-cell RNA is opened.

## What the available source units permit

The pinned `arcinstitute/State-Tahoe-Filtered` revision is
`fdf87abece385feea6fa5e9944ab46e173b6af50`. The previously authenticated metadata census in `pairwise_v3/data_availability/AVAILABILITY.json` contains the following records:

| Exposed source file | Cell line | Exact drug-dose-unit labels | Treated label/plate strata | Strata per label | Minimum full-QC cells in a stratum |
|---|---|---:|---:|---:|---:|
| c40.h5ad | NCI-H661 | 146 | 292 | 2 | 15 |
| c44.h5ad | SW 1088 | 146 | 292 | 2 | 18 |
| c45.h5ad | SW 1271 | 146 | 292 | 2 | 31 |

For each of these files, every label occurs on exactly two distinct plates; each treated label/plate stratum contains one sample ID. Thus two source observations are available for every recorded condition, but no third source repeat is present in this census. Drug components, concentration and unit match. The new `literature/SOURCE_QUALIFICATION.json` authenticates the original Tahoe v2 methods' dataset-wide **24-hour** exposure and authors' description of **plate14 as a biological replicate of plate6**. All 24 proposed treated strata and eight P0.5 control strata join official pinned sample/plate/condition metadata exactly. Exposure time is a verified global protocol, not a per-sample timestamp; culture preparation dates, source randomization and between-batch exchangeability remain unknown. Other plate pairings are not promoted to biological repeats by this statement.

The Tahoe release describes a plate as a plate in which a mixed-cell spheroid was seeded and treated, and a sample as a treatment-sample identifier. Cell-line partitions can therefore reuse the same sample ID. The proposed 24 cell-line/label/plate strata below contain only 12 distinct plate/sample IDs. They cannot be counted as 24 independent cultures. A/B source plates in the old scalar packet are also distinct from the hash-split `meanA`/`meanB` cell subsets in the extraction recipe. Splitting cells from one source sample yields sampling pseudo-replicates only.

The historical `24`-hour replay value was simulation metadata. The fresh source evidence independently supports 24 hours for the released Tahoe protocol; this supersedes the old unknown-duration state without changing its immutable receipt. A channel requiring explicit per-sample timing still lacks that field. The exposure claim should identify its global-methods provenance rather than silently copying the simulation value.

## Release requirements before treated RNA

1. Authenticate the exact 39 original data coordinates in both proposed source files, preserving ordered coordinates, symbols, endpoint weights and provenance. An endpoint-coordinate certificate is not a certificate for all 2,000 HVGs or a STATE/MAP checkpoint decoder axis.
2. Preserve the newly verified selected sample/plate/condition joins, global 24-hour protocol and author-described plate6/14 biological-repeat status. Join further experimental metadata when needed: culture preparation, readout protocol, pooled membership and batch/randomization. Global protocol matching permits a source-supported common-time description; it does not establish per-sample exposure timestamps or exchangeable independent new cultures. Those stronger uncertainty claims remain blocked.
3. Freeze a new metadata-derived cell manifest, exact ranges, byte cap, QC rule, reference-control assignment, estimators, split structure, channel costs, action contract, code and verifier. Record the prior v3 and P0.5 exposures. Do not alter earlier freezes.
4. Keep target B evaluation expression outside the reliability fitter and channel selector. Sentinels used to fit reliability cannot subsequently count as unseen terminal validation units. If the available two observations are both consumed to fit a sentinel source discrepancy, neither is an independent third confirmation.

P0.5 control-only covariance results, if completed, permit a control-cell sampling statement. They do not by themselves release A propagation, a treated-response noise estimator or an RNA-to-function bridge.

## Metadata-only bounded sentinel proposal

`literature/METADATA_REPEATS.json` preserves the initial metadata-only c40/c44 proposal. Subsequent primary-source reading found that the authors excluded NCI-H661, NCI-H596 and NCI-H2122 from later analyses because of consistently low condition counts, and required at least 50 cells per analysis condition. This does not invalidate all retained NCI-H661 cells, but it is a concrete source quality concern for a scarce-data reliability panel.

Before any RNA freeze, `literature/UPDATED_SENTINELS.json` therefore supersedes that proposal with **c44/SW 1088 and c45/SW 1271**, requiring plate6/plate14 and at least 50 full-QC cells per stratum. There are 86 eligible labels. It keeps the original outcome-free rule: sort SHA256 of `p06-sentinel-metadata-only-v1|label` and take the first six. The selected labels happen to remain:

- Ritonavir, 5 uM.
- Docetaxel, 5 uM.
- Retinoic acid, 5 uM.
- Ciclopirox, 5 uM.
- Tofacitinib, 5 uM.
- Fusidic acid, 5 uM.

This is a low-cost source-diagnostics panel, not a representative dose-response panel: all selected labels are 5 uM. Conditions match the authenticated global 24-hour protocol, with per-sample timing unavailable. The proposed payload is 6 labels × 2 cell-line partitions × 2 plate sources × 32 complete 2,000-gene float32 cell vectors = 768 vectors = **6,144,000 treated-expression bytes**. Actual treated-expression bytes in this task are **zero**.

The P0.5 plan selects 250 cells across eight c40/c44 control strata, corresponding to **four distinct pooled sample IDs on two plates**, not eight independent cultures. Its full endpoint axis certificate failed, so those 250 cells were not read and no control-noise estimate is available. The updated sentinel design additionally needs c45 endpoint certification and a new matched c45 control manifest. Existing c44 control metadata may inform selection; previously blocked control RNA must not be described as available. Matched control roles and sample weights must follow the frozen source recipe; equal averaging of unequal source groups changes the original endpoint. More reference cells require separately registered ranges and charges. The proposed 6,144,000 treated bytes plus the earlier 2,000,000 planned control bytes would equal 8,144,000 expression bytes, and adding the earlier 5,083,146 metadata bytes would exceed the old 10 MB aggregate pilot cap. P0.6 needs a new explicit cap and cumulative accounting that also includes prior axis reads; it must not silently inherit a 10 MB allowance.

For each treated stratum, select 32 cells by a new preregistered barcode/row hash and retain each complete gene vector. Split into two disjoint 16-cell subsets for a sampling-repeat diagnostic; also retain the complete 32-cell mean. These cell subsets are not new sample units. With 32 cells, estimate `var(X @ w, ddof=1)/32`, with the original scalar weights `w_j=+1/39`; do not replace it by an inverse mean 2,000-gene precision proxy. A source group with fewer cells would require its actual n, but the current sentinel eligibility explicitly avoids that case.

Report within-source full scalar covariance, diagonal-only variance, their difference and ratio, vector-bootstrap intervals conditional on cell exchangeability, sample counts, both source means, plate-reference means, and paired-source differences. Report the two cell halves descriptively, without treating repeated random splits as independent measurements.

## Separating identifiable quantities from speculative decomposition

For candidate a on source plate p, write a scalar response as

`Y[a,p] = mean_treated[a,p] - mean_reference[p]`.

The conditional independent-cell sampling approximation is

`Var(Y[a,p]) = Var(mean_treated[a,p]) + Var(mean_reference[p])`

only when the two cell sets are conditionally independent. Both terms are endpoint-specific full-gene scalar variances. Known cell/sample sharing must be retained. If two candidates share exactly the same reference mean, that reference term cancels from their within-plate difference; adding it independently to both candidates overstates contrast noise. Across distinct reference groups, cancellation cannot be assumed. Related source samples can still introduce dependence after cell sets are disjoint.

With only two source observations, `Y[a,plate6] - Y[a,plate14]` combines treatment/source mismatch, plate/reference shifts and sampling error. Its squared difference is not automatically twice a biological measurement variance. A common plate offset can be described from multiple sentinels, but its removal does not identify causal batch variance, nor does a six-label panel establish a stable input-dependent reliability model. Biological effects, plate bias and treated sampling error cannot all be separated from two confounded source groups without additional assumptions or replicates.

P0.6 should initially deliver source discrepancy and conditional sampling diagnostics. A hierarchical model may be a subsequent exploratory sensitivity analysis, with explicit unidentified terms and broad uncertainty. It must not produce a biological variance fraction from this panel.

## Channel-selection shadow contract

Register distinct information actions rather than assuming that every cheap A observation is equally informative:

| Proposed action | Required provenance | Permitted immediate interpretation |
|---|---|---|
| Inspect source/condition metadata | Typed receipt, source identity, time and repeat mapping | Resolve whether a channel is eligible |
| Inspect additional matched DMSO controls | Certified endpoint coordinates and exact source rows | Reduce uncertainty about conditional control sampling |
| Inspect another disjoint cell subset of the same treated sample | Preregistered source rows, no overlap, same sample | Sampling-repeat information; correlated source error remains |
| Inspect a separate recorded-condition treated source | Authenticated matching conditions and repeat type | Source-discrepancy evidence; biological independence is a separate question |
| Direct B measurement or stop | Qualified endpoint/measurement contract | Strong terminal-information comparator or preserve baseline |

During the initial shadow trial, an action is a recommendation only. No tool purchases RNA or changes the production posterior. Missing eligibility fields route to metadata certification or stop. Query price, latency, failure probability, bytes, simulated profile charges and new plate starts are different quantities; report them separately until an authenticated conversion to endpoint utility exists.

Use frozen STATE means and the complete 146-action menu. Freeze boundary comparisons from pre-A information. A future noise-aware boundary heuristic can rank the **conditional variance reduction of a candidate difference**:

`[C_BA(i,q) - C_BA(j,q)]^2 / [Sigma_latent_AA(q,q) + R_observation(q,q)]`.

This expression is appropriate only if latent response covariance and observation covariance are separately qualified. If an empirical A covariance already includes measurement variation, adding R again double-counts noise. The existing observed-residual model and a separately noise-corrected latent model are different contracts, not interchangeable formulas. Positive variance reduction is not positive NetVOI, reliable ranking correction or permission to propagate evidence. Preserve shared-control and repeated-source covariance for multi-observation channels.

Compare three shadow recommenders on identical receipt menus: fixed deterministic qualification router; cheapest eligible channel with stable identity tie-breaking; and a noise-aware boundary proposer. Keep no-update, strong shrinkage, direct-B and stop available in any later executed policy study. Log every recommendation, required missing fields, eligibility denial, estimated uncertainty and abstention. LLM use is unnecessary for this deterministic shadow; a later LLM comparator must receive exactly the same tools, receipts and budgets.

The first shadow endpoints are legality and reproducibility: no unqualified channel is proposed as an executable measurement, no unavailable A is released, no evaluation B is read, all costs are explicit, and identical inputs yield identical traces. Synthetic typed scenarios may test these contracts but cannot demonstrate biological or decision benefit.

## Future experimental evaluation, if qualification succeeds

Fit reliability using development source units only. Whole culture/sample/plate batches that share a reference must remain grouped across splits; do not split cell-line partitions of a pooled sample into supposedly independent folds. Condition-level evaluation and novel-culture evaluation are distinct claims. The current two-background, two-plate sentinel panel is too small and exposed for risk certification.

First isolate updating from acquiring: all matched-information arms read the same charged A channel and compare no update, fixed shrinkage, learned shrinkage, condition-gated feedback and MAP/structure controls. Then separately compare channel-selection policies. Freeze terminal actions before evaluator B opens. Sentinels spent on reliability fitting are development information; confirmation needs additional untouched measurement/sample units. If these units do not exist, report that the data support development diagnostics only.

Register actual endpoints: Top-5 B utility, candidate-pair regret, corrected/harmful flips relative to each arm's own mean, effective coverage, channel purchases, profile/plate/time use, and probability calibration. Report global RNA MSE secondarily. Use clustering by authenticated experimental unit, retain full menus with static fallback, disclose near-ties and their prospective tolerance rule, and adjust registered multiple contrasts. Do not select a post-score threshold that turns this development panel into a no-harm certificate.

## Literature interpretation

The primary-source receipts and applicability notes are in `literature/CLAIMS.json` and `literature/REVIEW.md`.

- rMFBO motivates a protected primary-only baseline and source rejection. Its theorem needs a correctly specified known multi-output GP and smoothness assumptions, and compares an augmented robust budget with a smaller baseline budget. It is not a same-budget risk guarantee for MAESTRO.
- Input-dependent MFBO motivates source-and-condition-dependent reliability and uncertainty over noise. Its GP/Gaussian/independent bounded-noise assumptions do not cover unknown shared plate bias automatically.
- muscat motivates sample-level inference and preserving experimental units. It does not turn cell halves into biological repeats.
- Systema motivates perturbation-specific diagnostics and strong average/identity baselines. Its published examples concern genetic perturbations; its metrics are not a proof of chemical action utility.
- BioPert motivates testing a measured biological reference response against chemical representations, reference-copy and random controls. The September 29, 2026 release is a preprint; its abstract is authenticated, while full-text methods were inaccessible during this retrieval. No author-reported performance is adopted as a MAESTRO result.
- STATE issue #279 records a user-reported ordered-HVG reproducibility gap. It is an issue discussion, not an authoritative decoder mapping. Certifying the original data's 39 endpoint coordinates does not close that broader model-axis gap.
