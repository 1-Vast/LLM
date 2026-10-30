# Protocol: evidence-driven revision of functional transfer rules (O'Neil 2016, internal development)

Written 2026-10-20 before the challenge batch was disclosed. Executes
[NEXT_RESEARCH_PROMPT](../../log/20261020/NEXT_RESEARCH_PROMPT.md). O'Neil is previously exposed data:
a hidden partition does not make it independent. The object tested is a conditional functional
prediction rule, not a molecular mechanism, cellular trajectory or pharmacological class.

**Question.** Given identical cumulative observations, does one bounded, evidence-driven revision of
conditional functional transfer rules improve the selection of entirely held-out drug pairs beyond
(i) fixed-structure refitting, (ii) a fixed sparse supermodel containing every allowed edit, and
(iii) conventional structure learning? Application: preclinical combination prioritisation inside a
known compound library (38 drugs, 39 cell lines). Link to the reviewed proposals: EvoPharm-WM supplies the
hypothesis that feedback should change *where* experience transfers; the critical review supplies the restricted
edit language, same-information comparisons and the requirement to improve decisions on unmeasured combinations.
The DBP/Potter task is separate and is not started.

## Data route and endpoint (decided from structure, not performance)

RAW ROUTE, on the three authenticated original workbooks. Primary batches 1 and 2 only
(22,737 pair-cell groups, 583 unordered pairs x 39 cells, each a complete 4x4 grid). Batch 3 (selected repeat) is excluded.
The old aggregate cache and its Bliss label are not used. Row locators are kept
(`groups.npz`: first row, the 16 combination rows and the 8 single-agent rows per drug).

* Activity **A = 1 - mean(X/X0)** over the 16 published grid points, equal weight, no clipping. Raw viability columns stay in the workbook; X/X0 is publisher-derived.
* Derived reference **A_ref = 1 - mean(Xa(ca) Xb(cb))** from same-batch log-concentration interpolation of the single-agent curves; never extrapolated, never borrowed from another batch. Only 23,595 of 363,792 rows match both doses, so most reference values are interpolated: a *derived reference*, not an observation and not a purchasable point.
* Residual **R = A - A_ref** is an *interpolated functional reference residual*, not validated Bliss synergy. Learners predict R; the nominated quantity is A_hat = A_ref + R_hat.
* Missing/invalid handling (fixed before looking at values): a group is eligible only if it has 16 distinct finite points, a same-batch single-agent curve per drug and all doses inside the curves' range. All 22,737 groups are eligible, so there is no exclusion and no substitution. Ties in a shortlist go to the smaller pair id.
* Technical repeats (4 combination / 6 single-agent columns) are not independent cultures; no plate, well, control, stock or bundle identifiers exist, so physical costs and culture independence are NOT qualified.

## Information boundary and partition

Disjoint canonical unordered pairs, 60/15/10/15 percent = 350 S / 87 C / 58 G / 88 F (identity only, seed 20261020, first
draw meeting the coverage rule: every drug in >= 9 S pairs; observed minimum 10). All cells, doses, orientations and repeats of a pair share a role.
Outcome files are written once, split by role (`outcomes_S/C/G/F.npy`, SHA-256 in PROVENANCE.json) and read only through
`adapter.OutcomeVault`: S at start; C only for the acquired panel after one disclosure; G through one retention query per arm after
disclosure; F once, by the final evaluator, after all retention decisions. The vault ledger is stored.
Common initial information for every method: the complete single-agent panel (16,752 rows), its cost recorded as common initial information, not incremental.
Feature scaling uses S features only; modules and gates use the single-agent panel only; nothing uses a combination outcome outside S/C.

## Fixed model, functional modules, gates

