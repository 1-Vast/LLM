# Exact-dose data qualification

This packet supports an **exposed retrospective algorithm diagnostic**, not an
independent biological confirmation. It rebuilds the matrix from the publisher's
PRISM primary response file. It does not use any previously averaged, mixed-dose
derived matrix.

Run from the repository root:

```powershell
python research/context_probe_20261011/data/prepare.py
```

`output.npz` is ignored by Git and is reproducible from the local sources listed
with SHA-256 hashes in `MANIFEST.json`. Load it with `numpy.load(...,
allow_pickle=False)`. Its complete array contract is in the manifest. The
evaluator owns `y` and `available`: code that fits a model or selects probes must
receive only reference outcomes, plus the explicitly purchased target entries.
The preparation step itself is not an access-control boundary.

## Qualification results

| Item | Count |
|---|---:|
| PRISM primary response rows | 578 |
| Matched contexts with identity metadata and basal input | 561 |
| Reference / development / evaluation contexts | 356 / 99 / 106 |
| Exactly 2.5 uM, HTS treatment columns | 3,939 |
| Metadata identity components | 3,860 |
| Eligible components after reference-only completeness filter | 3,621 |
| Untransformed basal source columns | 19,144 |
| Missing basal values in retained contexts | 0 |
| Reproduced old mixed-dose compound groups | 36 |

The 17 exclusions comprise 10 failed-STR identities and 7 contexts without a
basal-expression input; their identities and reasons are in
`excluded_contexts.json`. Context eligibility uses identity/STR
metadata and prefeedback basal input availability. It never uses target response
magnitudes or response completeness.

The nominal split is 60% reference, 20% development and 20% evaluation by fixed
SHA-256 thresholds. The realized counts need not equal those fractions exactly.
The hash uses the documented RRID when available and the DepMap ID otherwise.
If multiple eligible contexts share an RRID, only the lexicographically first
DepMap ID is retained; none of the qualified 561 rows required this removal.
The split is constructed before response values are loaded. Lineages overlap
across roles; `MANIFEST.json` records the entire lineage-by-role count table.
This is a new-response-context task, not lineage-held-out or unseen-drug testing.
There is no separate policy-calibration set and no coverage guarantee in this
initial information diagnostic.

## Exact conditions and identity

Only treatments satisfying numeric `dose == 2.5` and `screen_id == "HTS"` enter
the new library. No tolerance accepts nearby doses. All 3,939 qualified columns
exist in the raw response header. No dose averaging occurs.

Treatment aliases form metadata-only connected components when they share a
Broad compound prefix or a NFKC/casefold/whitespace-normalized name. A component
uses its lexicographically first qualified treatment column as the sole outcome
source. This rule is independent of outcomes and missingness. Other batch/alias
columns are never averaged, used to fill missing responses, or separately
eligible for a probe or terminal decision.

`drug_groups.json` records every alias, Broad prefix, representative column,
source-column set, reference completeness and eligibility decision. There are
76 multi-column components, 11 components spanning multiple Broad prefixes,
and 82 components containing multiple distinct metadata SMILES strings.
Those strings sometimes contain repeated or conflicting structures. They were
not chemically canonicalized and are not used as model inputs or as a basis for
merging additional components. The component rule conservatively blocks aliases
but does not prove pharmaceutical equivalence. A later chemistry study needs
independent identity resolution.

The endpoint is publisher-normalized log2-fold-change relative to negative
controls from a pooled, barcoded-cell PRISM assay. Lower values indicate lower
relative viability. It is not absolute cell death, apoptosis, or a mechanism
measurement. The local collapsed metadata do not provide per-treatment exposure
times, culture/day identifiers or plate-level repeated measurements. Therefore
the exact dose and screen are verified, but per-sample time consistency and
independent culture replication are not established here.

The publisher already applied control normalization, QC, ComBat and median
replicate collapse, as described in the hashed primary README. That processing
may share information across plates/pools/contexts. This packet does not
reconstruct raw culture-level preprocessing. Subsequent modeling can enforce a
strict reference/target response boundary **after that supplied processing**;
it cannot claim a completely isolated raw-assay preprocessing pipeline.

## Missingness and legal use

Each drug representative must have at least 95% finite outcomes among the fixed
reference contexts. This threshold is fixed before model execution. Target
values and target missingness do not determine drug eligibility. All reference
contexts remain included, even those with sparse responses.

| Role | Observed eligible outcomes | Missing | Minimum per-context observed fraction |
|---|---:|---:|---:|
| Reference | 1,259,829 | 29,247 | 0.08423 |
| Development | 353,690 | 4,789 | 0.39823 |
| Evaluation | 378,751 | 5,075 | 0.65258 |

The low minimum fractions reflect structured missingness despite high overall
availability. No eligible drug is observed in every reference context. Training
must respect the reference observation mask; filling a missing training label
and treating it as a measured response would be an additional modeling
assumption. Any fitted imputation, scaling, feature selection or response
factorization must use reference inputs/outcomes only.

The `available` mask is evaluator bookkeeping. A missing purchased probe is a
failed/unavailable measurement with its declared cost treatment. A missing
response for a committed terminal selection remains unscorable; it must not
cause silent replacement, shrinking top-k or filtering that context. Report
scoring availability per arm and the paired evaluable population, because even
outcome-value-blind availability can be selection-dependent. Complete-case
results cannot alone establish a whole-library benefit.

`context_missingness.csv` audits all eligible drugs per context. The manifest
also audits missingness before the reference-only drug filter. None of these
target audits is a permissible input for probe selection or model fitting.

## Previous dose mixing

`old_mixed_dose_groups.json` reproduces all 36 mixed-dose groups in the earlier
1,403-compound split using its original treatment-column lists. For example,
AZD7762 contains 2.5 and 2.52 uM, while GDC-0879 contains 2.38 and 2.5 uM. The
legacy split is used only for this audit and contributes no outcomes, features,
roles or candidate eligibility to the new dataset.

The source data have already been available to previous repository work. A new
hash split makes the diagnostic reproducible and prevents new model leakage;
it does not restore a previously unobserved scientific holdout.
