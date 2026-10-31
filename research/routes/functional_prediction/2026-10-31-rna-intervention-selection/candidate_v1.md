# I001.v1: a restricted cross-cell splicing-response test

Status: proposed, not admitted, not fitted. Parent: attachment route2, reframed after processed-source and closest-prior checks. No RiNALMo/MAMMAL representation or new algorithm claim is proposed.

## Question and practical setting

Can an already measured RBP-knockdown response in one cell line predict the same knockdown's exon response in the other cell line when that target-cell intervention has no response labels for fitting or selection? The proposed usable output is a ranked set of exon responses for follow-up RNA experiments. This is known-intervention cross-cell prediction, not a new-drug task or demonstrated assay savings. A bulk RNA-seq experiment observes many exons together; exon holdouts are not independently purchasable assays.

The mechanism hypothesis is that transferring a fixed change in splice-inclusion odds accommodates target baseline state better than transferring the raw inclusion difference. This is an ordinary response-scale hypothesis. It becomes a useful predictive component only if it beats equally informed direct/nonlinear regression. It cannot by itself establish biological gating, causal RNA editing, a new Virtual Cell algorithm or novelty.

## Conditional data and selection, before effects

Use original uncorrected hg19/GENCODE19 rMATS junction-count skipped-exon outputs from the authenticated ENCODE publication file set ENCSR413YAF. Exclude normalized/batch-corrected outputs, significance-filtered tables and treatment-informed novel event selection. Candidate panel, chosen for known splicing biology and metadata availability without effects: HNRNPC, HNRNPK and RBFOX2, each HepG2/K562. HNRNPC is training intervention, HNRNPK validation, RBFOX2 decisive test, in lexical target order. Both cell directions form one matrix. No alternate target is substituted after outcome access.

The six selected source archives and their upstream BAM/control mappings must be authenticated; headers, event coordinates, replicate slots and baseline counts must support the contract before execution. All six target/cell pairs advertise eCLIP availability, but eCLIP values are not acquired or modeled here. This test does not test binding-to-function gains or RiNALMo's incremental value.

Group every event of the same Ensembl gene, RBP and cell in a shared deterministic gene fold. Require the event in both cells with identical GeneID/chromosome/strand/SE coordinates. Control-only coverage and reference annotation determine eligibility, never treatment significance or delta. Use only genes with unique event-to-gene identity. Leave genes out of fitting/selection too; source-cell responses of test genes are explicitly permitted prediction inputs, so these genes are not globally response-unseen.

## Measurement and information contract

Confirm that sample1 is KD and sample2 control, the effect sign is KD minus control, and there are two distinct control and KD biological input files per archive. rMATS replicate-slot order may be arbitrary; do not equate a slot to a biological replicate number without a crosswalk.

Primary target baseline feature uses control PSI slot0; target label uses mean KD PSI minus control PSI slot1. Source response uses mean source KD PSI and source control slot1. This avoids directly reusing the target baseline feature inside its label. It does not ensure independent batch/normalization errors or establish baseline causality. All models receive the same source response and baseline inputs. Baseline-slot reversal is a prespecified frozen-model sensitivity, not a refit or extra candidate search. If distinct replicate/control identity cannot be authenticated, stop this interpretation/test rather than silently average away the problem.

## Minimal candidate, rivals and decision

Clip PSI only for the logit transform at fixed epsilon0.01. Source log-odds change is logit(mean source KD PSI)-logit(source control PSI slot1). Candidate predicts sigmoid(logit(target baseline PSI slot0)+a*source log-odds change)-target baseline PSI slot0. Select a from0,0.25,0.5,0.75,1,1.5,2 using validation target/intervention genes only.

Ordinary rivals include zero response, raw source delta, fitted linear response rescaling, Ridge, polynomial Ridge and gradient boosting under identical legal information/folds/selection. All learned models have at least the candidate's legal source log-odds feature, source delta/baseline and target baseline. Gene identities are grouping keys, not prediction features. KATMAP already provides functional-splicing and cross-cell prior art; its motif-attribution task is not reproduced by this response-transfer test. No claim to beating KATMAP is allowed without an actual comparable run.

The main endpoint is held-RBFOX2/held-gene mean squared deltaPSI error, aggregated with equal gene weights, separately by direction. Secondary functional selection uses fixed |deltaPSI|>=0.1 and sign-correct Top100, with the actual selected event/gene and intervention counts reported. Do not use a five-hit exceptional-gain gate near a realized ceiling. A predictive continuation requires at least5% MSE reduction over every ordinary rival in both directions plus positive gene-cluster paired uncertainty support. This is descriptive evidence from the inspected experiments, not an external validation or independent biological replication interval. An inconclusive small panel cannot falsify splicing transport generally. Failure stops this candidate; success still does not meet an algorithm-novelty gate.

Before any numeric access/fitting, freeze exact source hashes, eligibility thresholds/folds, full estimator grids, ranking/ties, sensitivity and execution code after independent scientific and synthetic/caller-flow review. No scientific alteration after values. At most one matrix/1800seconds/four threads, with one implementation-failure reserve as defined in record.md. Missing measurement/independent-unit support permits ending with a documented admission failure, without fabricating a numerical negative.

## Alternatives and falsification

Ordinary conditional prediction may already capture every useful response-scale effect. Correlated control error, support bounds, transcript-coverage differences or knockdown efficiency may explain apparent transport. Existing binding models and KATMAP make a new functional-splicing capability claim inappropriate without direct comparison. The smallest decisive test is the fixed ordinary-versus-odds transport matrix under a distinct-baseline construction. No molecular mechanism, drug efficacy or Agent advantage follows from it.
