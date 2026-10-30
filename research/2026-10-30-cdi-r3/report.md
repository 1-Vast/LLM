# Cross-scale differential identification (CDI): evidence-grounded checkpoint

Date: 2026-10-30 (Asia/Shanghai)

## Executive finding

The seed idea can be reduced to a defensible scientific question, but the full
Agent × virtual-cell method is not established.  In a fixed retrospective FLT3
slice, an exact same-target relative-Kd feature added a small amount of held-out
prediction for PRISM viability, including a lineage holdout.  The context
contrast that would be central to CDI was nearly uncorrelated with relative Kd.
The data therefore support a conditional feasibility lead, not a target-mediated
mechanism, an Agent advantage, or a novel algorithm.

The surviving candidate is a **pre-registered matched structural-to-functional
diagnostic design**.  A virtual cell models the conditional relation between a
matched drug-pair contrast and cell response.  An Agent chooses the next
pair × context × control observation by expected separation of four competing
failure models, at equal cost, and stops when the models are observationally
equivalent.  This design is a hypothesis for a future intervention study; its
distinctiveness and decision value remain unverified.

## Question and closest-prior boundary

For two compounds A and B acting on the same target, let `Δa` be a relative
binding quantity measured under one comparable assay and let `y` be a
drug × cell × dose response.  The proposed functional contrast is

```text
D = [y(A,C1) - y(B,C1)] - [y(A,C2) - y(B,C2)]
```

`D` is an interaction estimand.  It is not automatically a causal difference in
differences.  A target-mediated claim would require an intervention or a
cellular engagement measurement that is absent from the public join used here.

The three user-supplied papers were read from their original publisher pages,
the author repository where available, and saved source text:

