# Cheap-input dual-core research: eight questions

The next scientific claim is conditional: affordable information available before
assignment must predict generalizable relative action value, survive the model and
selector, and improve measured decisions or evidence acquisition. The decision-value
and mechanism-value chains are separate. This round prioritizes questions4,2,5;
it adds a real observed-RNA coverage audit and bounded resampling diagnostics, without
claiming that the other questions have been solved.

## New evidence and limits

[`decision_space.py`](decision_space.py) reads the pinned c39 file and retains native
observation IDs, source rows, sample IDs, plate, formulation, filter strata, EGR1
coordinate and file SHA256. It makes no new predictions or physical experiments.
The [final run](results/20261002_decision_space_v2/summary.json) contains146 exact
nonsolvate Trametinib treatment cells in six conditions and586 control cells across
14 plates. There are732 traceable rows. Only5/146 treated cells have nonzero EGR1.

| Exact dose, uM | Plate | Treated cells | Native sample | All-row EGR1 mean | Same-plate control mean |
|---|---|---:|---|---:|---:|
|0.05|plate1|6|smp_1529|0|0.540802|
|0.05|plate10|14|smp_2427|0|0.442571|
|0.5|plate2|30|smp_1625|0.101515|0.729695|
|0.5|plate11|17|smp_2523|0.122000|0.330687|
|5|plate3|39|smp_1721|0.104643|0.339618|
|5|plate12|40|smp_2619|0|0.301597|

These are normalized log1p RNA, not viability or raw UMI. No plate has even one
measured pair from the exact three-action menu. Dose and plate families are
confounded; control centering does not prove the absence of action-by-batch effects.
Each treated plate has one native sample, not a certified independent culture.
Solvate records are a distinct formulation and cannot fill missing actions.
Full/minimal strata are preserved, not selected after seeing means: for example,
plate11 middle-dose full-only cells have mean0 while its all-row mean is0.122000.
These strata do not provide complete attempted-experiment failures or assay QC.

Of27 original pool/seed/action predictions, only9 have a measured same-plate/action
condition;18 remain missing. Two predicted zeros correspond to a positive observed
condition mean. Conversely, some positive predictions correspond to observed zero
means. These are descriptive development disagreements, not out-of-sample error or
state-blind/visible comparisons. Training exposure, parental linkage and biological
calibration remain unknown. Full-source controls must not be confused with the
30-cell frozen sampled input pools.
CSV EGR1 values round-trip exactly to their original float32 dtype. Reproducing
native means from CSV requires reading EGR1 as float32 before float64 aggregation;
default float64 parsing of decimal text can differ slightly from the native values.

## 1. What does the system optimize?

**Evidence.** The production expected-coverage path maximizes weighted anticipated
hypothesis coverage under budget, with cost/size/priority tie handling
([acquisition.py](../../src/maestro/acquisition.py)). The STATE diagnostic maximizes
negative predicted mean EGR1 over Trametinib0.05/0.5/5uM; it has no validated
intervention utility. Expected terminal decision value exists as a separate planning
function; it does not automatically authorize evidence updates.

**Unknown.** The current data do not define biological efficacy utility, assay failure
and refusal losses, operational state cost, or a minimum meaningful improvement.
Neither1e-6 numerical ties nor an expression decrease supplies these quantities.

**Next experiment.** Freeze three task contracts independently: intervention selection
(complete exact-dose menu plus control, actual phenotype endpoint); mechanism
discrimination (explicit competing claims and registered target/proximal/phenotype
tests); next-evidence selection (registered measurement menu, reduction in terminal
decision loss). Price interventions, input collection, waiting, failures and refusal
before opening confirmation outcomes. Choose each meaningful delta from the scientific
decision requirement and development measurement precision, not a test-set ranking.

**Continue/modify/stop.** Continue technical RNA diagnostics. Modify the objective and
measurement contract before efficacy evaluation. Stop promotion of EGR1 ranks to
intervention utility while that bridge and meaningful delta remain unspecified.

## 2. Is there real decision headroom?