Fixed structure (ridge on R, intercept; blocks penalised by lambda_base or lambda_theta): cell effects, symmetric drug effects, module effects,
a within-module and a cross-module shared component, three numeric terms (A_ref, min and max drug monotherapy activity at the pair's grid), and
symmetric drug-by-cell terms. Modules: Ward clusters (k=4) of the 38 drugs on their 39-cell monotherapy-activity profile (single-agent panel only).
Observable gates (from the same panel): a cell satisfies the gate if its mean monotherapy activity (all drugs, or drugs of a module) is at least the
across-cell median; an unknown gate value is encoded -1 and is never treated as satisfied (feature 0).
Cross-pair propagation is never inferred from single-agent similarity alone: single-agent profiles only define modules and gates; the effect
sizes are learned from combination outcomes of S/C.

## Edit language and frozen dictionary (16 edits, metadata only)

* A. **Split** of a shared component by an observable condition: cross-module component x {global sensitivity, sensitivity to module m0..m3} (5) and within-module component x {own-module sensitivity} (1).
* B. **Add** one restricted interaction shared by all pairs of a module class: the 10 module-pair classes (4 within, 6 cross).
The dictionary was fixed from metadata before any S model was fitted; it was not screened on outcomes. A pair-specific coefficient is not an allowed edit. An eligible edit must have scope on >= 10 evidence pairs (>= 3 in the challenge panel) and on >= 2 unmeasured pairs.
Statement of claim: any advantage concerns finite-data learning, search efficiency or reduced negative transfer within a controlled function family; ordinary models can represent the same functions.

## Challenge, diagnosis, revision, retention

1. Fit the frozen initial model on S (source-tuned, 12 ridge configurations, 5-fold pair-grouped CV, 2 repeats).
2. **Challenge panel:** 60 pairs from C (equal allocation over the 10 module classes, hash order), each in all 39 cells = 2,340 groups, one acquisition batch. Chosen from design metadata and the single-agent panel only; counted in groups, not a verified physical cost.
3. Record the initial model's predictions for every panel group (hashed) before disclosure; disclose the panel; flag counterexamples |observed - predicted| > 2 source-side out-of-fold residual SDs.
4. All methods get exactly S + panel (same preprocessing, features, tuning folds and candidate pool).
5. Mandatory comparators: (1) frozen initial model (descriptive only); (2) fixed structure refitted on S+C, 12 configurations; (3) fixed sparse supermodel with all 16 edits, 12 configurations; (4) conventional structure learning: a gradient-boosted-tree model (12 configs) and a second-order factorisation machine over cell and drug fields (12 configs), champion chosen by S+C grouped validation (home-built approximations, not comboFM or BATCHIE); (5) bounded revision.
6. **Revision selector (deterministic, primary):** for each edit, relative grouped-CV MSE reduction on the challenge groups (S+C pooled folds, refit's configuration); eligible if the all-groups relative change >= -0.25% and the scope guards hold; the candidate is the eligible edit with the highest challenge gain, else NO_EDIT. The candidate is retuned over the same 12 configurations. One candidate per arm.
7. **Retention (one G query per arm after the candidate is fixed):** accept if the shortlist-utility gain over the refit on G >= tau (= margin/2), activity MSE ratio vs refit <= 1.02, for single-edit arms also the out-of-scope (prior applicability range) MSE ratio <= 1.02, and complexity limits hold. Otherwise the deployed procedure is the fixed-structure refit and no further edit is made. Raw candidates and deployed procedures are both reported. The same rule applies to the full-dictionary and conventional-champion candidates (their out-of-scope notion does not exist, so only the overall MSE check applies; stated asymmetry).
8. Predictions and nominations for G and F of every method are sealed (hashed) before any G read.

## Primary metric, margin, uncertainty

Per cell, nominate k=5 of the 88 held-out F pairs by predicted A; utility = macro-cell mean true A of the shortlist; regret = oracle - utility. Secondary: the same shortlists scored by R (reference-adjusted). Supporting diagnostics: activity MSE and negative transfer
(share of F groups with larger error than the refit, mean excess).
**Margin.** The brief's default 0.02 exceeds the source-side headroom: on S pseudo-pools of F's size the Bliss-reference ranking has regret of about 0.02 and the fitted fixed model about 0.017, so 0.02 would be unreachable. Rule fixed before C: margin = max(0.001, min(0.02, round(0.25 x S-estimated regret of the fixed model, 3))) (a research screening threshold, not a clinical effect size).
**Precision (S only):** repeated random 88-pair S pools (with finite-population correction) give the SD of paired utility differences; the design is labelled ESTIMATION_PILOT when the worst minimum detectable effect (2.8 SD) exceeds the margin. The label is stored in FREEZE.json.
**Uncertainty.** Resample whole F pairs with all cells (2,000 draws), reselecting shortlists inside each draw; percentile bounds at alpha/3 = 0.0167 one-sided (three primary contrasts, Bonferroni-conservative Holm); delete-one-drug jackknife (cluster-by-shared-constituent sensitivity) and a cell bootstrap. Intervals do not establish independent biological replication.
Primary contrasts (deployed procedures): revision - refit, revision - full dictionary, revision - conventional champion.
**Verdict (VERDICT_RULE in FREEZE.json).** PROMISING_INTERNAL_DEVELOPMENT only if the revision was retained at G and all three contrasts have estimate >= margin, pair-bootstrap lower bound > 0 and drug-jackknife lower bound > 0. UNSUPPORTED if the upper bound of (raw candidate - refit) is below the margin. Otherwise INCONCLUSIVE. A flag STANDARD_STRUCTURE_LEARNING_SUFFICIENT is raised if the full-dictionary or conventional procedure beats the refit with lower bound > 0 while the revision does not. Beating the initial model is information-update benefit only. A non-significant difference is not equivalence.

## Optional policy comparison

NOT_RUN. Acquisition bundles, controls and physical costs are not recoverable from the originals. Agent strategy gain (counterexample-directed selection vs coverage vs direct confirmation) therefore stays untested; the model experiment is complete without it.

## Bounded API arm (secondary, registered before C)

Included. One edit-selection request to `deepseek-flash` through the maintained client: sees opaque ids (drugs D##, cells L##, pairs P##, observations O###), the frozen numerical edit definitions
and the same legal evidence table the deterministic selector uses (per-edit grouped-CV gains, scope counts, flagged counterexamples; the 25 largest flagged groups with their residuals) and returns an allowed edit id or NO_EDIT plus cited observation ids. It never sees names, dataset identity, old reports or G/F information. Local compilation and validation; no generated code is executed. Limits: one logical scientific request (the optional synthetic contract check is not used), at most 4 HTTP attempts including client retries,
max_tokens 1,024, conservative input estimate <= 6,000 tokens (no provider token counter; characters/2.5), temperature 0. Prices are unverified, so no monetary figure is asserted. Invalid or failed answers fall back to the refit with no second search. The arm uses the same G rule and its F predictions are sealed before G. This is a bounded integration test, not evidence of LLM superiority, acquisition-policy gain or autonomous discovery. Opaque ids reduce but do not prove absence of pretrained knowledge.

## Disclosures (before C)

* The grids (lambda values, tree and FM settings) and the margin rule were adjusted using S-only development runs on 2026-10-20: lower-theta lambdas and wider tree/FM ranges were added when the best value sat on the old grid edge; the margin rule was introduced after S pools showed the 0.02 default exceeds the headroom. G, F and C outcomes were not read.
* During those runs the per-edit S cross-validation gains were seen (all within about +/-0.4% of fixed-model error). The dictionary itself was already fixed from metadata and was not changed.
* Software tests use synthetic fixtures only; they are not scientific evidence.

## Reproduction

    & 'D:/MAESTRO/.venv/Scripts/python.exe' -B research/functional_rule_revision_20261020/run.py qualify   # authenticated originals -> groups, partition, sealed role files
    & 'D:/MAESTRO/.venv/Scripts/python.exe' -B research/functional_rule_revision_20261020/run.py all       # freeze -> challenge (API) -> retention -> final
    & 'D:/MAESTRO/.venv/Scripts/python.exe' -B research/functional_rule_revision_20261020/verify.py        # read-only
