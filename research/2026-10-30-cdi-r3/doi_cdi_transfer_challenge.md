# Independent challenge: DOI 10.64898/2026.08.04.742916 and the CDI proposal

Date: 2026-10-30 (Asia/Shanghai)

## Scope and evidence boundary

This is an independent mechanism and identifiability challenge. I used the DOI
metadata and abstract in the saved bioRxiv API record
(`research/2026-10-30-drug-discovery-capability/sources/root13_self_audit_api.body`)
and the CDI data-contract context in this workspace. I did **not** read the
paper's full text, supplementary data, code, or results tables. Statements about
the DOI paper below are therefore abstract-level claims or explicit inferences,
not a full-paper review. I did not run an experiment and did not modify
`src/` or `tools/`.

## Does the DOI paper already cover the proposed core?

The abstract reports three components:

1. **PACE**, a phenotype verifier that reduces immune ageing to ten scored,
   cell-type-resolved gene-set modules, selected for cross-cohort stability and
   evaluated in an in-house cohort of 434 elderly donors.
2. **CellQ**, a multi-modal-LLM virtual-cell verifier that compresses single-cell
   transcriptomes into eight discrete tokens and is claimed to predict
   perturbations and weak module shifts.
3. **Analyzer--Planner--Auditor**, which screened 110 compounds in primary human
   PBMCs, changed an ageing-module objective from an equal-weight mean to a
   balance-constrained minimum, and is claimed to generalize that self-correction
   to an independent 13-compound T-cell assay.

This is a meaningful overlap at the **workflow** level: a virtual-cell model,
an agent that chooses or evaluates objectives, and an experimental check. It does
not, on abstract evidence, cover the CDI scientific object:

| CDI requirement | What the DOI abstract says | Challenge judgement |
|---|---|---|
| Same-target A/B compounds with a calibrated molecular difference `Δa` | No same-target paired-compound or affinity contrast is stated | Not covered in the abstract |
| Transfer of `Δa` into a cell-background/function contrast | CellQ predicts perturbation expression/module shifts; no `Δa → Δy` estimand is stated | Related prediction task, different mechanism |
| Cellular target engagement, genetic perturbation, or rescue | None is stated | A phenotype verifier is not a target counterfactual |
| Separation of structural, target-insufficient, exposure/pharmacology, and assay-error explanations | The abstract says the agent audits its scoring objective | Objective self-correction is not failure-mode identification |
| Agent selection by equal-cost expected separation of competing models | Analyzer--Planner--Auditor is described, but the selection objective, costs, and comparator are not given | Cannot infer model-discrimination acquisition |
| Independent functional validation | The abstract claims an independent 13-compound T-cell assay | Potentially relevant validation, but endpoint, pairing, allocation, and independence details are unknown |

Thus the paper could already contain a strong **self-auditing phenotype-discovery
system**, but it does not establish that it has solved the narrower CDI problem.
The two ideas should be treated as partially overlapping, not as proof that CDI
is novel or that it is already covered. Full-text inspection would be needed to
test whether hidden supplementary details close any of these gaps.

The abstract's phrase “state-of-the-art perturbation prediction” and the two
compound counts are reported claims by the authors. They are not independent
evidence of causal target mediation, cellular engagement, prospective savings,
or a virtual-cell mechanism for molecular affinity differences.

## Strongest simple replacement mechanism

Retain one falsifiable mechanism and remove the larger stack:

> **Target-contrast gate.** For a same-target pair `(A,B)`, a virtual cell
> predicts the replicate-level functional contrast
> `r_c = y(A,c) - y(B,c)` from measured absolute affinities (or a pre-specified
> occupancy transform), dose, intracellular exposure, and cell state. A
> target-mediated component must (i) predict the direction and magnitude of
> `r_c` across held-out contexts and (ii) attenuate under target knockout or
> pharmacologic target blockade and return under rescue. Exposure-matched and
> plate/day-balanced controls test whether the same contrast is instead caused
> by pharmacology or assay error.