**Evidence.** The new six-condition audit establishes actual RNA response coverage,
the sparse EGR1 readout and missing within-plate action pairs. Dose/plate family
confounding is now an explicit field-level obstruction, not just an unspecified
need for more data. Differences between observed means are real descriptive values;
they do not identify the effect of replacing an action on a common parent population.

**Unknown.** Intervention utility differences and state-induced ranking changes are
unidentified. The data do not establish that actions are equivalent, nor that a
better dose exists. A zero EGR1 readout does not mean no viable-cell effect or no
other informative response. RNA sample counts are not independent physical repeats.

**Next experiment.** First obtain an outcome-only headroom panel: independently initiated
parent cultures, random sister allocation to all three doses and controls within each
block, the same actual phenotype endpoint, recorded attempts and costs. This stage
does not require STATE or expensive RNA availability. Use development blocks for
variance/QC/delta and power planning, then unopened confirmation blocks. Only if useful
headroom exists add authenticated cheap predecision information to test rank reversals.
Inspect both average action contrasts and reproducible parent-level heterogeneity:
opposing conditional advantages can cancel in the average, so lack of a significant
marginal contrast does not by itself stop state-interaction research. Apparent
post-hoc heterogeneity still needs predictable predecision information and independent
validation to become a feasible conditional policy.
Randomized action logs or randomized full-policy designs are valid alternatives if
their support, allocation, interference and denominator contracts are established;
same-cell counterfactual observation is not required.

**Continue/modify/stop.** Continue if independently validated utility contrasts exceed
the predeclared delta. Modify endpoint/menu if EGR1 remains uninformative while a
qualified phenotype differs. Stop pursuing gains on this menu only if an appropriately
validated upper bound excludes meaningful gain for the assessed population and
feasible input-conditioned policies; currently the status is unknown.

## 3. Do cheap inputs contain the required information?

**Evidence.** Current STATE consumes registered basal RNA and perturbation onehot.
Cell context and plate choose matching pools; a disabled batch encoder does not
remove distributional batch shortcuts. It does not directly consume targets, GO,
structures or mechanism prose. Historical2000-dimensional controls have a limited
technical input certification. New-RNA equivalence and31 axis coordinates remain
unresolved. The separate PublicTargetGOKernel and RidgeRNA retrospective experiments
have negative results; neither is STATE. No cheap real-time marker input is certified.

**Unknown.** Context-only, drug-only, a small measured marker panel and full RNA may
carry different amounts of relative-action information. Their decision availability,
operational prices and incremental generalization are unmeasured. Test names using
"cheap" refer to inexpensive software gates, not certified low-cost biology.

**Next experiment.** In the qualified headroom panel freeze an input ladder: context
and designed drug information C; C plus a small affordable measured panel S; separately
C plus fully authenticated RNA. Record acquisition/processing/available/assignment
events. Fit named simple auxiliary predictors on development units; do not pad sparse
markers into STATE RNA or call auxiliary results STATE. Compare predictions of action
contrasts, not just overall response, on held-out parent/batch components. Include
identity/batch baselines and within-context state permutation. Hold out chemistry or
cell contexts separately when claiming those kinds of generalization.

**Continue/modify/stop.** Continue an input only if its held-out contrast prediction
and net decision value improve over C at its measured cost. Modify it if gains vanish
after batch/identity controls. Stop calling it cheap-state value when chronology,
cost or out-of-unit performance fails; retain an unknown result if power is insufficient.

## 4. Where is the signal lost?

**Evidence.** The [native audit](ZERO_AUDIT.md) certifies EGR1 identity locally and
traces288/288 exact zeros in18 action means to strictly negative final pre-ReLU
values. All9 replays are byte-identical; export does not alter EGR1. Seven original
refusals are exact top ties. Thus these zeros are not missing-field imputation,
rounding or signed averaging. The new observed panel also has sparse EGR1, but model
and observed zero patterns do not agree perfectly.

**Unknown.** Final ReLU clipping alone cannot distinguish correctly sparse biology,
miscalibrated projection, an unsuitable single-gene endpoint, batch shift or a poor
control pool. ReLU is part of the registered model contract; its presence is not
proof of a software bug. Continuous latent differences may be lost before the
official output, but latent negatives are not measured RNA or validated utility.

