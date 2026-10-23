# CXCL9: real feedback helps ordinary calibration; no transferable new core

2026-10-23. Full objective ACTIVE / NOT_ACHIEVED. Previous turn PROGRESS; this turn PROGRESS: first commit-pinned author-source inspection, four raw real-assay downloads, schema repair, three independent sealed reviews with actual reciprocal objections, frozen raw-data passage-transfer experiment and saved-result audit. The experiment is a new development diagnostic, not a discovery or RSI validation.

## What was actually tested

Application: prioritize drug/cytokine conditions by 24-hour CXCL9 assay fluorescence in AsPC1 and BxPC3. CXCL9 is a legitimate proximal secretion-related functional assay; this is not a measured immune recruitment, cancer killing or clinical treatment endpoint. Author primary: Wang et al.2026, DOI 10.1038/s44320-026-00221-w. Repository commit b654a45faf5a80cdb1b514188cc90af8c9565b85.

Four initial-screen CSVs contain 203,732 FACS-event rows. These are capture-bead measurements, not that many cells, cultures or tasks. Metadata assigns E3CA/DA to P12 and E3CB/DB to P14. Each screen has 24 cytokine/inhibitor conditions × two Condition labels. Passage-related assay/batch effects and biology are not separately identified; replicate independence remains unresolved. There are only two cell-line backgrounds, with different cytokine doses.

For each cell line, source P12 supplies all 24 condition means from two samples. Target P14 reveals four no-inhibitor cytokine controls and five drug conditions under IFNG_TNFA (9 conditions ×2=18 measured wells). Predict the other 15 drug/stimulus conditions from their two held-out assay samples. This is familiar-drug passage transfer, not unseen-drug prediction. AL1/AL2 files, prepared MIDAS outcomes, saved fitted parameters and synthetic labels were not downloaded.

Primary output is within-well IQR-cleaned log10(MFI) minus matched sample blank log10(MFI). It is a fluorescence log-ratio, not calibrated CXCL9 concentration, secretion fold change or death-corrected activity. No whole-screen extrema enter the transform. Untrimmed results were prespecified. Filtering differs from the author's pooled filtering, so this is not a faithful author reproduction. All methods get the same allowed controls; controls are counted rather than treated as free. Vehicle pairing is supported by the paper's 1% DMSO statement, not independently proven by raw labels.

## New numerical evidence

Eight frozen ordinary direct/calibration predictors were evaluated. Hyperparameters and adaptive-method choice used only P12 duplicate-direction pseudo-tasks. Target test labels were masked as NaN in all prediction function inputs. The protocol, code and raw inputs were hashed before one experiment run; results were not used to change preprocessing, feedback selection, tuning or candidate list.

Primary MSE over 15 held-out condition means:

| Ordinary method | BxPC3 | AsPC1 |
|---|---:|---:|
| Source response table | 0.05727717 | 0.02668117 |
| Affine fit to four target controls | 0.03583813 | 0.01192123 |
| Control-anchored source drug effects | 0.04559537 | 0.01671126 |
| Nine-feedback global affine (source-selected in both) | 0.06453188 | 0.01710335 |
| Per-drug constant residual shift | 0.10094960 | 0.05125277 |
| Per-drug ridge effect slope | 0.03580812 | 0.01582215 |
| Hamming residual kernel | 0.04524608 | 0.01673876 |
| Fixed half residual shift | 0.04935556 | 0.02604730 |

**Supported development observation:** four-control ordinary affine correction reduces source-copy MSE by 37.43% and 55.32%. The direction remains under no trimming, with smaller gains of 19.13% and 15.58%. This supports local calibration value. The comparison does not identify whether correction reflects an instrument/batch effect or cell biology, and does not establish new biology, a learning algorithm or world-model necessity.

**Failed frozen progression:** source-selected adaptive nine-feedback methods fail to improve the control-anchored reference in either primary cell. In untrimmed sensitivity, BxPC3 still fails and AsPC1 selects a different adaptive method. Selected nine-feedback methods also lose to the simpler four-control affine method in all four cell/processing comparisons. The extra five measurements are not intrinsically useless: this exact selection/update design did not use them reliably. Strong shrinkage and fixed mixtures show localized gains, but no post-hoc winner becomes a new inherited rule.

## Decisions are a separate outcome

Menus contain five drugs plus no inhibitor in each of None/IFNG/TNFA. These are three correlated menus per cell, not independent trials. Regret measures missed log-fluorescence, not health utility. All models may use the measured no-inhibitor option.

In the primary analysis, the fixed half-shift has zero menu regret in BxPC3 and per-drug shift has zero regret in AsPC1, despite poorer MSE. These are frozen diagnostic outcomes, not source-selected successes. Under no trimming their mean regrets become about 0.08763 and 0.28903, respectively. They do not support robust action ranking. Source-selected primary affine does not improve BxPC3 regret and worsens AsPC1 versus four-control affine (0.01226 versus 0.00843). No stable drug-decision benefit passes the prespecified two-context/sensitivity gate.

