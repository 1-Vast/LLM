# Independent review of sciplex_pilot_v1

Date: 2026-09-29. Scope: read-only inspection of sources, construction code, produced arrays,
metadata and QA. Only this review document was added; the pilot, scripts and original reports
were not rebuilt or changed.

## Verdict

The acquisition is real and the source checksums match. The claim that construction is complete
and scientifically validated by 10/10 QA is not supported. Keep this version as a development
artifact under review; do not consume it as a matched-control rescue benchmark, validated HGNC
alignment, probability-calibration dataset or failure-modeling dataset.

## Confirmed positives

- Both h5ad files match their recorded byte sizes, MD5 and SHA-256.
- Produced means/effects have the reported dimensions: sciPlex2 (33, 58347), sciPlex4 (207, 58347).
- Source gene names and Ensembl ID axes match between the two studies. No actual cross-file
  feature-axis misalignment was found.
- The numeric arrays are finite; raw feature columns have not been silently removed.
- No output row claims qualified experimental evidence. No outcome labels were fabricated.
- The pilot is explicitly development-only. Missing biological replication and unverified dose
  units are disclosed, although other handoff claims overstate what was constructed.

## P1: cross-plate control mismatch

`build_sciplex_pilot.py:201` constructs the sciPlex4 control key from cell identity only.
The protocol requires matching cell and plate. Actual DMSO/DMSO controls occur only in A549
plate10 (1022 cells) and MCF7 plate5 (1544 cells). Of the 204 treatment conditions, **144 use a
different plate's control**, involving 65061 cells (72 conditions in each cell line).

The corresponding deltas can contain plate effects. They must not be described as plate-matched
treatment effects. A missing within-plate control should block that contrast unless a separate,
justified bridge/adjustment is declared and evaluated; silently relaxing matching is not a fix.
Retain plate/well membership and the exact control identifiers in the contrast provenance.

## P1: unknown identity is manufactured into a qualified condition

`build_sciplex_pilot.py:80` converts missing values to strings before identity validation.
Forty sciPlex4 cells lack treatment, dose, cell, plate and well metadata. They become
`nan::nan|nan::nan|nan`, the 207th grouped record, with `qualified` status, one purported well
and a chemical-rescue tag. All 240 output rows receive `qualified` merely because their groups
contain cells (`:265`). Nonempty cell groups do not demonstrate experimental quality.

Unknown identities require an explicit unresolved/quarantine record. They are not a zero-response
condition, an observed failed experiment, a known well or a rescue case.

## P1: treatment/control and rescue semantics are wrong

`build_sciplex_pilot.py:255` determines treatment type from the first intervention alone.
**28 conditions** with first intervention control and second intervention Abexinostat/Pracinostat
are mislabeled vehicle controls and assigned the control evidence class.

At `:286`, a nonempty second-treatment field is enough to tag rescue. Of **177 rescue-tagged
rows**, 80 have second treatment control and one is the unknown-identity group. Further,
the script computes only treatment/combination minus DMSO/DMSO (`:217`); it does not construct
the protocol's combination-minus-single-treatment rescue contrasts.

Classify both interventions and their doses before determining the action type. Distinguish a
rescue experimental design from an observed rescue effect. Deliver qualified single-agent and
combination contrasts separately, and do not claim rescue where required references are absent.

## P1: QA counts only positive effects while claiming absolute effects

At `qa_sciplex_pilot.py:99` and `:113`, the expressions are:

```python
np.abs(effect > threshold).sum()
```

The absolute value is applied to a Boolean comparison. The result counts `effect > threshold`,
not `abs(effect) > threshold`; negative responses are entirely omitted. Recomputing directly from
the delivered arrays gives the following counts at threshold 0.1, ordered by dose tokens
0, 0.1, 0.5, 1, 5, 10, 50, 100:

| Agent | Correct absolute-effect counts |
|---|---|
| BMS | 0, 164, 1476, 2776, 3475, 3441, 2745, 3648 |
| Dex | 0, 450, 747, 751, 732, 809, 715, 724 |
| Nutlin | 0, 29, 155, 347, 1253, 1476, 1753, 4042 |
| SAHA | 0, 921, 2459, 3477, 3839, 3821, 3969, 3791 |

SAHA's maximum absolute count above 0.25 is **1264**, not 773. Nutlin has the greatest maximum
count above 0.1 in this table, not SAHA. Dex is not monotonically increasing. The existing check
only compares the highest dose with the lowest nonzero dose; it is not a monotonicity test.
BMS's reported mid-dose peak was based on positive responses only, so it cannot substantiate the
stated biphasic total-response interpretation.

These are threshold counts of feature rows, not independently replicated differential-expression
discoveries. Even the corrected counts do not validate biological efficacy or mechanism. The
absolute-count comparison still passes 4/4 under the weak top-versus-low rule; that does not
rescue the incorrect statistic or narrative.

## P1: gene mapping is ambiguous and not delivered as a usable artifact

Both h5ad files already contain `var.ensembl_id`: 58347 rows and 58302 distinct Ensembl IDs.
The mapping function ignores this identifier. At `build_sciplex_pilot.py:104`, `alias.setdefault`
silently chooses the first target for a multi-target alias.

Independent checks against the same local HGNC file found:

- 137 input rows have multi-candidate base-name aliases.
- 75 selected mappings conflict with the Ensembl-to-HGNC correspondence.
- Example: MUM1 / ENSG00000160953 is assigned IRF4 by the symbol logic, while the stable ID
  corresponds to PWWP3A in the local HGNC table.
- 37537 mapped rows refer to only 36813 distinct approved symbols: 306 collision groups,
  involving 1030 rows and 724 additional rows beyond unique targets.