The cross-context contrast

```text
D = r_c1 - r_c2
```

is an interaction estimand. It is not automatically a causal difference-in-
differences: the causal interpretation comes from the intervention and blocked
controls. The virtual cell can be an ordinary hierarchical model with a
measurement-error term. A large multi-modal LLM is optional and should not be
part of the scientific claim.

The Agent has a single narrow role. After an initial balanced block, it chooses
the next allowed action from a frozen menu (pair, cell context, dose, and one
control arm) that maximizes expected posterior separation between only two
pre-registered worlds:

- `H_T`: the contrast contains a target-mediated occupancy component that changes
  under target intervention and is restored by rescue;
- `H_N`: the apparent contrast is explained by exposure/off-target biology or
  assay/batch effects and does not show that intervention pattern.

Expected separation is evaluated at equal total cost, including controls and
failed assays. Compare this selector with random selection, an ordinary
hierarchical model with standard value-of-information (VOI), and a fixed
balanced design. The contribution, if any, is the intervention-gated
identification rule and its stop condition; it is not an LLM architecture or an
agent name.

This replacement is stronger because it has a direct counterexample. If a
non-target exposure artifact produces the same distribution before and after
the target intervention, the mechanism is not identifiable and must return
`inconclusive`; no amount of virtual-cell scaling can turn that observation into
target mediation.

## Minimum data contract

Freeze and hash these tables before agent selection. Missing fields are masks
that invalidate the corresponding claim; they are not imputed as evidence.

**Drug and target.** Canonical structure (including stereochemistry and salt
policy), stable drug and target IDs, pair ID, absolute `a_A` and `a_B`, `Δa`,
measurement or prediction source, uncertainty, assay construct/temperature/
ligand state, concentration, selectivity/off-target panel, stability, and lot.
Relative affinity alone is not enough when absolute occupancy, efficacy, or
kinetics can differ.

**Cell context.** Stable cell ID, target abundance and alteration state,
relevant pathway and transporter variables, growth/media state, passage and lot,
and whether the sample is parental, target-perturbed, or rescue. Context labels
must be measured before the response is revealed.

**Intervention and exposure.** Knockout/knockdown or a justified target-blocking
arm, rescue construct, target-engagement measurement, intracellular free
concentration or a validated matched-exposure control, dose, time, vehicle,
uptake/efflux metadata, and intervention fidelity. A baseline expression value
is not a target counterfactual.

**Assay record.** Raw replicate-level endpoint `y`, units and pre-registered
transform (viability, log viability, growth rate, or Emax), dose/time, plate,
day, operator, reagent lot, well position, randomization/block, censoring, QC,
and failed wells. Preserve the raw endpoint and a replicate-level error model.

**Selection and provenance.** Candidate pool, frozen model/feature versions,
priors, action costs, expected information, selected action, remaining budget,
and an assertion that no outcome from the selected action was visible at choice
time. Keep target-level, scaffold-level, cell-level, and assay-day split labels,
plus hashes for every input snapshot.

At least three measured cell contexts are needed to claim a transferable context
rule. Two contexts can define one planned contrast, but cannot validate a virtual
cell moderator. Every A/B pair must be run together in the same blocked assay,
with independent assay days. Public joins that lack exact pair identity,
exposure, intervention, and replicate provenance may support a predictive
association, but not the target-gated mechanism.

### Cheap-public-data boundary

The low-cost first pass can be a masked replay on a public matrix: hide selected
drug-by-cell responses, let the Agent choose from the remaining candidate pool,
and score held-out responses at equal row/plate cost. This can test leakage,
split discipline, and whether a selector beats random or ordinary VOI. It is a
retrospective prediction test. It cannot establish `H_T` unless the same mapped
drug pair, cell context, exposure/time, and endpoint also have a linked
target-engagement or genetic perturbation/rescue observation with independent
replicate provenance. Name joins across PRISM, affinity, DepMap, or transcript
resources are not a substitute for that contract. If no public resource passes
this exact-match gate, stop at the masked replay and report the mechanism as
untestable with public data.

