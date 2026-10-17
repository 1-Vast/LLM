# PRESAGE-inspired biological transfer: P0 fails

Date: 2026-10-16. Verdict: **NO-GO for this target-pathway drug adapter**.
Development on historically exposed PRISM 19Q4; not confirmation. A genuine
gene-feature correspondence signal appears relative to matched nulls, but it does
not improve on strong conventional predictors or retrospective functional ranking.
P1/P2/P3 and the LLM proposer were not run. No scientific model is promoted.

## What PRESAGE contributed

PRESAGE motivated separating source information from architecture and testing a
compact gene representation with strong simple comparators. We inspected the
official implementation at `2c7b231c60cf110c4aab0acf8ecd2c2b3268fffb`.
Its external response sources, preprocessing, PCA, splits, modular model and
functional expression metrics are audited in [SOURCE_AUDIT.md](SOURCE_AUDIT.md).
The original full text returned HTTP 429. Source dominance and learning-curve
saturation are qualitative author-reported findings; exact paper numbers were
not verified. The 3,392,114,905-byte cache was not downloaded: a bounded 2 MB prefix
confirmed that it contains large derived features, beyond simple gene embeddings.

This is a **PRESAGE-inspired pharmacological viability adaptation**, not a
PRESAGE reproduction. No knockdown/knockout/inhibition equivalence is assumed.
Gene-expression strength, phenocopy or gene-set metrics are not viability truth.

## Checkout and implementation

Actual HEAD equals the previously inspected commit,
`6e6a2e4fe0ba44cb58a7d5bc536f4a4d632ec630`. At entry, `research/STUDIES.json`
already had changes and `research/indication_triage_20261016/` was untracked;
that work was preserved. Historical frozen studies and sealed outcomes were not
changed. The registry addition retains the pre-existing indication-triage entry.

Read the central research/evidence/register and log, plus knowledge transfer,
knowledge reality, orbit contrast, collaboration limits, selective hit triage,
mechanism feasibility and evaluator-defect records. Earlier results constrain
this study: annotation-class transfer is not target-biology evidence; RKT's RNA
scope does not cover PRISM viability; mechanism truth is unavailable; and
test-batch normalisation or oracle missingness cannot guide nomination.

Implemented one dated study with a frozen evaluation entry point. Real primary
screen responses cover **4,528 compounds × 568 identified cell lines**, clustered
into **1,145 family/connectivity components** and five outer folds. Reactome_2022
has 1,818 pathway sets, covering 1,528 of 1,795 target symbols and 3,118 compounds.
The first run stopped before fitting because cell metadata included non-cell
controls; amendment A1 and the original freeze are retained. The revised metadata
rule excludes ten barcode controls and ten failed-STR rows without DepMap IDs.

The bridge uses chemical structure, candidate targets, declared pharmacological
classes and known assay-line decoder outputs. It retains chemistry for missing
targets, uses a 64-dimensional projected pathway representation and small ridge
decoders, and keeps inhibition, activation, degradation, mixed and unknown classes
distinct through declared feature rotations. This coding choice is an adapter
assumption, not a pharmacological or engagement estimate. There is no target
feedback, occupancy estimate, unseen-context encoder or fitted dose/time bridge.

All normalisers fit training compounds only. Twenty gene-feature permutations
retain sharing, class, coverage and degree/count strata while breaking target-to-
feature correspondence. Matched random embeddings have the same dimension and
coverage. Neighbour baselines reuse RKT's chemical/knowledge neighbour parameters,
without transporting its RNA calibration certificate into viability.

## Executed results

Pearson is computed per compound across available lines, then averaged across all
metadata-eligible compounds. It includes general line sensitivity; it is not an
identity-specific effect metric. Raw MSE is a secondary metric. Top-3 hits mean
measured log2 fold change <= -1 in the three nominated lines; missing nominated
values consume slots and count as no hit. Every arm has 13,584 nomination slots.

