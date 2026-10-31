# A: retrospective functional-teacher countertest

Version1, 2026-10-30, before this round's model execution. **Already exposed development labels; not a pre-label or independent-confirmation experiment.** Requires independent initial review before implementation/execution. Overall goal ACTIVE / NOT_ACHIEVED.

## Question, changed premise and limits

Does a source-only functional response teacher improve rare sensitizer prioritization beyond direct predictors with identical chemical/pharmacological inputs? Does independent prior pharmacology help compared with chemistry alone? The second question is descriptive unless separately supported; a distillation gain cannot be attributed to new information without the equal-input direct comparison.

The parent Morgan-only diagnostic remains parked. New information is the existing Broad Drug Repurposing Hub 2020-03-24 target/MOA metadata, matched using isomeric canonical parent structures without query name/CID/fuzzy matching. Its metadata freeze finds54 annotated development compounds (fold19/24/11) and177 unmatched; all231 remain in the primary denominator. This is independent historical annotation, not new experimental function, target engagement or a causal explanation. Source classes inferred from CGI results, CRANKS2 and query response panels are excluded. No63-compound held-out calls, S2 numeric values or historical protected outcomes are opened.

The donor principle is supervised transport into a frozen meaningful coordinate system. Here a simple linear teacher provides a cheap countertest. This is ordinary response-space projection, algebraically related to reduced-rank regression; no new algorithm or faithful reproduction of Omni is claimed. A measured function matrix is not a dense-caption embedding teacher, and this comparison does not establish a general multimodal learner.

## Fixed observations and target

Use the corrected parent `labels.npz`, preserving231 compounds,18,415 canonical genes, three scaffold folds70/97/64,181 scaffold groups and screening-round identities. The label is a native published negative CRANKS/FDR<.05 sensitizer call, not physical effect size. Non-calls are not validated negatives. Use only representative development screens, the parent's pre-label 7p/21q/identity mask and source-only rarity (at least one training call, no more than10% source prevalence). Retain every query, including zero-call queries. Exact count ties precede canonical lexical ties.

Inputs are frozen Morgan radius2/1024-bit/chirality fingerprints plus214 prior-pharmacology columns:213 target/MOA indicators and an annotation-available flag. Query annotations are allowed information; their availability does not depend on this CGI experiment. Alias annotation conflicts are missing. No feature or source selection is based on replay performance. Each training fold computes feature means/population SD; zero SD becomes1. Standardize the chemical and pharmacology columns identically, including concatenation. Both feature sets are available to all equal-input rivals.

## Fixed panel and functional teacher

1. Historical gene-call frequency, calculated by exact integer counts divided once.
2. Chemical-only full-rank Ridge, alpha100, with intercept (legacy control, not a reopened candidate).
3. Pharmacology-only full-rank Ridge, alpha100, with intercept.
4. Concatenated-input full-rank Ridge with intercept, alpha1.
5. The same, alpha10.
6. The same, alpha100.
7. Concatenated-input RBF kernel Ridge with intercept, alpha1. Gamma is1 divided by the count of source-varying standardized columns (fallback1). Center the train/query kernel with source means and center outputs on their source mean. This is an ordinary nonlinear equal-input rival.
8. Candidate: concatenated-input Ridge alpha100 distilled into a rank32 source-response teacher, retaining the source response mean. The rank is fixed, not selected by replay scores. Use fewer directions only if the centered response rank is less than32; declare the numerical eigenvalue tolerance before execution.

For source call matrixY, H=I−11'/n and centered responsesYc=HY. LetVr be its top right singular directions. The frozen teacher target isYcVr and its decoder iszVr'+mean(Y). Fit a Ridge student from source standardized concatenated inputs to those teacher coordinates, using alpha100 and an intercept. This predicts mean(Y)+(direct_Ridge_prediction−mean(Y))VrVr'. It is exactly a projected ordinary predictor under the same penalty, not a separate source of functional information. The equivalent source-row formulation may use the top left eigenvectors ofYcYc' to avoid a large gene covariance. Define positive modes as eigenvalues greater than1e-10 times max(1,largest eigenvalue), sorted descending; source compounds are lexical. No query response builds the teacher, mean, rank, modes or student.

Predict all eight profiles on the same queries/candidate genes, clip predictions to[0,1] after reconstruction, and take Top20 with canonical lexical ties. Preserve unclipped or operator identities sufficient for the stated bounded check; do not claim saved Top20 arrays certify full unsaved predictions. No LightGBM installation or new neural/vision/text backbone is used.

## Primary contrast, null and uncertainty

Primary endpoint: macro rare native-call P@20 over all231 compounds. The direct comparator is the maximum full-CV P@20 over frequency and the four equal-input direct settings (joint Ridge1/10/100 and RBF1). Ties follow that listed order. The candidate is fixed; do not switch among teachers/ranks. Primary gain is candidate minus this strongest direct comparator. Also retain chemical-only, knowledge-only, oracle/recall, per-compound counts and the metadata-frozen annotated subset descriptively; no favorable subset becomes primary.

Use the parent's49 frozen coherent whole-scaffold profile assignments (seed20261030), within ordered-round/size strata. Reassign source AND validation truth consistently. In every draw, rebuild source eligibility, frequency, source-response teacher and all profile predictions. Select the identical best direct comparator in every draw; compare exact recovered-call differences, including ties, with `(1+count(null_gain>=observed_gain))/50`. Null assumptions/mobility and conditional limits carry over; neither prior exposure nor a p-value makes this confirmatory.

Bootstrap the selected aligned candidate-minus-direct recovered-call differences by complete scaffold group,2,000 draws, seed20261031, lexical group order; use integer group differences before division by20 times sampled compound count. Report the95% percentile interval as conditional exploratory uncertainty, not independent-culture or population coverage. Shared source controls and the source's label-construction limits remain.

Continue only if gain>0 and conditional p<=.05; report the interval separately. Even passing establishes neither exceptional practical benefit nor biological sensitization. A physical-effect/noise/cost threshold is unavailable from these binary published calls, so `robust_benefit_established`, `held_out_release`, Agent integration and core promotion remain false regardless. A useful ordinary pharmacology predictor can be retained as an exploratory component without calling the projected teacher novel or indispensable.

## Old-path retention, implementation and budget

The archived chemical-only path may remain separate and frozen. Its exact invariance is a deployment/engineering property, not a scientific non-forgetting gain. This experiment does not update a previously validated shared core; no claim of general old-task retention follows. Record model compute separately from real assay cost; a32-dimensional teacher does not mean measuring fewer genes.

Pin scripts, metadata/features, label/identity arrays, null assignments, this protocol and reviewer amendments before launch. Precompute feature-to-source linear/kernel operators without outcomes; source teachers still use source-fold calls only. Independently check the projected-Ridge identity and count ties on a small synthetic fixture before any real model matrix. One A matrix, four threads,1800-second hard launcher; save partials/failure and disallow silent replays. The sole global failure rerun is for demonstrated implementation failure only. Freeze independent saved-rank arithmetic checking before root outcomes, then independently interpret before synthesis. Preserve all results, including a valid negative.