- 268 collision groups include different Ensembl IDs. Removing `:N` does not prove that these
  columns are biological duplicates. Only 38 collision groups contain one shared Ensembl ID.
- Of 20810 symbol-unmapped rows, 5067 have candidates through existing Ensembl IDs in the local
  HGNC file: **5066 unique and one ambiguous**. AC000061.1 / ENSG00000083622, for example, maps
  to CFTR-AS2. Describing the entire accession-like tail as inherently unresolvable is incorrect.

The mapping object is computed at `:275` but never serialized or applied. The gene file retains
original symbols and the arrays remain on the original feature axis. Therefore the current
matrices have not been damaged by a mapping merge; the failure is an untrustworthy and incomplete
mapping deliverable, not demonstrated corruption of expression values.

Required artifact: original feature index/name, source Ensembl ID, HGNC ID/symbol, candidate set,
mapping method, ambiguity/conflict/collision status, and mapping-resource checksum. Resolve
stable-ID conflicts explicitly. Do not automatically sum all columns sharing a stripped name.

The mutually exclusive current lookup accounting is:

| Lookup category | Rows |
|---|---:|
| Original approved symbol | 35071 |
| Alias without suffix removal | 1874 |
| Suffix removal then approved symbol | 406 |
| Suffix removal then alias | 186 |
| Total reported mapped | 37537 |
| Unmapped | 20810 |

The manifest's alias count 2060 overlaps suffix count 592 in 186 rows. Its field name
`resolved_via_alias_or_suffix` is misleading: the union is 2466. Counts describe lookup results,
not independently confirmed biological identity.

## P2: missing effects and completeness checks are misrepresented

The zero-initialized effects array contains four rows marked `effect_available=False`:
sciPlex2 `control::nan`; sciPlex4 A549 and MCF7 DMSO/DMSO baselines; and the unknown-identity group.
The handoff describes the three sciPlex4 rows as treatment conditions missing their controls.
In reality, two are the controls themselves and one has unknown identity.

The mask exists, so missingness is not entirely hidden, but the standalone arrays encode all these
different situations as zero. Distinguish a defined self-contrast baseline from an unavailable
contrast, and enforce availability in both validation and plotting.

At `build_sciplex_pilot.py:231`, the claimed sample-sheet comparison only counts lines: there is
no condition join, set difference or missing-condition record. Independent source inspection found
all 206 identifiable sciPlex4 sheet conditions represented this time; the builder nevertheless
cannot detect a future missing combination and must not claim that it performed that check.

## P2: QA is not an acceptance gate

- Failed checks are printed but `main()` returns normally; the script does not fail its process
  when checks fail.
- Shape checks compare means against the manifest but do not verify effect shapes and axis
  identity as claimed.
- Control zero checks cover only one sciPlex2 control row, not the sciPlex4 classification or
  plate matching.
- Provenance checks verify column presence, not field validity, identity or control linkage.
- The median-zero assertion is weak: 56.66% of sciPlex2 and 61.20% of sciPlex4 effect entries are
  zero; 15759 and 17420 features respectively are never detected. The inspected histograms are
  dominated by zero entries. This does not establish correct normalization or biology.
- No targeted tests referencing either new pilot script were found under `tests/`. Broad shape
  and tool tests cannot substitute for regression tests on these data-construction failures.

Keep scientific plausibility plots descriptive. Biology is not universally monotonic with dose,
and a hand-chosen broad-effect threshold should not certify dataset correctness. Add focused
checks for actual contracts and make structural failures produce a nonzero process exit.

## P2: incomplete and inaccurate handoff

- sciPlex2 in the actual file contains A549 only; the handoff incorrectly says A549/MCF7/K562.
  There is no actual cross-cell aggregation defect in this particular sciPlex2 input, although
  the builder's condition key omits cell identity.
- `CONTRACT_MAPPING_V1.md`, explicitly required by the construction protocol, does not exist.
- No rescue-specific contrast product, row-level gene mapping or complete member-level control
  provenance is delivered.
- The current mean is a cell-weighted mean of log-normalized expression, not a count-summed
  biological-replicate pseudobulk. That descriptive estimand can be retained if named accurately;
  it does not yield replicate uncertainty and weights wells according to recovered cell counts.
- All observation statuses are qualified. There is no attempted-experiment denominator or
  `undetected` subset supporting the suggested failure-modeling use. Zero recovered cells would
  not by itself prove biological non-detection in any case.
- Hash binding is incomplete for the sample sheets, HGNC resource, protocol, builder and outputs.
  A dated prose claim alone does not let this review independently establish preregistration time.

## Recommended repair order and acceptance

1. Preserve v1 and mark it not accepted for downstream scientific use. Repair in a new version.
2. Quarantine unknown treatment/context rows and classify the complete two-intervention action.
3. Enforce declared cell/plate control matching; report unavailable contrasts rather than silently
   relaxing matching. Build rescue contrasts only where references support them.
4. Emit stable-ID-first mapping with conflicts, ambiguities and collisions; bind the HGNC version.
5. Implement actual sample-sheet reconciliation and source-to-contract mapping, including outcome
   visibility and sampling-frame limits.
6. Correct QA arithmetic, enforce nonzero exit on failures, and add small adversarial regression
   checks for these failures. Recompute figures using valid contrasts and retain negative effects.
7. Rebuild, verify inputs/outputs and lineage, then rewrite handoff counts and permitted claims
   from the actual artifacts. Keep task A/B descriptive and development-only unless further data
   establish stronger scientific eligibility.

Do not repair this by lowering QA thresholds, asserting biological stories from a plotted pattern,
or changing the historical frozen evaluation. The raw source files can be reused; another large
download is not required to resolve most of these issues.
