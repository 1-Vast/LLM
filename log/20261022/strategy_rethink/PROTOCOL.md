# Frozen-plan candidate: finite ordinary C4 opportunity screen

2026-10-22. Status initially DRAFT; execution is authorized only after `FREEZE.json` binds this file, the code, input hashes and exact ID-only episode manifest. All code/new tests are under `research/strategy_rethink_20261022/`; all evidence, failures and output are under this log directory. This is explicitly a **non-innovative conventional benchmark**, not a new core, functional-drug claim or complete RSI test. Historical STOPs remain in force; no TG later14/AZ413 access.

## Scope and dependence

Use only `research/knowledge_transfer_20261012/cache/dev_routes.npz` and its historical source code for provenance. Its phase1 regime-A export has31,647rows,7,760compound IDs and9line IDs; the old seven-line confirmation tier is different. Arrays contain five route types but this protocol uses exactly context, pheno, chem, know, as in historical pooling. No historic module is imported. No historical arrays/files are rewritten.

Archived route construction used an outer-fold reference atlas containing compounds in the other folds, and regime A permits the query's own other-line responses. Therefore the source/later split below is NOT molecularly isolated from precomputation. This is a **conditional exposed-background calibration/program-search experiment**. New top-layer calibration/development/evaluation IDs are disjoint, but their route vectors do not establish prospective unseen-compound prediction. All historical outcomes were exposed; new masking controls only this execution. No active-response eligibility or outcome norm is used for task admission.

## Frozen IDs and one partition

Source uses archived fold0; later uses fold1; fold2/3/4 response values are not used in fitting, feedback or scoring. NPZ access decodes the COMPLETE stored arrays into memory before slicing, including unused folds and terminal/source-evaluation rows: no claim of raw numerical non-contact or unopened outcomes is made. Execution isolation means only approved sliced values are passed to fitting/proposal/scoring, and target terminal slices are passed to scoring only after the deployment seal. Full-array contact is disclosed in the receipt. Within each fold, sort compound integer IDs by SHA256(`strategy-c4-split-v1:`+str(compound)). Take the first512 and divide consecutively into8episodes of64. Within each episode, first16 are calibration compounds, next16 are development-feedback compounds, final32 are terminal-evaluation compounds. All regime-A line rows of the selected compounds are included. The manifest contains every exact compound ID and row index, derived before scalar outcomes are read. Compound IDs cannot overlap between episodes or source/later. No random repartition or coverage-based rescue.

## Fixed solver and finite grammar

All route vectors are archived centered978-dimensional predictions, treated as fixed background. Normalize each route vector by its norm (zero stays zero). Ground truth is the archived centered vector, likewise normalized. For a route available in a calibration row, its training label is dot(unit-route,unit-truth), with exactly zero when either vector is zero. Fit four independent ordinary ridge accuracy regressions, one per route. Availability is from the archive, never derived from truth. Features are one of:

0. intercept only;
1. intercept plus that route's archived support columns;
2. feature1 plus nine line indicators;
3. feature2 plus four route-agreement features: cosine of this route with each route, zero where the other route is unavailable.

Nonfinite support/prediction/truth aborts if the corresponding route/row is declared available; unavailable route support/vectors are replaced by zero. Train-feature means/scales use that route's available calibration rows only, with zero-SD scale1. Intercept is unpenalized. Ridge lambda is exactly0.1,1 or10. This yields12programs ordered feature-major then lambda ascending. S0 is feature1/lambda1 and is always fit on the same16calibration compounds. A route with zero available calibration rows gets accuracy0. Each fitted predicted accuracy is clipped[0,.95]; its weight is rho/(1-rho^2), zero when unavailable. The predicted transcript direction is the unit normalized weighted sum of the four unit route vectors. No fitted generic direction, activity certificate, active-subset filter or magnitude prediction. These are ordinary pooling/calibration programs, not modifications of the historical RKT result.

Per-compound score is the mean cosine across all its included line rows. Episode score is the mean over compounds, giving every compound equal weight. Terminal score uses only the32evaluation compounds. Development feedback uses only the16development compounds. Training labels use only16calibration compounds. No evaluation scalar, archived route cosine/true_norm/active array or historical pooled certificate is exposed to any proposal method.

## Source learning and same-start later intervention

Actually fit and development-score all12programs in each of8source episodes:96newfits of a four-regression solver (up to384route regressions). Source terminal-evaluation scores are not needed and are not computed. The source record contains full ordered program/development scores, S0 score and an episode descriptor. Descriptor=13numbers: four availability fractions and nine line proportions across calibration rows. It uses no development/evaluation response values. Standardize descriptors using source-episode statistics only.

Both old/new improvers are the SAME categorical proposal class over the11non-S0 program IDs, drawing without replacement. Old checkpoint has zero logits (uniform). For program j, new logit is `(sum_e(dev_score[e,j]-dev_score[e,S0])/8)/0.02`; subtract max logit for numerical stability. At each draw, probability is exp(logit) renormalized over unrequested candidates. There is no within-target logit update from target scores: only previously drawn candidates are removed. Development feedback selects deployment. This is ordinary learned proposal ordering, not a new improvement algorithm or unbounded self-improvement. Checkpoint construction sees exactly the source records available to source-history comparators. New source gains do not affect S0 or the target calibration dataset.

