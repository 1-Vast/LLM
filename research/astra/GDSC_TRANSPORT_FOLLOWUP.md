# Different-layout transport and executable pilot preparation

The new measured diagnostic advances the evidence, but does not establish cheap-state,
STATE or agent benefit. The frozen background predictor beats its development-fixed
two-action comparator on later layouts, yet loses to the other fixed action in a
post-outcome diagnostic. Its average action contrast has the opposite sign to the
measured contrast. The immediate problem is comparator strength and prediction
transport, before another increase in model or agent complexity.

## Sources acquired and gates actually tested

The official GDSC full release and original CTRPv2 archive were downloaded and hashed.
Large originals remain in ignored `tmp`, with versioned receipts and a pinned
[reacquisition script](results/20261002_gdsc_transport_reproduction/acquire_raw.py).
Provider monetary charges and data licences are unknown unless separately documented;
code/package licensing does not certify data usage terms.

| Source | Verified raw content | Qualification result |
|---|---|---|
| Existing GDSC example | All 1,837 plates; exact-menu assignment fields | All three actions remain fixed to positions 124/123/101; no alternative complete layout |
| Official `GDSC2_public_raw_data_27Oct23.csv`, release 8.5 | 15,069,449 native CSV records; 8,745 exact-action metadata rows | Later layouts 231 and 284 measure PLX-4720 10 uM and PD0325901 0.25 uM in different positions; Afatinib does not complete those menus |
| CTRPv2.0 original 2015 expanded archive | 545 compound records; 12,470,175 raw well metadata records; all 15 declared MD5 member checks matched; SHA256 recorded for all 16 members | Afatinib's closest recorded dose is 2.1 uM, PLX-4720's is 8.3 uM; no PD0325901 compound record. No exact original menu |
| CCLE original guessed export route | HTTP 404 receipt | Acquisition unsuccessful, not a scientific dataset rejection |

GDSC full CSV SHA256:
`e915be2948b174982a9b64bea5fab00f6ec8c15f7baa76bc7e2f7a7df295500e`.
CTRP archive SHA256:
`8f62b3b5ed70cfd367cf52ce0a99884dd0a674d1a8c301474b707648689bdee3`.
The recovered CTRP URL comes from fixed pipeline commit
`93d29e9b3171a6aabb30277164e21f73b3c15fec`, with original Git blob receipts.
The downloaded ZIP contains raw wells, pre-QC and post-QC exports and field definitions;
it is not accepted merely because a portal or paper claims large coverage.

CTRP nominal top concentrations are not used to invent actual concentrations.
Dose inspection reads only compound/experiment/plate/concentration metadata columns;
response values, fitted curves and AUCs are not used. The native header explicitly
distinguishes `cpd_avg_pv` from `cpd_pred_pv`. Its transformed luminescence and aggregated
control statistics also differ from the original GDSC blank-subtracted arithmetic.
The inspected archive lacks well coordinates and independently certified state
availability. Full protocol access fails through several normal routes, so exposure
duration remains unknown here. Neither a related MEK inhibitor nor an interpolated
dose is substituted for a measured original action.

