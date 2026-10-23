# Independent simplicity and necessity assessment

Scope: source-only review of root_sources and the latest norman_feedback_transport/DECISION.md. No other current reports, datasets, protected outcomes, HTTP, or fits were accessed. This report was written before reading another review. Full objective remains ACTIVE / NOT_ACHIEVED.

## Decision

GO_BOUNDED_AUTHOR_BASELINE_QUALIFICATION; NO_NEW_WM_MECHANISM_GO. NAIAD is an essential strong ordinary comparator before claiming that a new state/world-model mechanism is necessary in this setting. It explicitly combines measured single-gene functional effects, trainable gene embeddings, a permutation-invariant summed embedding interaction predictor, and capacity chosen from training sample availability. This directly occupies the ordinary adaptive-representation explanation. It is not proof it beats the existing RNA/nuclear baseline, and it need not be the sole comparator.

The preceding STOP remains binding: the early-mixture restricted updater lost to ordinary union refitting. NAIAD inspection supplies no reason to revive that configuration. A positive NAIAD result would be useful ordinary prediction, not evidence of world models, agents, inheritance, RSI, drug response, or the full objective.

## Exact endpoint contract before fitting

Paper section 3.1 permits a scalar phenotype, but Appendix A.1 is specific: bulk viability log-fold change relative to negative-control treatments, averaged over guide pairs for a gene pair. Singles are gene-targeting/non-targeting guide pairs on the same outcome scale. Norman here is 112 genes / 6,328 combinations in the paper; its shared name does not establish identity with a transcriptomic Norman task.

An admissible comparator must receive precisely the currently authorized functional target, direction, units, time window, normalization, gene mapping, canonical pair universe, and authorized single-gene functional values. Do not replace functional outcomes with RNA changes, use an interaction residual as if it were viability, infer a missing single from held-out pair truth, or pool mismatched controls. Existing DECISION does not specify this entire contract: source-only review cannot certify exact compatibility.

Author data contract is id1,id2,comb_score,id1_score,id2_score (models.py lines 9-40); utils.py reorganize_single_treatment_effects removes singles, merges their scores, and drops missing scores. Therefore explicitly audit missing singles and exact retained universe: silent dropping changes the comparison. The all-negative row has a role in author preprocessing; do not invent a zero control if the existing target has a different origin. A prepared-table adapter can bypass irrelevant raw-guide conversion, provided these semantics are demonstrated.

## Minimal faithful implementation

Use pinned author EmbedPhenoModel with model_type=both and embed_model=mlp, the author training loop and optimizer, plus a small adapter for the already frozen split and prepared scalar table. Preserve author parameter initialization, phenotype shuffling, dropout, branch architecture, and evaluation mode. Do not rewrite as a custom matrix factorizer/kernel and call it NAIAD. RNA conditioning would be an extra method, not the direct author baseline.

Author naiad.py lines 214-219 computes n_train / len(treatments), then chooses the last schedule key strictly below that value. Schedule: 0->2,2->2,4->4,10->16,20->16,30->32,40->64,60->64,80->128,100->128. Do not silently substitute twice pair count / genes or change strict boundary behavior. Paper Table 9 Norman uses 500 epochs and single-gene hidden dimension 64; package fallback is 256. Pin one reproducible author-faithful primary configuration and disclose this paper/package difference instead of choosing whichever scores better. Capacity depends only on training count, never development outcomes. No new learning-controller layer is required.

Author treatment summation is permutation invariant, but phenotype branch uses the two inputs with preprocessing shuffling. Do not claim mathematical exact symmetry of the entire implementation; inspect orientation effects on synthetic inputs and report the chosen faithful preprocessing.

## Bounded fit / success / stop contract

Before any numerical data access, freeze the endpoint/control contract, artifact hashes, exact authorized split IDs, target transform/inverse, full single/RNA information ledger, training-only schedule, seed set, settings, epoch policy, metrics, and comparator prediction artifacts. Do not let the package create a random replacement split.

A sufficient modest execution budget is three declared seeds at the one primary later512 union training size, 500 epochs per fit, no hyperparameter sweep, no active acquisition rounds, and no protected evaluation. If a different epoch policy is essential for the existing budget, label the run an explicitly bounded author-code adaptation rather than a literal paper reproduction. Count all fits, failed attempts, time, supplied singles, RNA cells/prior acquisition, and dependencies.

Entry gate: endpoint identity, controls, single-value provenance, pair coverage, and split exclusion pass; author module imports and synthetic forward/backward shape/finite checks pass. Stop before fitting when any fails. Author dependencies or missing outcome semantics are qualification blockers, not invitations to invent data.

Implementation success: unchanged author computation executes on frozen authorized training data, all three seeds produce finite predictions for the identical evaluation universe, and independent saved-prediction arithmetic reproduces reported MSE. Report seed distribution and the identical conventional union RNA/nuclear comparators, regardless of ranking. Exposed development remains exploratory. Ordinary baseline qualification does not require winning, and losing three seeds does not authorize a tuning campaign.

Scientific next-step gate: a future state mechanism needs a prespecified advantage over the strongest direct ordinary comparator with the same available information and counted acquisition/search costs. Predictive improvement alone cannot establish necessity, useful experiment choices, or transfer. If no robust advantage or distinct diagnostic remains, STOP the proposed mechanism claim. No protected data reopening or budget expansion to reverse an unfavorable result.

## New scientific-error candidate

NO_CANDIDATE. Source-only evidence supports endpoint/control checks and ordinary adaptive-capacity confounding, not a genuinely different empirically supported scientific failure mechanism. The tutorial's general claim of nonlinear residuals and the paper's acknowledged unseen-gene limitation do not establish reliable structured residuals in the present target. Measurement uncertainty, context dependence, state-mediated causation, and benefit of acquisition remain hypotheses without the required present-task evidence. Do not manufacture novelty from them.

Sources: paper.text sections 3.1,3.2,A.1,F.1 and Table 9; naiad__models.py.body EmbedPhenoDataset/EmbedPhenoModel; naiad__naiad.py.body n_treatment_seen/initialize_model; naiad__utils.py.body load_naiad_data/reorganize_single_treatment_effects; tutorials__data_preparation_tutorial.ipynb.source.txt; README.md.body; preceding DECISION.md. File hashes in seal bind this review to the inspected local copies rather than asserting an unverified repository commit.