The target duplicate squared discrepancies are 0.02699/0.04013 in primary BxPC3/AsPC1, rising to 0.05334/0.11950 without trimming. These describe variation between two assays; they are neither independent error-bar estimates for a population nor permission to subtract noise from scores. No bead-level significance test was used.

## Candidate and cross-review consequences

Three independent reviewers sealed initial opinions before reading their peers, then actually exchanged challenges. A constructive candidate projected residuals outside action/assay nuisance directions before selecting a single edge correction. Its exact linear witness improves scalar-only SSE from 1/2 to 0, but the same-information direct interaction and ordinary union least-squares refit also attain exactly 0. This is an operation-level conventional counterpart, not rejection merely for using conventional mathematics.

The witness is limited to its stated linearization. Finite nonlinear graph restrictions could still help; compare them with same-edge, same-forward-model bounded nonlinear coordinate refitting/search at equal full enumeration cost. A static endpoint graph is separately needed to test whether dynamics add value. One 24-hour scalar output does not establish dynamics.

Biology's strongest objection was accepted: four nuisance/control degrees plus five drug shifts can span the nine observed feedback values. With full row rank the nuisance-orthogonal residual is exactly zero. One feedback per drug cannot distinguish action repair from a context-dependent edge error. This design can compare prior-fixed predictive rules, not attribute a defect to an edge. Do not weaken direct baselines to manufacture attribution, or inspect these 15 test labels and then choose an edge to repair.

**NO_NEW_CORE_GO / STOP_FIXED_9_TO_15_PROMOTION.** The first pilot is complete and its gate did not pass. Do not rerun it with tuned preprocessing or feedback menus to rescue the claim. Preserve its local ordinary-calibration positives. This is not a blanket rejection of this dataset, nonlinear restricted action calibration, virtual-cell models or RSI.

## Source-code provenance changes the next action

Author preparation first pools conditions across screens for IQR cleaning, then applies per-sample full-screen log-MFI range normalization. Masking those prepared values cannot by itself simulate sparse measurements. The raw files permit the distinct local transform above.

The pinned AL script literally reads a table named synthetic_data and appends synthetic_mean in the update loop, without a separate experimental branch. Comments mentioning experimental data do not establish that running this script replays real feedback. This does not dispute the paper's independently reported wet-lab AL1/AL2 rounds; their actual measurement mapping would require a separately frozen source audit. Current synthetic candidate counts and optimizer initial-state assignments are not extra biological tasks or state trajectories.

There is no approved new operation to evaluate on AL1/AL2, so those payloads remain unfetched. The next research action must supply a precise new predictive restriction and a lawful comparison capable of separating it from ordinary calibration. It must not merely add another agent layer or relabel source-repeat selection as inheritance. Full world-model, agent, inheritance, joint and improved-improver contributions remain unestablished; strong direct, retraining, CL, AL, mixture and equal-total-budget search remain obligations for any future candidate, not victories established by this pilot.

## Resources, verification and scope

Method independently reconstructed saved tuning, predictions and metrics: 336 comparison groups / 1,160 numerical components, maximum absolute discrepancy 6.66134e-15, all 13 pre-run hashes unchanged. Constructive separately rebuilt raw aggregation using csv, its own linear quantiles and math.fsum/log10: 384 response values agree within 4.44089e-16, all 384 raw/retained-count pairs and schema checks agree. Neither imported/reran the root predictor; raw aggregation audit is additional computation on the same measurements, not independent biological replication. Biology sealed its result interpretation before reading method's result, then they actually exchanged and recorded challenges. They agree on retaining ordinary positives and the bounded STOP; no resolved arithmetic disagreement remains, while portability, biological attribution and future new-core mechanism remain unestablished.

Root made 15 successful HTTP retrievals: repository/commit/tree (3), source/metadata (8), real raw files (4). Reviewers report zero additional GETs/API calls. No DeepSeek request was needed this turn; previous API failure is not re-proposed. Native agent model identities/token/currency are not attested. One CPU experiment script ran for 1.6089232 seconds (internal timer), producing two prespecified processing variants. Source hyperparameter fitting and independent arithmetic audits are additional computation, not new tasks. No GPU, new wet experiment or author-model performance reproduction occurred.

All research code and tests are under research/cxcl9_source_feasibility_20261023/; all data/evidence under log/20261023/cxcl9_source_feasibility/. Historical stopped branches and protected endpoints remain closed. Local source/prediction/review hashes do not repair the unresolved historical global provenance drift. Independent numerical audit and final local continuity/manifest details are recorded in their own artifacts; no full-goal completion is asserted.