## Minimal discriminating experiment

The smallest study that could falsify `H_T` without pretending that one
expression panel is a mechanism is:

1. Fix one target for which a validated perturbation/rescue or cellular-
   engagement assay is available. Select two same-target A/B pairs: one with a
   sizeable, calibrated `Δa` and one near-null pair. Freeze the pairs before
   looking at functional outcomes.
2. Use three cell contexts spanning target abundance or relevant background.
   Run parental and target-perturbed material, with rescue where feasible. If
   rescue is impossible, label the result a weakened counterfactual rather than
   a positive mechanism test.
3. Measure both compounds at the same nominal dose and time, with intracellular
   exposure or a matched-exposure control, on randomized plates across at least
   three assay days. Collect a target-engagement or orthogonal endpoint in the
   same experiment.
4. Reveal one initial balanced block to all selectors. Let the Agent choose a
   small number of remaining pair-by-context-by-control actions under the frozen
   equal-cost ledger. Keep random, fixed-balanced, and ordinary hierarchical
   VOI selectors on the same candidate pool and budget.
5. Evaluate the pre-registered target-gating statistic on held-out assay days
   and at least one held-out context. The primary result is the difference in
   target-sensitive contrast between `H_T` and `H_N`, not a generic response
   prediction score.

The decisive pattern is: the affinity/occupancy ordering is reproducible in
parental cells, is selectively reduced by target perturbation, and is restored
by rescue while exposure and assay controls remain balanced. A large response
that persists after target perturbation, disappears after exposure matching, or
changes with plate/day is evidence for `H_N` or for a mixed mechanism. A failure
to separate the worlds is `inconclusive`, not a negative biological result.

## Stop conditions

Stop the CDI line, without adding model modules, if any of the following occurs:

- exact structures, target identity, intervention status, exposure, or replicate
  provenance cannot be audited before selection;
- no target perturbation/rescue or orthogonal engagement measurement is feasible;
- the A/B contrast is not reproducible under the pre-registered endpoint scale,
  or its sign depends on a post hoc transform;
- target perturbation does not selectively alter the proposed component and
  exposure/off-target controls cannot distinguish the alternatives;
- the relation fails on held-out contexts, target-level/scaffold-level splits,
  or independent assay days;
- `H_T` and `H_N` remain observationally equivalent for every affordable
  action, with expected separation below the pre-registered assay-noise/cost
  floor;
- the Agent has no out-of-sample model-separation or attribution gain over
  random, fixed-balanced, and ordinary hierarchical/standard-VOI controls at
  equal total cost;
- the apparent advantage is explained by leakage, post-selection, or a cheap
  predictive baseline using the same information.

If any stop condition is met, retain the result as a boundary on what the public
data can identify. Do not reinterpret a missing engagement or intervention
measurement as support for a virtual-cell mechanism.

## Independent conclusion

On the abstract alone, DOI 10.64898/2026.08.04.742916 **partially overlaps**
with CDI's agent-plus-virtual-cell workflow but does **not establish coverage of
the core same-target `Δa → Δy` mechanism**. The strongest simple alternative is
an intervention-gated target-contrast study with a two-world Agent objective and
a hard non-identifiability stop. It is worth pursuing only if the exact
drug/pair, exposure, perturbation, engagement, and replicate contract can be
met. Otherwise the scientifically honest output is a standard conditional
regression/active-learning proposal with no claim of causal mechanism,
prospective savings, or novelty.

### Evidence pointer

- You et al., “Virtual-cell verification enables self-auditing AI discovery for
  immune rejuvenation,” bioRxiv preprint, DOI
  [10.64898/2026.08.04.742916](https://doi.org/10.64898/2026.08.04.742916),
  abstract version dated 2026-08-11. Local abstract record:
  `research/2026-10-30-drug-discovery-capability/sources/root13_self_audit_api.body`.