| Source | What was verified | What it does not provide for CDI |
|---|---|---|
| AdaMBind, *Nature Communications* 2026, DOI [10.1038/s41467-026-70554-5](https://doi.org/10.1038/s41467-026-70554-5) | Target-specific tasks, MAML adaptation, 5/40-shot support, adaptive task sampling, BindingDB/KIBA/Davis and an FLT3 enzyme example | No matched A/B cell-function contrast, cross-background `D`, exposure control, or mechanism-discrimination Agent |
| PBCNet2.0, *Nature Chemical Biology* 2026, DOI [10.1038/s41589-026-02241-x](https://doi.org/10.1038/s41589-026-02241-x) | Siamese relative-affinity prediction, 8.6 million complex pairs, local pocket changes, ENPP1/ALDH1B1 forward checks; author code and data pointers | No cell background, dose/time, viability endpoint, or equal-budget experimental selector; full split/ablation details remain access-limited |
| Robin, *Nature* 2026, DOI [10.1038/s41586-026-10652-y](https://doi.org/10.1038/s41586-026-10652-y) | Literature candidate generation, human-run experiments, Finch flow/RNA-seq analysis, consensus and follow-up | No `Δa → Δy` input, same-target A/B design, `D`, or explicit selection to discriminate structural, target, exposure and assay explanations |

These papers occupy few-shot affinity adaptation, relative molecular comparison,
and a lab-in-the-loop discovery loop separately.  Combining their names is not a
new contribution.  The fresh independent challenge (`fresh_challenge.md`)
classified the current CDI stack as ordinary interaction regression, model
discrimination/VOI, and few-shot adaptation, retaining only the controlled
diagnostic design as a conditional lead.

The cross-field transfer is therefore deliberately narrow.  Query-by-committee
and uncertainty sampling from computer vision/NLP, model-discrimination control
from robotics, and factorial interaction logic from causal inference all point
to choosing an observation that separates competing explanations at equal cost.
They do not supply a new biological object or a new architecture here.  The
transfer is retained as a design principle and an evidence standard, not as a
claimed module-level innovation.

## Data contract and identity audit

The audit used only public/local assets and did not read sealed or confirmation
responses.

* Klaeger 2017/ChEMBL (`data/external/klaeger2017_chembl`) contains 70,505 Kd
  activities across 243 molecules, 320 targets and 325 assays.  All values are
  nM Kd; 65,576 are right-censored (`>`), so the resource is suitable for a
  censored relative ranking feature, not a cellular engagement measurement.
* A single bounded ChEMBL REST request retrieved the 243 molecule records. 242
  contained a standard InChIKey.  The raw response and request budget are in
  `raw/chembl_molecules_batch.json` and `chembl_api_manifest.json`.
* PRISM 19Q4 supplies drug-batch × cell-line DMSO-relative log-fold viability,
  dose, screen and well/plate identifiers.  The secondary treatment table has
  1,507 broad IDs.  `MTS010` is documented as a technical redo of 147 oncology
  compounds.  Its column labels carry the raw token `120H`, but the README does
  not define a structured exposure-time or preparation field; the token is kept
  as a label rather than treated as an independently verified exposure record.
* DepMap 19Q4 supplies exact cell identity, lineage, baseline expression and
  mutation.  The local release has no CRISPR GeneEffect or paired target
  perturbation, so expression is a background covariate and not a genetic
  intervention.
* GDSC Jaaks 2022 and BeatAML2 remain possible external functional resources,
  but their endpoint, patient/cell-line and fitted/raw units cannot be merged
  into the PRISM label without a separate contract.  LINCS/MIX-seq are state
  proxies and were not substituted for viability.

The exact-structure census (`identity_census.json` and
`prism_structure_identity_candidates.csv`) found:

* 4,744 unique PRISM broad IDs in the supplied treatment files;
* 4,627 with one parsed structure, 115 with conflicting structures, and 2
  unparsed;
* 225 exact InChIKey matches to the ChEMBL records;
* 17 name-only candidates, which remain unconfirmed and were not used as exact
  mappings.

These counts establish identity candidates only.  They do not establish target
identity, cellular engagement, matched exposure, independent biological repeats,
or causal mediation.

## Minimal exploratory run in the `maestro` environment

The target was fixed to FLT3 (`CHEMBL1974`) before response inspection because
FLT3 is the explicit wet-lab example in AdaMBind.  This is a seed-driven pilot,
not an outcome-selected target choice.

The static target census found 53 structure-mapped molecules with an exact Kd,
66 PRISM broad IDs, and 1,378 exact-Kd molecule pairs.  Across all secondary
screens, 1,081 pair rows had at least three shared non-missing cell contexts.
For the fixed `MTS010` screen used in the response pilot, the analysis retained
153 pairs, 429 treatment columns, 469 cells from 21 lineages, and 487,364
pair × cell × nominal-dose observations.  Duplicate treatment columns were
averaged within molecule × dose × cell; their count is retained but is not a
biological replicate count.

For each exact-Kd pair, `pKd = -log10(Kd[nM])` and `delta_pKd` were computed within
the same ChEMBL target.  The response was the PRISM DMSO-relative log-fold
viability.  Baseline FLT3 expression from DepMap was split into three fixed
tertiles.  Two frozen ordinary models were compared with five-fold pair-grouped
cross-validation:

1. `context_only`: expression and log nominal dose;
2. `context_plus_relative_kd`: the same inputs plus `delta_pKd` and its
   expression interaction.

The primary execution used `conda run -n maestro` (Python 3.11).  An independent
file-level audit re-read the saved long table and context contrasts.  A second
lineage-grouped five-fold check tested transfer to held-out observed lineages.
No Agent selector was claimed from these retrospective labels.

### Observed values

| Check | Context-only | Context + relative Kd | Difference |
|---|---:|---:|---:|
| Pair-grouped RMSE | 0.703181 | 0.700920 | −0.002261 |
| Pair-grouped R² | −0.001397 | 0.005032 | +0.006429 |
| Pair-grouped Spearman | −0.012998 | 0.056749 | +0.069748 |
| Lineage-grouped RMSE | 0.702772 | 0.700309 | −0.002463 |
| Lineage-grouped R² | −0.000234 | 0.006764 | +0.006998 |
| Lineage-grouped Spearman | −0.006954 | 0.060438 | +0.067391 |

Across pair means, `delta_pKd` and mean `delta_y` had Spearman `rho = -0.3026`.
The key context contrast, high-expression minus low-expression `D`, had
`rho = 0.0601` with `delta_pKd` across 1,109 pair × dose contrasts.  The printed
p-values are descriptive calculations only; cell and pair dependence prevents
using them as independent biological inference.

A 20-seed pair-level permutation of `delta_pKd` gave a `maestro` null RMSE of
`0.703394 ± 0.000289` (range `0.702973–0.703891`) versus observed `0.700920`.
This negative control says that the particular retrospective pairing of Kd
contrasts contains some predictive information in this matrix.  It does not say
that Kd mediates viability or that an Agent saved experiments.

The response table and the context contrasts were byte-identical between the
Python 3.14 and `maestro` runs.  Small CV differences appeared between sklearn/
Python runtimes, so the `maestro` values above are the canonical execution
values and the runtime discrepancy is retained in `runtime_repro/comparison.json`.

## Interpretation and limits

The pilot is compatible with a weak, target-specific retrospective association
between molecular relative binding and overall drug-pair viability difference.
It does not show the CDI mechanism: the affinity contrast did not explain a
substantial expression-conditioned `D`, and the screen has no verified cellular
engagement or target perturbation.  A stronger chemical series, uptake,
residence-time, off-target, saturation, batch, or assay-scale explanation remains
possible.

The earlier 684-row transcriptome–PRISM bridge was rejected as a matched
proxy/function experiment because transcript rows were all `24 h | 10,000 nM`
while PRISM contained multi-dose pooled curves with missing preparation,
vehicle, exposure-time and independent-repeat matching.  The historical
kinobeads substitution experiment likewise found that a binding kernel did not
replace the functional reference (`contrast = -0.000059`, CI
`[-0.000115, -0.000010]`).  The present FLT3 result is therefore a narrow
predictive association and does not overturn those boundaries.

The full pair census was intentionally not promoted: the first implementation
would enumerate about 5.26 million affinity pairs and repeatedly scan the wide
response matrix, exceeded the practical runtime, and was stopped without a
result.  The targeted FLT3 census avoided that computational shortcut and is
the only response experiment reported here.

## Decision

* **Conditional GO:** one small, pre-registered falsification/identifiability
  study is justified if a target-specific intervention resource can be obtained.
* **NO-GO:** do not build the full CDI stack, add MAML/PBCNet modules, claim a
  virtual-cell mechanism, or promote code from this retrospective result.

The decisive next study must freeze two or three matched A/B pairs (including a
near-null pair when available), at least three measured cell contexts, blocked
replicates across independent assay days, matched dose and documented exposure,
and a target perturbation/rescue or cellular-engagement readout.  Freeze four
models before selection: structural/target-mediated (M1), target-insufficient
(M2), exposure/pharmacology (M3), and assay mismatch (M4).  Let the Agent choose
the next pair × context × control by expected posterior separation at equal cost,
and compare ordinary hierarchical regression, random selection and standard VOI.
Stop if the models remain observationally equivalent or if a simple hierarchical
model explains the data with no decision-separation gain.

No result from this round meets the independent-validation bar for `src/` or
`tools/`; neither directory was changed.

## Files and provenance

* `prior_verification.md` — original-paper method and closest-prior audit.
* `data_audit.md` — source contracts and measurement boundaries.
* `fresh_challenge.md` — fresh independent challenge of CDI.
* `identity_census.json`, `prism_structure_identity_candidates.csv` — exact
  structure mapping census.
* `flt3_pilot_census.json`, `flt3_response_pilot.json`,
  `flt3_lineage_holdout.json`, `flt3_pair_label_permutation.json` — static gate,
  primary pilot, lineage holdout and negative control.
* `flt3_pilot_independent_review.json` — separate file-level and arithmetic
  verification.
* `run_*.py` — research-only scripts; none is core code.
* `../deepseek/tasks/DS044/` — fixed-field identity census task and coordinator
  review.  Only transcription and arithmetic were adopted.