| Arm | Mean Pearson | Raw MSE | Top-3 hits | Hit yield |
|---|---:|---:|---:|---:|
| Training line mean | 0.1661 | 0.7447 | 1,968 | 14.49% |
| Chemical ridge | 0.1450 | 0.7553 | 1,869 | 13.76% |
| Mechanism class | 0.1151 | 0.8098 | 1,759 | 12.95% |
| Chemistry + mechanism | 0.1133 | 0.8162 | 1,812 | 13.34% |
| Chemistry + mechanism + matched random targets | 0.1077 | 0.8275 | 1,809 | 13.32% |
| **Chemistry + mechanism + pathways** | **0.1161** | **0.7771** | **1,903** | **14.01%** |
| Pathways only (ablation) | 0.1482 | 0.7136 | 1,983 | 14.60% |
| Chemical neighbours | 0.1239 | 0.7766 | 2,142 | 15.77% |
| Ungated chemical + target/MoA neighbours | 0.1427 | 0.6734 | 2,223 | 16.36% |
| Fixed pathway / chemistry+MoA fusion | 0.1202 | 0.7791 | 1,899 | 13.98% |
| Ungated pathway residual | 0.1143 | 0.7915 | 1,896 | 13.96% |

The full pathway arm minus chemistry+mechanism is **+0.0028**, family-cluster
bootstrap 95% CI **[-0.0020, +0.0083]**, below the frozen 0.01 development threshold.
Against chemistry alone it is **-0.0288 [-0.0331, -0.0244]**. Against the training
line mean it is -0.0499. The standalone pathway ablation does not rescue the
predeclared incremental-information claim or beat the strongest ranking baseline.

The correspondence null mean is 0.1115 and maximum 0.1140; real correspondence
scores 0.1161, randomisation p=1/21=0.0476. Relative to matched random target
embeddings the gain is +0.0084 [0.0044, 0.0129]. Thus there is a narrow, nominal
alignment signal in this representation, **not a practically useful incremental
biological prediction result**. Twenty nulls give coarse p-value resolution; no
broad multiplicity-adjusted biological discovery is claimed.

Retrospective nomination curves (actual historical measurements, no purchased
assays) favour the existing ungated neighbour alternative:

| Slots per compound | Pathway hits / slots | Ungated-neighbour hits / slots |
|---:|---:|---:|
| 1 | 655 / 4,528 | 789 / 4,528 |
| 3 | 1,903 / 13,584 | 2,223 / 13,584 |
| 5 | 3,109 / 22,640 | 3,600 / 22,640 |
| 10 | 5,971 / 45,280 | 6,758 / 45,280 |

At three slots the pathway arm loses 320 hits, or **-2.36 percentage points**
(post-hoc family-cluster CI [-4.00, -1.12] points). Both nomination lists miss over
99% of all measured pair-level hits because the menu is large and the slot budget
is small; this is the reported false-exclusion metric, not drug rejection or a
NO-GO error. Missing selected values are 1,341 vs 1,931. No calibrated reliability
threshold or abstention arm was fitted, so calibration/abstention is **not evaluated**.
These curves are not P2 independent campaign net benefit or a money-to-utility model.

## Interpretation and generalisation

1. **Prior information:** a small correspondence-dependent signal exists, but the
   predeclared useful incremental gate fails. Do not conclude that all biological
   priors fail; this tests one pathway snapshot, target mapping and compact adapter.
2. **Context adaptation:** not run after P0 failure. No anchor or context-transfer
   improvement is established.
3. **Agent reasoning:** not run. No LLM or autonomous scientific reasoning benefit
   beyond deterministic baselines is established.
4. **Combined decision value:** not established. The pathway system loses to the
   conventional neighbour workflow in this exposed-data ranking diagnostic.

The supported setting is internal compound-held-out prediction with no same-
connectivity compound training response, on already known cell contexts, using
retrospectively available non-response annotations. Across folds, 3,044 test
compounds share a target with training, 1,909 share a MoA and 1,487 share a nonempty
scaffold. Therefore this is primarily setting **C** (unseen compounds, often known
targets/families), not uniform D. No external response sources enter the model;
absence from *all possible* response sources is unaudited, so do not claim B.
A, E and F are not tested. No earlier exposure is relabelled fresh confirmation.