**Next experiment.** Validate frozen model readouts against matched actual RNA and
the declared phenotype in common-parent complete-action development blocks. Examine
zero mass, dynamic range, calibration and action-contrast errors. If choosing an
alternative gene/program readout, choose and lock it in independent development
data before confirmation, with an explicit endpoint link. Preserve the original
EGR1 rule as a comparator and do not remove ReLU to manufacture a winner.

**Continue/modify/stop.** Continue when the legal output readout retains reliable
measured action contrasts. Modify readout/model if observed contrasts are present
but predictions systematically flatten them. Stop this readout for selection if its
validated useful-resolution bound is inadequate; do not equate that with no biology.

## 5. What does multi-seed aggregation stabilize?

**Evidence.** Seeds resample fixed historical controls. They are not biological
states, model ensembles or future experiment draws. At K=3, Plate10's internal
middle-minus-high mean and descriptive MC SE are both0.01015909. The middle-minus-low
mean is0.05298151 with MC SE0.05131179. The
[bounded omission diagnostic](results/20261002_decision_space_v2/sampling_diagnostics.json)
restores a top tie when omitting seed42 on plate1 or seed17 on plate10/11. This is
post-hoc sensitivity description, not an adaptive seed-selection procedure.

**Unknown.** Neither exact replay nor the unique three-seed aggregate certifies
adequate MC precision or real advantage. Biological variance, model bias and domain
shift are not estimated by sd/sqrt(K). Averaging computational draws cannot prove
that measurable state heterogeneity was preserved or destroyed.

**Next experiment.** After endpoint/headroom validation, predeclare a bounded paired
K or valid sequential precision rule and numerical target in development. Keep real
predecision S separate from resampling seed; compare conditional policies across
states against the context-only aggregate on independent units. Establish validated
intervals for the intended estimand rather than treating seed variation as outcome
noise. Current linear EGR1 utility does not generalize to nonlinear U(E[Y]) versus E[U(Y)].

**Continue/modify/stop.** Increase K only when authenticated MC error is the limiting
factor and the fixed compute budget can help. Modify modeling/calibration for bias
or domain shift. Stop increasing K for the current biological claim until the
readout/action evidence gaps are resolved. Return a unique numeric rank separately
from a scientific recommendation; retain candidate sets or refuse when valid
meaningful-advantage intervals are unavailable. Nonsignificance is not equivalence.

## 6. How do the two cores act together?

**Evidence.** ASTRA `DecisionPath` distinguishes diagnostic and explicit selection
use, binds raw prediction identities, filters execution and preserves one final
submission. Software fixtures prove that injected predictions can change actions.
Real STATE pool replacement changes4/9 decisions through refusal only, with no
concrete action switch or measured terminal. `zero_audit` now returns contrasts,
estimand, sampling source, original refusal causes and scientific candidate sets.
The default production coverage selector is not a deployed four-way scheduler.

**Unknown.** STATE's continuous RNA does not provide authenticated mechanism-specific
reading distributions or full attempted-experiment success probabilities. Available
`OutcomeForecast` and decision-value functions are not automatically connected to
the production orchestrator. Biological outcome improvements remain untested.

**Next experiment.** Bind a development-only selector to one qualified task and
freeze four catalogued behaviors: compute only for reducible MC error; buy a
measurement only under a calibrated reading/consequence model; execute an admissible
intervention only with certified advantage and constraints; otherwise stop/return
unknown. Return prediction applicability, joint contrasts, covered/uncovered
uncertainty and measured costs. Where branch probabilities are unavailable, return
that limitation instead of creating them from EGR1 amplitude. Compare against the
same selector with blinded information using matched budget and measured results.

**Continue/modify/stop.** Continue a behavior only with an independently observed
benefit at its resource cost. Modify interfaces if reliable predictions do not
change decisions. Stop automation of biological claims or added measurement spend
when the prediction-to-consequence contract is missing; software wiring can remain
under contract tests without an efficacy claim.

