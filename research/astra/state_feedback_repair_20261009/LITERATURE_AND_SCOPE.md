# Joint feedback repair: literature and scope

This study tests whether first-well A feedback should update terminal-well B
through a fitted joint residual distribution. STATE predictions and the named
39-gene RNA endpoint remain fixed. Gaussian conditioning, correlated knowledge
gradient (KG), and decision-focused losses are established methods; a useful
contribution here must be an observed, equal-budget improvement with correct
source separation.

## Mechanism and primary literature

For joint residual covariance blocks C_AA, C_AB and C_BB, observing residual
r_A(q) updates B by C_BA[:,q] * r_A(q) / C_AA[q,q], with the corresponding
conditional covariance reduction. Additional measurement variance belongs in
the denominator only if it is excluded from the fitted observed-A residual
variance. Otherwise it would count the same noise twice. A and B are distinct
source wells, so their relationship must be estimated rather than assumed to be
one latent response plus independent observation noise. The zero residual mean
and fixed 0.5 diagonal shrinkage are bounded modeling assumptions, not calibrated
uncertainty guarantees.

| Primary source and inspected depth | Implication |
| --- | --- |
| Frazier, Powell and Dayanik (2009), [correlated normal KG](https://doi.org/10.1287/ijoc.1080.0314); verified publisher metadata/abstract | Dependence can inform acquisition. Its ranking-and-selection guarantees do not transfer automatically to one A observation per candidate and a separate B endpoint. |
| Elmachtoub and Grigas (2022), [Smart Predict, then Optimize](https://doi.org/10.1287/mnsc.2020.3922), [author preprint](https://arxiv.org/abs/1710.08005); targeted full-PDF introduction and consistency assumptions | Prediction MSE and decision regret differ. SPO+ is an established surrogate, not implemented or validated by the present feedback repair. |
| Mandi et al. (ICML 2022), [decision-focused learning through ranking](https://proceedings.mlr.press/v162/mandi22a.html); official full PDF, especially sections 4.1-4.5 | Feasible-set ranking and pairwise objective differences matter. Lower global MSE need not improve top-five membership. The present gain grid still uses reference MSE; terminal B utility tests whether posterior repair closes that gap. |
| Kuleshov et al. (ICML 2018), [calibrated regression](https://proceedings.mlr.press/v80/kuleshov18a.html); official full PDF, sections 3.1-3.5 | Calibration and sharpness are separate. A Gaussian covariance is not evidence of coverage; their recalibration procedure needs separate or cross-fitted data and enough comparable observations. |
| Angelopoulos et al., [Learn then Test](https://arxiv.org/abs/2110.01052); targeted full PDF, sections 1.1 and 2 | Explicit risk control needs valid tests on independent calibration units and multiplicity control. This study does not inherit such guarantees from dependent drug pairs or exposed targets. |

## Evaluation and independent units

The registered retention criterion is reference mean terminal B utility above
the same-mean old KG comparator by more than 2%, with positive differences in at
least two of three outer folds, plus exact source-isolation and budget checks.
This is a development retention threshold, not a significance test. Report
absolute paired differences, all fold results and the baseline denominator
alongside percentages because the RNA endpoint is signed. The combined
drug-gain-plus-joint arm versus old M2 is a separate comparison: it changes both
the forecast and feedback model. Same-mean comparisons isolate feedback repair.

The intended evaluation uses 43 references with complete 146-candidate A/B
support. Every outer-held cell must be excluded from means, gain selection,
offsets, residual forecasts and covariance fitting. The gain grid and its MSE
selection remain unchanged. Only purchased A entries may reach the held-cell
policy; B is evaluator-only after commitment. Full-menu completeness is a
source-support restriction and must not be confused with complete physical
attempt coverage.

There are 43 reference contexts, not contexts multiplied by methods, doses,
gene coordinates or replay seeds. These references overlap STATE pretraining;
the five other target profiles have already been exposed. Cross-fitting can
test the new readout/posterior on held-out contexts while keeping fixed STATE
predictions, but cannot establish independent pretrained-model generalization.
A/B wells and plate labels do not authenticate independently initiated cultures.
The measured endpoint is signed RNA change, not apoptosis or viability. No
agent-versus-deterministic advantage is tested.

## Small public metadata audit for the next experiment

On 2026-10-09 the [official Tahoe dataset API](https://huggingface.co/api/datasets/tahoebio/Tahoe-100M)
and [metadata tree](https://huggingface.co/api/datasets/tahoebio/Tahoe-100M/tree/main/metadata?limit=100)
returned HTTP 200, revision `2dc57900b7981cfcf5e211527169a0b006546a95`.
Only README/API responses and the following metadata were retrieved; the three
Parquet files were parsed in memory, with no expression or new outcome arrays.

| Verified metadata at that revision | Bytes | Coverage |
| --- | ---: | --- |
| [Cell-line annotations](https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/2dc57900b7981cfcf5e211527169a0b006546a95/metadata/cell_line_metadata.parquet) | 19,040 | 1,000 annotation rows; 102 unique cell names/Cellosaurus IDs |
| [Drug annotations](https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/2dc57900b7981cfcf5e211527169a0b006546a95/metadata/drug_metadata.parquet) | 40,475 | 379 distinct drug strings |
| [Sample/condition annotations](https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/2dc57900b7981cfcf5e211527169a0b006546a95/metadata/sample_metadata.parquet) | 65,636 | 1,344 unique samples; 1,138 exact condition labels; 380 drug strings including control; 14 plates; 0/0.05/0.5/5 uM labels |

SHA256 values in table order are
`67641f5bdd3fb077978ff1fec4d0d617490674bcd42850515ae3997194c29d4d`,
`7a04c7a6611e74c92253163b994ff0a47191928ee7511f1c2ca508cee0e79f28`,
and `33167f0ce28cff8357c503cda67d1c7fea200bff6918ee1de3c4f3549175b9d3`.
Total metadata payload was 125,151 bytes. The dataset card advertises
337,644,770,670 download bytes for expression data; those assets were not fetched.

The [primary Cell article](https://doi.org/10.1016/j.cell.2026.08.035)
was verified through Crossref and the Europe PMC abstract: it describes 50
profiled cancer lines and about 1,100 drug-dose conditions. Therefore the 102
cell annotation IDs do not establish 102 available response contexts. The
abstract describes proliferation and cytotoxicity phenotypes, but the inspected
Hugging Face metadata does not authenticate a separate independent functional
assay, its attempted units, or linkage to the present RNA endpoint. Final article
full text was not obtained in this audit; preprint retrieval returned HTTP 429.

A cheap next question is whether metadata-selected compound conditions outside
the current 146-label replay retain the A-to-B transfer on authenticated source
units. Before opening their outcomes, establish actual sample/well support,
checkpoint exposure and local exposure, assay identity, control dependence,
attempt/QC coverage, timing and a justified utility. Existing STATE uses exact
drug-dose categories: annotation coverage does not add support for new chemistry
or continuous doses. Such a test can become a separately frozen development
experiment; it becomes independent confirmation only after the relevant
checkpoint and biological/source independence have been validated.