The discovery and five source-check directories retain 37 HTTP attempts, including timeouts, 403/404/405/
410/500 responses and successful fallback routes. Two old CTD2 URLs return HTTP 200
but redirect to a general cancer.gov page: these are not successful dataset retrievals.
The cross-study methods article
[Safikhani et al., 2016/2017](https://doi.org/10.12688/f1000research.9611.3)
was obtained as original XML; CTRP article methods were not obtained successfully.
This is a bounded search across official GDSC exports, CTRP original records/protocol
routes and a CCLE route, not an exhaustive claim about public drug-response data.

## A new task frozen before later-layout outcome evaluation

[gdsc_layout_validation.py](gdsc_layout_validation.py) registers a separate two-action
historical transport diagnostic. The change of menu is explicit. It does not estimate
the original C-versus-Afatinib gain and cannot validate the original PD recommendation
branch against Afatinib. Both selected exact actions are measured in the same plate,
with the same four-day Glo assay and original utility calculation.

The raw-format source explains that reference tags `R*-D*-S` are real single-agent
drug treatments and that `NC-1` is DMSO vehicle; an `R` tag is not an untreated control.
It also explains that each plate contains one cell line, `CELL_ID` identifies an
expansion from frozen stocks, and only one scan passing internal QC is published.
These definitions support recorded grouping; they do not expose the complete failed
attempts or independently verify a new physical culture's history.

Of 992 metadata-complete candidate scans in layouts 231/284, 694 have development
parent/component overlap and 98 lack a unique matching original annotation/model
identity. Their records and individual gate columns remain visible. The resulting
200 scans represent 196 original patient/parent components, 196 cell lines/expansion
IDs and 41 dates. Some lines were in the original opened confirmation set: this is
a later-assay diagnostic within GDSC, not cross-study or wholly new-line replication.

The original selected Ridge C model, alpha 10, is reconstructed once from the original
development CSV. No external pickle is loaded, no hyperparameter search or target
fit occurs. Its full original confirmation forecasts match sealed forecasts to
`8.326673e-16`. The new two-action policy is the registered predictor's restricted
argmax, with its original 1e-12 numerical tie rule. The fixed two-action comparator
is selected solely from original development observations: PD0325901.

Source hashes, membership, prediction table, QC, endpoint, weighting, support fallback
and analysis code are frozen in
[the transport freeze](results/20261002_gdsc_layout_freeze_v1/protocol.json).
Only then does the outcome evaluator scan the full source and join selected native
records. All 200 selected scans have both finite measured outcomes and valid matched
controls under the frozen rules; no imputation, clipping or post-outcome QC change
occurs. Shared control source rows and every action source row are saved. All 85/400
out-of-[0,1] utilities are retained. Zero failed selected scans does not certify a
zero failure rate for all attempted laboratory work.

## What the actual run shows

Results use equal original parent/component weights. Point differences describe
published records; no physical confidence interval or mechanistic claim is made.

| Layout | Scans | C2 minus development-fixed PD, ATP inhibition pp | C2 minus fixed PLX, pp, post-outcome diagnostic |
|---|---:|---:|---:|
| 231 | 22 | +2.509 | -5.407 |
| 284 | 178 | +4.411 | -0.428 |
| Pooled | 200 | **+4.207** | **-0.961** |

The frozen C2 policy chooses PLX in 71 scans and PD in 129. Its point utility is
0.17230, versus 0.13022 for the development-fixed PD policy. The full-panel fixed PLX
point utility is 0.18191. The latter comparison is explicitly in a separate
[post-outcome diagnostic](results/20261002_gdsc_layout_diagnostics_v1/summary.json);
it does not replace the registered comparator or select a deployable target-fitted
policy. Both layouts have the same sign for each fixed-action comparison.

Average predicted PD-minus-PLX is **+3.893 pp**, while measured average PD-minus-PLX is
**-5.168 pp**, a mean contrast error of **+9.061 pp**. Contrast RMSE is **26.975 pp**.
The selected action agrees with the single measured paired ranking in 113 scans,
disagrees in 86, and has one numerical measured tie. These are observed-readout ranks,
not certified correct biological choices or mechanism outcomes. No new refusal rule
is introduced and no deployment savings or dollars are assigned.

On these published records, the frozen policy's point value exceeds the registered
development comparator, but this does not establish generalizable information value
or superiority to both fixed policies. Part of the apparent gain can arise because development-
selected fixed PD transports poorly. Different wells reduce dependence on the exact
old positions; each new layout still binds each action to a fixed position. Layout,
date, composition, medium and annotation changes remain entangled. The two layouts
are not randomized treatment-to-position crossover experiments.

Do not recalibrate or search models on these opened outcomes. Keep C as a comparator;
the next independently registered experiment must include all fixed actions and test
the relevant absolute contrast calibration, not only gain over one weak comparator.

## Executable randomization preparation

[gdsc_pilot.py](gdsc_pilot.py) generates a deterministic, seeded proposed roster,
24 planned culture IDs, randomized well assignments and an unfilled event ledger.
Selection uses only original identity metadata and sealed C recommendations: four
unique lines per recommendation stratum. It does not select on measured response.

The executed generator produces **336 terminal wells plus 48 destructive sister
baseline wells on eight plates**, across four planned days. Each proposed culture
has all three exact actions in triplicate, three vehicle wells and two medium blanks.
Two sister baseline wells per culture are technical repeats. Every line's two starts
are on different days; each day has six planned cultures. Drug, vehicle and blank
locations are randomly assigned across the day's plate. There are no duplicate wells.

This is a feasibility/repeatability allocation, not a powered confirmation or 24
independent donors. All execution flags are false; culture verification flags are
false; actual times, measured outcomes and costs remain empty. Twelve terminal and
84 baseline wells per day are unallocated for calibration/additional controls or
failures. Appropriate baseline blank/calibration placement and actual media must be
resolved before physical execution. ATP baseline is not a certified GR cell count.
The allocation is ready to inspect and instantiate once real laboratory records and
handling/calibration details exist; no physical work is claimed.

The proposed protocol now includes frozen C and **each of the three fixed actions**
as comparators. Actual background must be recorded before results. Randomized positions
and separate starts directly address the remaining design issue. Power, a single
minimum meaningful effect, refusal/QC calibration and costs remain prerequisites for
confirmation, rather than numbers inferred from a favorable point difference.

## Eight questions: current decisions and discriminating next tests

| Question | Evidence now | Unresolved explanation | Next discriminating test; continue/modify/stop |
|---|---|---|---|
| 1. Objective | Four-day ATP action value, two-action diagnostic and three-action pilot defined | Net value and a practical minimum gain unknown | Register one estimand/cost contract before confirmation; stop deployment claims while unknown |
| 2. Real decision space | Both actions measured; C2 changes 71 choices and gains vs development PD | Fixed PLX is stronger on the opened target; fixed-layout confounding persists | Compare C with every fixed action under randomized positions; continue only for independently replicated meaningful gain |
| 3. Cheap input | Original background gives some recorded predictive signal | Later annotations, identity and assay/culture structure can carry shortcuts | Record actual background and one cheap measured state prospectively; stop conflating seeding settings with measured state |
| 4. Signal loss | New ATP task has no zero-surrogate bottleneck; mean relative forecast has wrong sign | Calibration/domain shift vs biology/layout cannot be separated | Measure exact contrasts across randomized positions/starts; modify calibration only using separate development data |
| 5. Seed aggregation | Registered Ridge/selection deterministic | More seeds cannot repair physical or transport error | Use independent starts and control calibration; stop additional inference-seed expenditure for this predictor |
| 6. Dual-core linkage | Predictor changes archival choice | Static argmax requires no agent; no incremental acquisition value shown | After an identified measurement contract, compare evidence scheduling to a strong equal-budget single selector; stop architecture-benefit claims now |
| 7. Evidence scope | Native ATP supports assay differences | Mechanism, target dependence and clinical killing unconfirmed | Orthogonal target/phenotype and competing-prediction experiment if mechanism is the registered task; do not label ATP as mechanism truth |
| 8. Attribution | Unopened later-layout evaluation frozen; posthoc diagnostics separated | Comparator drift, layout and selection remain | Independent randomized full-menu confirmation with all fixed baselines; stop current superiority claims if it cannot exceed the registered practical comparator |

The decision-value chain has measured action differences and a prediction-to-choice
link, but no demonstrated state input contribution, superiority to the stronger
fixed action, or net deployment value. The mechanism-value chain remains untested.

## Reproduction and verification

Use maestro and new output directories. The existing pinned PR snapshot can be
reconstructed with the prior review's acquisition script if absent. No PR merge is
required. The existing raw caches can be reused after verifying their frozen SHA256;
the optional reacquisition command downloads approximately 2.46 GB of originals.

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
# Optional, when originals are absent: stream/hash into a new ignored cache.
& $py research/astra/results/20261002_gdsc_transport_reproduction/acquire_raw.py --out tmp/NEW_TRANSPORT_CACHE
& $py -m research.astra.gdsc_transport --csv tmp/NEW_TRANSPORT_CACHE/gdsc.raw.txt --prior-metadata research/astra/results/20261002_gdsc_transport_discovery_v1/exact_menu_metadata.csv --out research/astra/results/NEW_LAYOUT_METADATA
& $py -m research.astra.gdsc_layout_validation prepare --snapshot tmp/gdsc_review_15fec7c --metadata research/astra/results/NEW_LAYOUT_METADATA/exact_menu_metadata.csv --source tmp/NEW_TRANSPORT_CACHE/gdsc.raw.txt --out research/astra/results/NEW_LAYOUT_FREEZE
& $py -m research.astra.gdsc_layout_validation evaluate --freeze research/astra/results/NEW_LAYOUT_FREEZE --out research/astra/results/NEW_LAYOUT_EVALUATION
& $py -m research.astra.ctrp_qualification --archive tmp/NEW_TRANSPORT_CACHE/ctrp.raw.txt --out research/astra/results/NEW_CTRP_QUALIFICATION
& $py -m research.astra.gdsc_pilot --snapshot tmp/gdsc_review_15fec7c --out research/astra/results/NEW_RANDOMIZED_PILOT
& $py -m research.astra.verify --out research/astra/results/NEW_TRANSPORT_VERIFICATION
```

The frozen two-action analysis source itself must remain unchanged between prepare
and evaluate. New contract tests verify metadata response independence, exact dose
matching, shared controls, missing/failed/duplicate/nonfinite outcomes, unaltered
action identity, nonpositive controls, tie rules and complete randomized allocations.
The initial nine contracts pass; the final expanded twelve pass, with no errors/skips.
Scoped maestro verification passes **358 tests**, including **159 ASTRA contracts**,
with zero failures, errors or skips. The twelve new contracts are included in that
count; the counts are not summed. The full prior repository suite, original 60 model
fits and 888 archival ledger cases are not rerun. The scoped verification receipt is
linked from the ASTRA index and daily log.
No production `src/tools`, dependency, checkpoint, original threshold or frozen history
is modified. There is one registered model reconstruction, no new model selection,
no STATE forward, paid LLM request, real culture, or physical state assay. HTTP calls
are real source access, not LLM or STATE experiments.
The native assay exposure is four days. Process compute time was not instrumented;
download durations are recorded separately in HTTP receipts and cannot be summed as
wall time across concurrent requests. Compute charges, assay/state costs and net
deployment value remain unknown.