## 7. Which evidence supports which claim?

**Evidence.** Production nodes distinguish engagement, proximal function, pathway,
cell state and phenotype. Qualified results enter registered outcome rules;
prediction artifacts do not become measurements. Forecast Brier/log loss scores
evaluate readings, not mechanism probabilities. Planning Bayes calculations in
`expected_terminal_decision_value` expressly do not authorize validator conclusions.

**Unknown.** EGR1 suppression alone lacks a validated map to survival, engagement
or MEK-mediated survival effects. A small p-value, GO association, agent agreement
or repeated analysis does not identify a mechanism likelihood ratio. The mechanism
null must imply the tested statistical null, or the test must be valid under every
distribution permitted by the mechanism null. Only then can statistical rejection
challenge that mechanism. No-MEK-mediated effects can still include off-target RNA
changes, so an RNA-response test alone does not reject that mechanism null.

**Next experiment.** Freeze competing claims, for example MEK-dependent phenotype
versus a non-MEK-dependent effect, alongside a no-valid-phenotype alternative. These
are hypotheses, not established causes. Obtain actual RNA for transcriptional
response, actual viable-cell/apoptosis outcome for phenotype, and direct engagement
or a validated proximal assay for the relevant target claim. A causal claim needs
orthogonal perturbation/rescue/competition and reviewed linkage to phenotype,
with appropriate timing, dose, controls and off-target assumptions. Use either a
validated p(data|H1)/p(data|H0) contrast or a predeclared discriminatory evidence rule
whose premises are met. Count shared samples/controls once and retain failure/QC.

**Continue/modify/stop.** Continue only the claim actually supported by its measured
node and reviewed premises. Modify experiments when competing explanations make
the same predictions. Stop mechanism acceptance from RNA alone or from a model
forecast; report unresolved rather than converting an expression statistic into
causal confidence. Statistical confirmation is not a universal causal proof.

For an authenticated likelihood model, posterior odds equal prior odds times
`p(actual data | H1) / p(actual data | H0)`. The actual data include the appropriate
experimental dependence and, when modeled, QC/failure events. A forecast conditional
on a valid readout is not the likelihood of all attempted experiments. Those
likelihoods and premises are not supplied by the current EGR1 audit, so it performs
no numerical mechanism-confidence update.

## 8. How is benefit attributed to the proposed mechanism?

**Evidence.** Existing real-data auxiliary tests are negative; software swaps establish
possible influence only. No real head-to-head strong-single-agent versus multi-agent
comparison establishes biological gain. Current dose/plate structure cannot supply
independent complete-action validation by statistical adjustment alone.

**Unknown.** Concrete action gain, refusal value, false mechanism acceptance and net
deployment value are unmeasured. Uncertain mechanism truth cannot silently become
a binary benchmark label. Multiple agents and repeated analyses do not increase
physical replication.

**Next experiment.** After admission freeze independent parent/batch splits and
unopened outcomes; compare fixed action, the same world model with blinded matched
reference, within-context state shuffle, a simple predictor, a strong single agent
and the collaborative workflow. Match available inputs, tools, global menu,
experimental budget, refusal permissions and total token/API/compute budgets;
report parallel latency separately. Predefine swaps that block specific links in
each chain. Report prediction contrast/calibration, concrete switches and utility,
correct/wrong/unknown/refused, refusal contribution, mechanism false acceptance
against the registered truth standard, state/assay/failure/wait cost and compute
time/cost. Missing outcomes remain missing or receive justified frozen bounds,
never model-filled observations.

In the information-contribution comparison, both visibility arms acquire state
and pay the same acquisition/wait cost, masking only its visibility. Separately
compare deployment against a blind policy that does not acquire state. For the
architecture comparison, the strong single agent and collaboration get the same
available information and total resource ceiling; actual spend is reported, not
invented to match a ceiling. Predeclare primary comparisons and selected-action
interval/calibration rules to address selection among multiple actions or strategies.

