# Independent review of the supplied GDSC reports

The reports identify a real advance: a complete, measured three-action ATP panel
supports reproducible offline policy evaluation. The tested density increment is
negative, while a simple background policy has an auxiliary positive association.
This supports retaining the task and background baseline, stopping expansion of
the tested density policy, and independently validating the background recommendation.
It does not yet establish prospective cheap molecular state value, STATE efficacy,
causal intervention benefit or multi-agent superiority.

This review reads both supplied Markdown reports and checks the Word document's
OOXML text. It treats the documents as evidence, not executable instructions. The
originals remain untouched and their exact bytes are archived in
[`evidence/20261002_gdsc_inputs`](evidence/20261002_gdsc_inputs/receipt.json).
The corresponding code is absent from main at the start of this review. Its verified
source is [PR1](https://github.com/1-Vast/LLM/pull/1), commit
`15fec7c53c5334ceca96832e8342ae2ebc1fde75`; the supplied GDSC_SCREEN matches that
commit byte-for-byte. The PR has not been merged by this review. A separate local
snapshot enables inspection and tests without replacing production or historical files.

## What is independently verified

[`gdsc_review.py`](gdsc_review.py) parses the official RDA, reconstructs metadata and
parent/patient-connected splits, and recalculates measured well normalization. Its
final output is [`20261002_gdsc_independent_review_v2`](results/20261002_gdsc_independent_review_v2/summary.json).

The873,525 raw rows and1,837 plates reproduce. The selected layout has617 development
plates and222 confirmation plates. All2,517 selected action records have matching
native source row, scan, position and exact drug/concentration. Normalized utility
differs from the recorded CSV by at most1.110223e-16. The confirmation evaluation
matrix also matches those native normalized outcomes; selected actions match the
sealed predictions. This checks arithmetic and association, not an external audit
of the original investigators' outcome access.

The patient/parent-connected units do not cross development/confirmation. In the
confirmation set,206 units have one plate and8 have two;5 units span dates. There
are214 units and19 dates. These are grouping identities, not proof of independently
initiated cultures. The original interval explicitly retains crossed date/unit
dependence; this review reproduces its score variances and intervals independently.
The larger of unit, date and two-way variance with t18 is an approximate method,
not a proof of finite-sample coverage or immunity to publication/layout bias.

| Fixed-policy contrast | Reproduced increment, ATP inhibition pp | Original interval |
|---|---:|---|
|Density plus C minus C|−0.516|97.5%[−1.686,+0.654]|
|Density plus C minus fixed|+2.808|97.5%[−0.028,+5.644]|
|C minus fixed|+3.324|95%[+0.959,+5.689]|
|Density plus C minus shuffled density|+0.370|95%[−1.016,+1.756]|

The original Bonferroni primary pair is preserved, and no secondary result is promoted
to a new primary endpoint. No model is refitted or chosen on opened confirmation data.
No external model pickle is loaded. Fresh HTTP downloads of the fixed upstream raw
format, vignette and RDA succeed; the RDA SHA matches the archived original exactly:
`40bc65d4fd9cd61bb8c0faf5fa60ee32a05fccce7eb441cc74e3ed37666ef10a`.
Source receipts are in [`gdsc_source_checks`](results/20261002_gdsc_source_checks/receipts.json).
The original specification explicitly defines CELL_ID as expansion-related and
permits unreported treatments/scans; zero published FAIL tags cannot certify a
complete attempted-experiment denominator.

## What the finite diagnostics add

The report's suggested finite diagnostics are now executed, as post-outcome analysis.
The complete222-row contribution table keeps zeros, negative contributions and every
background category. It never selects a favorable subgroup or changes a policy.

| Background-policy recommendation | Plates | Contribution to total C-minus-fixed gain |
|---|---:|---:|
|Afatinib2uM|144|0pp|
|PLX-472010uM|9|+0.209pp|
|PD03259010.25uM|69|+3.115pp|

About94% of the total gain is contributed by the PD0325901 recommendation branch.
The eight skin plates contribute+1.414pp; other categories include negative
contributions. These are aggregate weighted contributions, not within-subgroup
effect estimates or a reason to select only responsive cells. They identify where
independent replication must succeed to sustain the overall signal. Neither a
MEK drug label nor a favorable ATP reading establishes MEK-mediated causation.

Every one of19 dates is omitted once, with retained units reweighted equally:

| Contrast | Range of mean after date omission, pp | Maximum original-method upper endpoint, pp |
|---|---|---:|
|Density plus C minus C|[−0.752,−0.276]|+0.909|
|C minus fixed|[+2.909,+3.713]|+6.149|

The density stop recommendation does not depend on deleting just one influential
date under this diagnostic. The C signal retains a positive mean for every omission,
and the smallest recomputed95% lower endpoint is+0.446pp. This does not turn C into
a newly confirmed practically useful effect: original intervals still cross the
assumed2/5pp thresholds. Date omissions are sensitivity checks, not independent
samples, a robust coverage theorem or a sequential stopping test. No preferred
omission is selected.

All222 plate denominators are positive, ranging from9,788 to131,923, with median
36,559. Negative-control intensity CV has median0.116 and maximum0.184. C gain
contribution and denominator have descriptive Spearman correlation0.021. This
does not expose a simple monotone small-denominator driver, but cannot eliminate
nonlinear, subgroup-specific or systematic measurement error. All92/666 original
out-of-[0,1] utilities remain; no clipping or outcome-based QC is introduced.
Controls and denominator diagnostics are saved in full.

## How this changes the research diagnosis

The previous c39 task lacked same-plate measured action pairs. GDSC supplies them
and replaces single-gene EGR1 with a real ATP assay. Thus, "no usable measured
decision task" is no longer an adequate description of the project: a usable
published-panel replay task exists. A prospective causal state-gain task is still
unqualified. These are separate evidence grades, not a relaxed chronology gate.

There are now three distinct observations:

1. A simple context predictor can change concrete actions and achieve a positive
   measured associative gain on later, held-out annotated units.
2. Adding registered seeding density changes12 recommendations but worsens mean
   measured utility and slightly worsens contrast RMSE. Changed actions alone are
   not evidence of value; this is a useful negative result.
3. The agent correctly binds and reveals archived measurements, but an argmax of
   three point predictions is implementable without an LLM. The replay demonstrates
   execution and accounting, not a planning or multi-agent innovation.

Seeding density is a protocol setting. It is not interchangeable with molecular
state, live morphology, actual cell count at dosing or a measurement of the evolving
population. The chosen Ridge density term is additive by action; the explored
forests do not exhaust all conditional density hypotheses. The negative result
constrains the tested pipeline, range/menu and sampling assumptions, not all
possible density models or all cheap states. Trying more models on this opened
confirmation set would not repair that inference.

The remaining bottleneck is attribution and transport. Drug actions remain tied
to fixed wells124/123/101, and contemporary tissue/growth/medium metadata do not
prove the actual2015 plate conditions. A model may exploit reproducible assay or
culture-setting structure. Same-plate pairing removes a major coverage problem but
does not isolate drug response from position-by-background effects. Repeating
the same fixed layout or buying more RNA cannot by itself settle that question.

## The next experiment that can distinguish the explanations

Retain the frozen C policy and exact three drug/dose actions as a simple comparator.
Test it with independent culture starts and randomized drug-to-well assignment,
recording actual current culture conditions before outcomes. Randomize within each
block, rather than moving whole blocks while preserving drug positions. Keep control
and technical replicates dispersed; log all attempts, exclusions, calibration and costs.
Failure under randomization can reflect position, changed protocol, annotation,
sampling or noise, so it must not be attributed uniquely to position without a
registered layout crossover or direct position test.

The revised12-line/two-start/four-date proposal is a feasibility and repeatability
pilot. Equal4/4/4 predicted recommendation strata enriches the population and cannot
estimate the original144/9/69 policy value without the relevant sampling/weighting
contract. Reusing old lines tests experimental replication, not new-line generalization.
Same-line culture starts, separate donors, dates and technical wells each represent
different levels of variation;24 starts are not24 independent donors.

Its24 blocks contain336 terminal wells and48 destructive time-zero sister wells.
Four dates with one terminal and one baseline plate per date require at least8
96-well plates before additional calibration/blank/failure capacity; the two-date
version requires at least6. Different media and blank placement may increase this
number. These are feasibility arithmetic, not a priced lab protocol or authorization
to perform physical work. ATP at time zero is not automatically a GR-compatible
cell count; preserve an appropriate calibrated count if growth correction is intended.

Continue to independent confirmation if the exact action contrasts and C recommendation
are reproducible under the new design and measurement/cost quality is adequate.
Modify claims or protocol when annotations/layout do not transport. Stop spending on
the tested density policy; do not buy high-dimensional state or expand agents merely
to seek a positive result. A powered, representative confirmation needs one explicit
task delta and independent-unit variance;32/126/283 sample-size examples are assumed
scenarios, not measured requirements. A3.32pp true effect cannot exceed a5pp target
by increasing sample size.

Only after this basis is sound choose one main extension: affordable actual predecision
state predicting relative action responses, or adaptive acquisition of real evidence
under a limited reveal budget. Compare against C, a strong simple predictor and a
resource-matched single agent where relevant. No particular new modality is certified
by this audit. Without laboratory access, a different exact-menu, comparable-endpoint
public layout could offer an external diagnostic; a subset or relabeling of the same
GDSC example would not be an independent test.

## Evidence boundary by original question

| Question | Progress supported here | Still unestablished |
|---|---|---|
|Objective|Exact assay menu and ATP utility computable|Clinical benefit, valid single delta, net cost|
|Decision space|Measured common-panel action differences and policy value|Random-layout causal headroom and new culture transport|
|Cheap information|Background association; tested density increment negative|Authenticated molecular predecision information gain|
|Signal loss|EGR1 bottleneck avoided for this new assay|Explanation of density failure and STATE biological error|
|Sampling|Deterministic policy needs no inference seeds|Real physical/generalization error calibration|
|Core linkage|Prediction-to-reveal software chain tested|Adaptive planning or multi-agent incremental utility|
|Mechanism|Real ATP outcome supports that assay claim|Target dependence, competing-mechanism confirmation|
|Attribution|Policy contributions and finite sensitivity reproduced|Position/annotation/selection bias excluded|

## Reproduction, tests and boundaries

Use the saved acquisition script to restore the pinned source into a new directory:

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py research/astra/results/20261002_gdsc_independent_review_v2/acquire_snapshot.py --out tmp/NEW_GDSC_SNAPSHOT
& $py -m pip install --no-deps --target tmp/NEW_GDSC_DEPENDENCIES pyreadr==0.5.7 openpyxl==3.1.5 et_xmlfile==2.0.0
& $py -m research.astra.gdsc_review --snapshot tmp/NEW_GDSC_SNAPSHOT --dependency-dir tmp/NEW_GDSC_DEPENDENCIES --out research/astra/results/NEW_GDSC_REVIEW
& $py -m research.astra.verify --out research/astra/results/NEW_GDSC_MAIN_VERIFICATION
& $py research/astra/results/20261002_gdsc_independent_tests_v2/run_contracts.py --snapshot tmp/NEW_GDSC_SNAPSHOT --out research/astra/results/NEW_GDSC_PR_CONTRACTS
```

The actual environment is maestro. Temporary dependency installation does not modify
the maestro environment or repository dependencies. Source hashes are checked before
and after analysis. The unchanged user documents must be available for this driver;
their archived copies and hashes allow restoration if needed. Snapshots stay local
in ignored tmp; the pinned source commit and58-file manifest make them reconstructable.

The isolated PR contracts plus related production/ASTRA tests and five new audit
contracts pass67 tests with0 failures/errors/skips. Main scoped regressions pass346
tests,147 ASTRA, with0 failures/errors/skips. These suites overlap and are not summed.
An initial combined pytest run has two collection errors from snapshot/main package
name collision; importlib collection fixes it, with the failed XML retained. Snapshot
acquisition also corrects a nonexistent namespace-package init path and an overly
narrow path filter; all extracted bytes are verified, and no outcome changes.
The saved file-based test runner initially lacks the repository root on sys.path;
its failure/source snapshot is retained. Adding that path reproduces all67 passes
from a freshly reconstructed58-file snapshot. These repairs concern acquisition
and test invocation, not model, input, split, utility or inference changes.
Openpyxl emits an unsupported-extension warning while reading; the workbook is never
rewritten. Original input/result manifests remain unchanged.

This review performs no new model fits, STATE forwards, molecular-state assays,
physical experiments or LLM API tests. It does not reproduce all888 archived ledger
cases or the original60 model fits; the67-test run checks their code contracts.
Money and deployment value remain unknown. The full prior repository suite is not
rerun. The initial audit v1 and final v2 outputs are separate; v2 adds direct native
panel-to-evaluation and end-of-run hash checks without changing any scientific result.