Important limits: Reactome is a derivative snapshot with upstream processing not
independently rebuilt; annotations postdate the historical screen; target engagement
and exact per-row assay timing are unqualified. All ridge fits selected the upper
alpha=100 boundary; the bounded search may under-regularise extra features. No
post-outcome tuning was performed. Family clusters do not certify independent
biological cultures or remove all scaffold/target overlap. A failed gate on this
adapter does not falsify PRESAGE on its original genetic task.

## Thin-loop audit and justified core repairs

`ENGINEERING.json` reproduces on pinned HEAD that support=0 / unrelated-scope
forecasts can spend budget, scores stay static after observations, and a label
declared as measurement moves the heuristic from 0.5 to 2/3. Source name and a
declared independent-unit count do not authenticate evidence. Existing acquisition
already provides source grouping and terminal decision value; world-model requests
already carry hypotheses/history; CaseStore already persists cases. None was
duplicated or replaced.

The surgical runtime repair binds forecast action identity, refuses explicit zero
support, requires matching scope/basis/support for explicitly scoped actions,
rejects nonfinite acquisition inputs/duplicate action IDs/noninteger support, and
preserves original source/QC fields when retaining invalid readouts. Legacy
unscoped callers remain permissive. These guards validate declarations only.

The loop still uses static scores and hypothesis-label counts and has no local
EvidenceLedger authentication. It is **not** a measured biological inference engine
or validated adaptive policy. Correct scientific use remains the existing registry,
strict review, terminal-value selector, world-model contracts and case persistence.
No likelihood, lineage integration or joint policy is claimed implemented here.

## Cost, reproducibility and decision

Real-data evaluation: 75.63 seconds wall / 97.03 seconds process CPU in
`D:\anaconda\envs\maestro\python.exe` (Python 3.11.16). 0 provider calls, purchased
assays, paid USD or assay waiting time. Input construction shares this run timing;
per-campaign deployment timing was not separately measured. Public retrieval
receipts total 4,365,188 payload bytes; initial exploratory HTTP requests are not
fully metered, so this is a recorded lower bound for the session. One-time projection
construction requires no paid model; upstream database curation/training sunk costs
are unknown. Local retained predictions occupy 281,300,304 bytes and scores 2,886,188
bytes. Network waiting, failed HTTP requests and full session CPU are not included
in the evaluation timing. Failure/attempt records are in RETRIEVAL and DEVIATIONS.

From the repository root, using the maestro interpreter:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' research/presage_transfer_20261016/verify.py
& 'D:\anaconda\envs\maestro\python.exe' research/presage_transfer_20261016/evaluate.py
& 'D:\anaconda\envs\maestro\python.exe' research/presage_transfer_20261016/audit_loop.py
& 'D:\anaconda\envs\maestro\python.exe' -m pytest research/presage_transfer_20261016/test_science.py -q
```

The verifier authenticates frozen inputs/splits/artifacts, reconstructs real-data
scores and every ranking, replays clustered intervals and the gate. Scientific
checks cover held-out outcome isolation, training-only feature scaling,
correspondence-breaking permutations, consumed missing nominations and clustering.
The full default software suite passes. Software success does not change NO-GO.

**Retain:** audit, negative result, source/split receipts, conventional neighbour
alternative, evidence and world-model boundaries, and tested runtime guards.
**Stop:** expansion of this pathway adapter, hard reliability gating, P1–P3, Agent
proposal/search and sealed confirmation for this failed method. Do not promote
research model code into src. The two system cores remain intact.

**Single highest-value next experiment:** independently evaluate whether one cheap
viability anchor improves nominations over ungated chemistry/target-MoA transfer,
with the anchor disjoint from terminal repeat measurements, at matched total assay
slots and on new connectivity groups. Compare fixed sparse placement against a
deterministic adaptive placement; predeclare meaningful yield gain and costs before
unsealing. Begin with the conventional predictor retained here; no new biological
source, LLM or memory is justified. This tests the lower-burden measured-anchor
alternative, not a continuation or confirmation of the failed pathway method.
