# Independent static DGP-LA operation review

Read the pinned model.py, prior.py, reproducibility guide and repository tree saved in root_sources. No external code imported/executed, network, fitting, data arrays or author performance reproduction. A new local byte-only checker verifies all3raw-source SHA256 receipts, Git blob SHA1s and sizes against the nontruncated tree at revision **2e87ceee1e73eb81d2c9b4481af454e26faea014**. All3pass; DGP_SOURCE_CHECK.json records exact hashes. The first combined full-source console output truncated; the decisive forward/objective/optimizer and prior sections were subsequently read in bounded ranges. No claim relies on unseen truncated code.

## What directly determines the graph and gate

In `_targets` (model.py397onward), condition names are parsed for a **single drug**, mapped through the fixed DTI lookup to retained gene indices, and encoded as a binary target vector. Drug dose is not used in this vector. Multi-drug labels are rejected by `_parse_drug_name`, rather than composed into a target union in this implementation.

`SparseSoftResidualGraphRefiner._one` (162–175) applies a learned target→rank sigmoid modulation to U,V factors, normalizes their gene-pair score, subtracts a fixed quantile threshold on absolute scores, soft-thresholds with ReLU, applies signed tanh and adds/clamps the residual to a static adjacency. A zero target vector returns the static graph and zero residual. Static PPI construction in prior.py retains STRING edges>=700, max-collapses duplicate undirected edges, scales scores/1000 and adds self loops; DTI tables are merged/deduplicated and projected to the gene order.

`TopologyAwarePriorAdapter.forward` (215–241) propagates initialized target features through normalized refined adjacency, produces a node “support” readout, pools mean/max node states, and generates a latent correction. A sigmoid gate depends on that pooled prior latent and mean absolute node support. Zero-target active mask zeros support/correction/gate.

Therefore **for fixed trained weights/prior, the refined graph, graph “support”, correction and gate are determined by the target vector alone**. They do not directly ingest current-cell control RNA, functional support feedback, residuals, acquired experiments, source-task history or new-context measurements. Identical retained target vectors give identical prior-branch outputs, including across different doses or contexts. This is a concrete forward-dependency conclusion, not a statement that learned parameters never saw source data: ordinary supervised training changes those global parameters.

Do not translate the source term “support” into few-shot functional support. Here it is a graph-node response/readout, not measured y_S or a support-query update procedure. Nor does the code certify target engagement: the vector is a static annotation projection. Unknown or out-of-gene-universe targets disable this prior correction but do not disable the chemical/backbone branch.

## Context dependence remains in the full model

Forward (438–480) separately encodes control-cell expression, fingerprint and dose. A fingerprint-dependent dose scaler multiplies drug latent features; the transition Transformer acts on `cell_state + perturbation_latent`. The fixed-for-target gated correction is broadcast into hidden state, and the response decoder receives `adapted_hidden + cell_state`.

Consequently the **final expression prediction and actual expression difference caused by a latent correction can vary with control context, chemistry and dose**, through the nonlinear transition/decoder interaction. A target-only gate does not imply a context-independent final effect. It would be incorrect to say the model discards control state or is just target lookup. Conversely the context-dependent final prediction does not make the graph/gate itself function-feedback conditioned. This precise distinction is the direct-neighbor implication.

`base_prediction` and fused `prediction` are both returned, but the objective as read uses fused prediction; no paired base-versus-updated functional utility target or source-feedback benefit gate appears. This is not a claim that the returned base prediction could not be used in a separate analysis; such an analysis is not implemented here.

## Objective and training are not RSI

The objective (482–514) is empirical expression-set energy distance plus1-minus-cosine alignment of predicted/observed mean deltas relative to controls plus mean absolute graph residual on active target conditions. The shown terms enter with unit coefficients. AdamW has backbone and graph/prior parameter groups with separately configured learning rates; ordinary training_step optimizes the fixed objective end to end. The reproduction guide explicitly describes that training flow and fixed unseen-context/drug split preparation.

This is learned target-conditioned graph residual representation and gated latent adaptation under a fixed supervised procedure. It is not, in the inspected files, autonomous research-program revision, acquired functional-feedback updater inheritance or improvement-strategy recursion. New functional validation, agent selection and common-parent G1/G0 descendant tests cannot be inferred from graph weights adapting during training. That boundary does not deny practical value or algorithmic novelty of the author's own method.

## Appropriate use as a close control

The source is a concrete recent near neighbor for “static PPI+target-driven dynamic graph+gated latent correction+control-conditioned perturbation prediction.” A proposal using the same ingredients needs a substantive different operation or demonstrable biological/finite-resource property; merely naming a cell agent or inherited graph is insufficient. A future functional-feedback-conditioned restriction can differ from the target-only gate, but must face equally informed conditional direct/EB/meta/refit comparators. The existence of this code does not prove every feedback-conditioned graph model equivalent to it or to ordinary ridge.

External PPI/DTI knowledge, control state, fingerprints, doses and source representation-training costs must be matched. Honest comparisons should state which implementations are faithful, altered, unavailable or costly rather than handing a baseline a free ideal posterior or denying its own metadata. No author accuracy/robustness numbers were reproduced here, and no model was trained.

## Root API rejection rechecked

The earlier rejection remains precise: old36×15query residual covariance is a derived statistic of already exposed development outcomes, not a new observation. A new white-ridge program or post hoc pair/bootstrap threshold would reopen a stopped menu; source-only fold fitting does not erase research-level selection. This is sufficient to reject that action. Do **not** reject it on the ground that all conditionalEB/AL/refit/mixture families are prohibited: they are allowed strong controls. Do not claim a fully specified exact equation equivalence where the API did not even define compatible support/query dimensions. No covariance, bootstrap or new fit was executed.

Constructive's later reverse question about pairedDelta has now also been answered explicitly: measured utility beating a construction prior remains an ordinary source-conditioned utility-learning positive absent a new law or finite-resource property. It does not alone establish updater innovation or RSI. The prior CROSS.md remains sealed; this response supplements it without modification.