The subtracted mean S0 score is constant across programs, so new logits rank programs exactly as source-best mean scores. New versus source-best differs only by softmax sampling versus deterministic top-four. Beating uniform would show ordinary source-prior learning, not an advantage over source ordering or strategy invention.

For every later episode, fit the identical S0 from its calibration data as a shared starting cost outside the four-extra-candidate budget, reveal its development score, then give every proposal arm exactly4distinct non-S0 candidate evaluations. Each evaluation returns only that candidate's episode development score. After four, deploy the development-best of S0 and the four candidates; ties choose smallest program index. Each requested candidate is actually fitted; immutable memoization may share identical same-episode program fits across arms, with logical requests and physical fits both reported. No full-grammar target scores are exposed to proposal arms. Terminal evaluation is performed only after all proposal trajectories/deployment choices and their checkpoint/feedback hashes are sealed. Target-development best is not a terminal-evaluation oracle.

## Comparators and fixed seeds

Run seeds1729,2718,31415, with independent deterministic episode/arm-specific RNG derivation, shared underlying data and no interpretation as independent biological replicates. Arms:

- old/uniform and new/learned categorical checkpoints: exactly four draws without replacement;
- cyclic: first four non-S0 programs in fixed grammar order;
- source-best: first four by mean source development score, descending;
- contextual-ridge: independently regress each program's source development gain over S0 on standardized13-dimensional descriptors using ridge lambda10, unpenalized intercept; propose the top four predicted gains, no target-label training;
- history-nearest: choose the nearest source descriptor by Euclidean distance (source-index tie), propose that source episode's top four programs;
- permuted-source checkpoint: source program gains reassigned among the11non-S0 program IDs by fixed seed99173 before fitting categorical logits, preserving their multiset and keeping S0 fixed. This is a content null, not fewer observations;
- checkpoint restart is exactly old/uniform, reported as an identity control rather than a spurious extra independent arm.

Every arm can retrieve the identical8source records and all96source program scores; source training cost is shared and disclosed equally. The explicit source-best, contextual and nearest-history methods test whether checkpoint storage adds value beyond ordinary fixed meta-learning or retrieval. S0/refit is a zero-search comparator. Full-dictionary refit is feature3/lambda1, exactly program10 in the12-program grammar, one candidate fit using the identical calibration labels; it is reported with its lower search cost rather than artificially charged four fits. A uniform50/50 vector mixture of S0 and full-dictionary is a fixed ordinary mixture comparator; normalize the sum before scoring.

After deployments are sealed, fit any not-yet-requested finite-grammar programs only for an offline terminal oracle. Oracle is best terminal score among12programs, explicitly undeployable, and is not credited as an equal-budget comparator. Report the difference from S0 and from the best deployed comparator. This bounds this finite grammar, not every possible program. Do not count the offline audit cost as feedback available to the policies.

## Claims, stopping and records

Primary C4 difference is new-checkpoint minus old-checkpoint terminal score at identical S0/calibration/development data and4candidate evaluations. Report each of8later episodes and each prespecified seed, plus seed-averaged paired mean. Also compare new against every ordinary arm, full-dictionary refit and mixture, and against the strongest ordinary arm by mean terminal performance as an explicitly post hoc envelope (not a deployable selector). Report source learning cost separately and target physical/logical counts, CPU/wall time and ordered proposals.

This initial screen runs all comparators even if an early difference looks negative. Stop further research on this **arena/grammar** if oracle mean gain over S0<=0, all old/new proposals coincide, or new mean terminal score fails to exceed either old or the strongest ordinary comparator. A positive difference licenses only a separately frozen continuation, not significance, novelty, useful drug-discovery value, agent-world joint benefit or general RSI. No retries, tuned temperature, extra seeds or expanded grammar after results. Report exact finite-sample differences, episode range and seed sensitivity; do not use folds/seeds/line rows as independent biological replicates. No application-usefulness threshold is asserted for transcriptional score.

World contribution, agent planning contribution, inheritance vs solver restart, joint benefit and drug functional utility are NOT_TESTED. New-vs-old checkpoint is a conventional finite meta-learning C4 analogue. The proposal class and its update rule remain fixed, so it does not establish novel strategy invention or stronger recursive improvement.

## Required integrity checks

Verify input SHA256s match the schema audit before response loading; verify protocol/code/manifest freeze before fitting. Verify exact episode disjointness and sizes; block public access to terminal data before deployment seal; do not load forbidden archived label-derived arrays. Confirm each arm uses4distinct non-S0 requests, same calibration hashes, no evaluation feedback, same source records, and selected deployment belongs to evaluated candidates/S0. Confirm source learning remains invariant to synthetic terminal-sentinel substitution. Independently reassemble weighted compound scoring from saved per-row results. Preserve all failures and never overwrite completed result files.