**Continue/modify/stop.** Continue when held-out measured gain exceeds meaningful
delta at acceptable error and net cost, survives blind/shuffle/simple/single-agent
controls and supports the specific attribution. Modify if prediction gains do not
reach actions or actions do not improve outcomes. Stop this strategy when validated
gain upper bounds exclude meaningful benefit or errors exceed the frozen tolerance;
crossing the threshold means inconclusive, not proven no benefit.

## Two proof chains and the next concrete unit of work

| Chain | Currently evidenced | Still missing |
|---|---|---|
|Decision value|Historical input changes predictions; numeric output/selection paths audited|Affordable lawful S, generalized relative utility, useful action change, measured gain|
|Mechanism value|Typed measured-evidence rules and software forecast linkage|Discriminating actual design, qualified measurements and reviewed inference premises|

The immediate experiment is the outcome-only common-parent randomized action panel
in question2, with a phenotype and accompanying RNA readout check for question4.
Its complete ledger must contain parent/child, native action/attempt/control IDs,
assignment/execution/results, QC including failures and actual costs. A separate
cheap-state pilot can then record real availability and test generalizable action
interaction. Three pilot batches may reveal feasibility; they do not constitute a
powered confirmation by themselves. Physical-unit intervals require authenticated
independence and an appropriate analysis; three actual independent cultures can
support an assumption-dependent, usually very uncertain interval. Three batch labels
do not establish independence or adequate power.

Freeze meaningful utility delta, refusal loss, endpoint and compute precision before
confirmation; the present audit deliberately leaves their unavailable values unknown.
STATE chronology/input certification remains a separate gate for calling an experiment
a STATE biological test. No imagined lab result or arbitrary outcome interval is
introduced to close either proof chain.

## Runs, negative results and reproduction

The first descriptive coverage output stays in `20261002_decision_space_v1/`. The
final v2 adds seed-omission diagnostics, explicit five-nonzero count and unambiguous
query-action count names; its source/inputs and outputs are hashed separately.
No historical artifact, src or tools file changes. No new STATE forward or external
API is needed for this round. Costs remain unknown; local execution is not declared free.

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py -m research.astra.decision_space --out research/astra/results/NEW_DECISION_SPACE_DIRECTORY
& $py -m research.astra.verify --out research/astra/results/NEW_EIGHT_QUESTIONS_VERIFICATION
```

Use new directories and pinned local c39/model evidence. The raw source SHA is
`5a5c9aab50be5118b1dfe949e9f0d3bca75f74944e7993bd77dc5b377e5d1f25`.
The existing registered checkpoint and NCI-H596 scope remain unchanged; actual
training exposure is unknown. The observed RNA agreement is development evidence,
not STATE efficacy or deployment value. The full prior1,861-test run and36 native
observation forwards are historical results, not new runs in this round.

The final scoped maestro verification passes341 tests, including142 ASTRA contracts,
with0 failures, errors or skips. All original snapshots,11 grid inputs and96 frozen
grid outputs match. The documentation/navigation follow-up passes21 repository-shape
checks; those overlap the scoped run and are not summed. Receipts are in
[`20261002_eight_questions_verification`](results/20261002_eight_questions_verification/receipt.json).
Independent review corrects the mechanism-to-statistical-null implication direction
and clarifies that verified independent pilot cultures can support assumption-dependent
intervals; batch labels alone cannot. It also retains opposing parent-level action
advantages as a possible interaction even if the marginal contrast cancels.

## Subsequent executed phenotype task

The historical sections above retain their original STATE/Tahoe scope. The later
[GDSC_SCREEN.md](GDSC_SCREEN.md) selects a new, explicitly frozen three-drug phenotype
task and executes real same-plate measurements with a patient-and-date holdout.
It updates questions 1/2/3/6/8 with measured offline evidence: the added seeding-density
policy has -0.52 ATP-inhibition percentage points versus the background policy,
97.5% CI [-1.69,+0.65]. Its upper bound is below the frozen 2/5/10/20pp sensitivity
thresholds under the stated cluster-inference assumptions. The background signal is
positive but meaningful/net deployment value remains uncertified. Molecular state,
mechanism discrimination, STATE superiority and four-way scheduling remain open.
