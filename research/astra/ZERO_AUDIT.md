# EGR1 zero, abstention and paired-action audit

This follow-up separates computational stability, meaningful action advantage and
actual experimental benefit. It implements the October 2 supplied review without
changing the original EGR1 score, numerical tie tolerance, checkpoint, query count,
action menu or seeds. New evidence stays in ASTRA; no production/tool policy is promoted.

## Scope and frozen semantics

The inputs are the already inspected nine requests in
[`20261002_paired_matrix_v1`](results/20261002_paired_matrix_v1/summary.json): three
historical NCI-H596 control pools, seeds17/42/103, and Trametinib0.05/0.5/5uM.
Each pool contains30 historical assay-endpoint control cells. Each action gets16
prediction slots with the same actual sampled basal tensor within a request.
The model is `state_generalization_zeroshot_X_hvg`; checkpoint SHA256 is
`2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3`.

These controls are not authenticated prospective RNA. Independent cultures,
checkpoint training exposure and actual costs remain unknown. A same integer seed
across pools uses different native cells; within-request output positions are
positions of a set-to-set model, not authenticated before/after cell trajectories.
The other31 ambiguous axis coordinates and new-RNA precision certification failure
remain unresolved.

The independent chunked identity check in
[`20261002_egr1_identity`](results/20261002_egr1_identity/receipt.json) verifies
all30,394 c39 rows: named EGR1 is column5090 in normalized `X`, and column546 in
`X_hvg`; log1p correspondence has maximum absolute difference2.384185791e-7,
with0 rows exceeding the original1e-5 tolerance. There are4,969 nonzero values,
so this is not an all-zero mapping coincidence. Source and installed inference
hashes match before/after. This certifies this local gene identity only; normalized
`X` must not be called raw UMI.

The exact original score is negative native float32 mean predicted log1p EGR1 at
coordinate546. A top gap at most1e-6 triggers the original numerical refusal.
This tolerance is not a scientifically meaningful utility difference. No such
meaningful delta is invented, and no validated biological or MC interval is fitted.

The aggregation estimand is the uniform mean of this linear score over the frozen
basal-resampling mechanism, conditional on the checkpoint and historical pool.
It is not the distribution of future experimental outcomes. Linear scoring makes
score-first and mean-first agree apart from documented floating-point reductions;
that property cannot be assumed for nonlinear utility: U(E[Y]) need not equal E[U(Y)].

## Verified saved-output findings

All original cell manifests,96 matrix manifest entries and saved request arrays
match their hashes. Returned output is `obsm["X_hvg"]`, not `X`.
The27 action means contain18 exact zeros; every one has16/16 exact-zero EGR1
outputs. There is no signed cancellation, display rounding, missing-value imputation
or final utility discretization behind these zeros. Full precision vectors, float
hex strings, array hashes and both native and float64 means are preserved in
[`readout_audit.json`](results/20261002_zero_audit_v1/readout_audit.json).

Seven original requests refuse because the best scores are exactly equal, gap0:

| Pool | Seed | Numerically tied best doses, uM | Original selection |
|---|---:|---|---|
| plate1 |17|0.5,5|Refuse|
| plate1 |42|None|5|
| plate1 |103|0.5,5|Refuse|
| plate10 |17|0.05,0.5|Refuse|
| plate10 |42|0.5,5|Refuse|
| plate10 |103|0.5,5|Refuse|
| plate11 |17|None|5|
| plate11 |42|0.05,0.5,5|Refuse|
| plate11 |103|0.05,0.5,5|Refuse|

These are numerical top ties, not uncertainty-interval refusals. The original
30-cell baseline, actual16 sampled inputs and separately predicted controls are
saved in the readout audit. Returned controls use their own sampling and are not
paired control responses. Treatment-minus-input values are retained only as
computational-position diagnostics; their set-mean differences are also predictions,
not measured treatment effects. Control subtraction with a common scalar could not
by itself remove the exact ties.

## Native activation observation

[`zero_audit.py`](zero_audit.py) installs a read-only forward hook on the actual
model's final `relu` during the frozen paired worker. It records the pre/post EGR1
vectors and full activation/output hashes, never returns replacement tensors, and
restores both class and module hooks, including on failure. The paired worker
retains its original action encoding and homogeneous per-action forward loop.

The observation plan is frozen before new forwards in
[`freeze.json`](results/20261002_zero_audit_v1/freeze.json): the same nine requests,
36 forwards including model controls, no new seeds and no adaptive stopping.
The prior output matrix was already inspected: this is an attribution audit, not
a newly blinded biological test. Each replay checks full78x2000 returned matrices
by shape, dtype and array-byte SHA, plus output identities; EGR1 export must equal
the observed native `preds` exactly.

Installed `state_transition.py` calculates the projection and then applies the
main ReLU before returning `preds`. The official inference exporter also applies
gene-space clipping to[0,14]. The explicit native/export comparison distinguishes
those stages, rather than attributing zeros from code presence alone. Negative
pre-ReLU values are latent model values, not negative RNA measurements. They must
not replace the original output or become a new utility intended to break ties.

The completed observation count, zero attribution and elapsed time are authoritative
in [`receipt.json`](results/20261002_zero_audit_v1/receipt.json), with per-request
commands and results in [`replay_receipts.json`](results/20261002_zero_audit_v1/replay_receipts.json).

All nine replays complete successfully, executing36 new real STATE forwards in
297.90 seconds. All nine complete output matrices are bitwise equal to their
originals. All18 zero-mean actions have16 strictly negative pre-ReLU EGR1 values:
288/288 zeros are directly traced to the final ReLU. Native EGR1 and exported EGR1
are byte-identical, so the export clipping contributes no further change to this
readout. Frozen inputs and historical files remain unchanged. This authenticates
the numerical path; it does not validate EGR1 as the experimental objective.

## Plate10 contrasts and bounded policy diagnostics

| Seed | Low EGR1 | Middle EGR1 | High EGR1 |
|---|---:|---:|---:|
|17|0|0|0.030477266758680344|
|42|0.0033577606081962585|0|0|
|103|0.15558677911758423|0|0|
|Uniform mean|0.05298151324192683|0|0.010159088919560114|

With U=-EGR1, middle-minus-high differences are[0.030477266758680344,0,0].
Their mean is0.010159088919560114; descriptive sd/sqrt(3) is0.010159088919560116.
Middle-minus-low differences are[0,0.0033577606081962585,0.15558677911758423].
Their mean is0.05298151324192683; descriptive sd/sqrt(3) is0.05131178902271956.
These summarize conditional numerical sampling only. No normal interval, physical
confidence interval or practical equivalence claim is reported. Independence is a
sampling assumption, not certified by observing three seed values.

For every fixed pair, the audit verifies that uniform averaging cannot move an
all-seed difference bounded by1e-6 outside that bound. Plate10 is consistent:
each seed has a top tie, but the tied pair changes. Middle is zero for all seeds;
each alternative is positive for at least one seed. Its unique aggregate rank
does not establish an optimal biological dose or demonstrate an averaging defect.

[`policy_diagnostics.json`](results/20261002_zero_audit_v1/policy_diagnostics.json)
compares four explicit replay interpretations on the same menu and readout:

| Strategy | Plate10 output | Prospective model forwards | Actual utility |
|---|---|---:|---|
|Original single seed|Refuse for each of17/42/103|4 per request|Unknown|
|Fixed K=3 uniform aggregation|Middle dose as numerical rank|12|Unknown|
|Same-K contrasts and scientific candidate set|All three candidates; no certified recommendation|12|Unknown|
|Fixed low-dose comparator|Low dose|0|Unknown|

Aggregation and contrasts consume the same computation. Original K=1 and fixed
action have different computational costs, which are explicitly retained. The
entire matrix is reused; these diagnoses cause no physical action. We do not call
all four strategies compute-matched, or charge fictitious experiments/costs.
The fixed low dose is a comparator, not a claim that it is safe or best.

Aggregation changes refusal to a concrete output for each of the three Plate10
seed-indexed comparisons. Those comparisons reuse a common aggregate and are not
three independent decisions. There are zero original concrete-to-concrete switches
on Plate10. Refusal benefit/error cost and realized terminal benefit cannot be
scored without legitimate matched outcomes and refusal utilities. Historical
cross-pool four refusal changes remain just that; this audit does not relabel them
as improved treatments.

The full scientific candidate set is an unknown-advantage set, not an equivalence
set. Meaningful advantage/equivalence would require an independently defined delta,
validated outcome contrasts, the relevant dependence structure and appropriate
selection reliability. The existing pools cannot supply that evidence.

## Next budget and reproducibility

Current next step: validate EGR1 against a legitimate endpoint and obtain matched
measured action outcomes. More seeds can refine the conditional model mean, but
cannot repair an unidentified endpoint, model error, missing action measurements,
illegal decision-time availability or unknown costs. No request increases seeds
until a preferred dose wins. True state-conditioned policy work additionally needs
authenticated available-before-decision states and independent experimental units.

The statistical interface now emits actual action contrasts, candidate sets,
estimand, randomness source, paired-input status, descriptive MC precision, original
refusal reasons and uncovered uncertainty. It keeps biological advantage and
experimental benefit unknown separately. This research interface is not promoted
into a production selector without validation.

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py -m research.astra.zero_audit run --observe --out research/astra/results/NEW_ZERO_AUDIT_DIRECTORY
& $py -m research.astra.verify --out research/astra/results/NEW_SCOPED_VERIFICATION_DIRECTORY
```

Omit `--observe` for a saved-output-only audit. Use a new directory; frozen source
snapshots and hashes are preserved. Large ignored H5AD/NumPy assets must be restored
from the earlier pinned acquisition and paired-matrix commands. No external API was
needed; no physical experiment or STATE biological state-gain comparison ran.

The initial15 new contract tests pass. The scoped maestro regression passes332,
including133 ASTRA contracts, with0 failures/errors/skips; its source freeze and
historical integrity checks pass in
[`20261002_zero_audit_verification`](results/20261002_zero_audit_verification/receipt.json).
The earlier1,861-test full run remains a previous-round result; this research-only
follow-up does not claim to rerun it. Three-agent independent review checked the
statistical boundaries, mapping/source path and pairing/zero receipts.

Independent software review identified two failure-receipt issues after the
successful observation run: timeout partial logs were not persisted, and failed
validation could be described as a completed request. The execution snapshot and
successful v1 receipts remain frozen. The current driver now retains timeout logs
and separates started processes, completed subprocesses and validated observations;
two new failure fixtures verify this correction. Observation, inference and scoring
functions are unchanged. No additional model forward is needed for this receipt-only
repair; the final scoped verification is stored separately under
`results/20261002_zero_audit_verification_v2/`.
That final run passes334 tests, including135 ASTRA contracts, with0 failures,
errors or skips. AST comparisons certify that the observation, inference, saved
readout and scientific policy functions match the successful v1 execution snapshot.
After documentation/navigation updates,21 repository-shape checks also pass
(`docs_followup.xml`); these overlap the scoped run and are not added to its count.
Exact replay establishes repeatability for identical inputs, not that three-seed
means have reached adequate numerical precision or that state gains are identified.
