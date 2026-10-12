# Assay-repeat qualification after discrepancy P0

2026-10-12, Asia/Shanghai. **The prerequisite diagnosis is complete. It does not
release a new feedback/Agent study.** Only 126 of 10,600 intended comparisons have
complete, source-qualified same-plate repeats; 53 of those 126 have conflicting
repeat directions. These are descriptive results for jointly ComBat-processed
PRISM responses, not independent raw validation or an identified biological cause.

The user reattached the same research recommendations reviewed previously: the
two attachments are byte-identical, SHA256
`0fd78bbd06164a3c52859580c6686a9a4b19572b7d155dc7dbf8589741230594`.
We carried forward the existing review and executed the repeat-stability
prerequisite in [the completed P0 decision](../discrepancy_p0_20261012/P0_DECISION.json).
This packet is not a newly named formal Block Q. Three agents separately prepared
metadata, reviewed source/scope, and checked safety/arithmetic; root integrated
the frozen run and reports. No historical study or production module was edited.

## Question and frozen observation contract

The narrow question is whether drug response differences near the archived
prior's selection boundary reproduce across recorded assay repeats, including
differences that oppose the prior's committed ordering. This tests reliability
of the available evidence before another evidence-buying policy is attempted.

The [protocol](PROTOCOL.json) retains all 106 exposed archived evaluation contexts
and all 100 prior-top-10 versus prior-next-10 comparisons per context. The fixed
terminal menu excludes the original eight probes. Ranks 11-20 are derived from
the retained prefeedback predictions now; they were not historical top-20 action
commitments. No response value, magnitude or finite mask recruits a case.

Only secondary HTS002 experimental treatments at exactly 2.5 uM qualify. Drug
matching uses the primary archived representative's **full Broad drug-batch ID**;
there is no name/prefix/salt substitution. Context matching uses exact passing
STR row identity and HTS002 pool metadata. MTS010 technical redos are excluded and
logged separately. Nominal five-day exposure is supported by original methods;
sample-specific elapsed exposure and independent culture starts remain unresolved.

For an eligible pair, both drugs must lie on the same compound plate and share
the actual recorded detection-plate identities. On each shared plate the
contrast is `D = LFC(prior-top10 drug) - LFC(prior-next10 drug)`. Negative supports
the committed prior order; positive opposes it. Never pair unrelated plates by
calling each drug's first sorted plate "repeat 1". Preserve the full expected
repeat set, absent-header columns, failed values and technical nesting.

Primary/secondary metadata and archived identity axes are checked before access.
[Independent metadata verification](review/METADATA_VERIFICATION.json) precedes
the [source/executable/menu freeze](runs/main/FREEZE.json), which precedes loading
new secondary response values. The producer projects 90 frozen value columns
from a 489-row source matrix and scores only eligible comparisons. All three
expected contrasts must be finite for a complete case. Exact zeros are separate
ties, not directional successes; no biological margin is invented.

## Coverage and results

| Stage | Contexts | Intended comparison records |
| --- | ---: | ---: |
| Original fixed boundary menu | 106 | 10,600 |
| Metadata-qualified same-plate observations | 91 | 292 (2.75% of intended) |
| All three expected differences finite | 58 | 126 (1.19% of intended; 43.15% of eligible) |

The 292 eligible records reuse only 32 distinct directed drug pairs, 11 compound
plates and 33 detection plates. They are dependent descriptive units, not 292
independent biological experiments. All 10,308 ineligible records and 15 contexts
without qualifying HTS002 pool mapping remain in the ledger.

The small coverage follows the **same-compound-plate contrast requirement** as
well as finite missingness. It is not evidence that the secondary source lacks
the prior's top-ten drugs: those identities all have exact-dose treatment
metadata. Cross-plate contrasts and complete-menu policy utility are outside
this diagnostic. No drug is replaced to enlarge the same-plate subset.

Among the 292 eligible records, 126 have three observed differences, 84 have two,
57 have one and 25 have none. The 166 incomplete records cannot receive complete
agreement labels. The one HTS002 column absent from the response header is logged
with its full expected plate identity; it is not used by this eligible menu.

| Complete same-plate status | Records | Fraction of 126 complete records |
| --- | ---: | ---: |
| All repeats support prior order | 54 | 42.86% |
| All repeats oppose prior order | 19 | 15.08% |
| Nonzero directions conflict between repeats | 53 | 42.06% |
| Exact ties | 0 | 0% |

The 292 three-repeat cases imply 876 repeat-pair comparisons. Of these, 414 are
missing and 462 are observed with both differences nonzero. There are 130
discordant observed comparisons. The unweighted context-macro discordance
fraction is 26.95%, contributed by 79 contexts with an observed nonzero repeat
pair; it includes partial cases and differs from the 53/126 complete-case metric.
No independence-based interval, significance test or scientific pass threshold
is applied.

Fifty-five complete comparisons have positive primary collapsed differences,
opposing the prior's committed order. Only seven have positive differences in
**all** secondary repeats: 7/55 at the comparison level; the context-macro
replication fraction is 10.36% across 37 contributing contexts. One complete
secondary comparison lacks the primary difference and remains missing for that
comparison. This is a descriptive cross-screen check. Nonreplication does not
tell whether the cause is culture variation, noise, normalization, biological
response, compound effects or a transfer failure.

Median minimum absolute repeat differences are 1.351 LFC for stable-supporting
cases, 1.071 for stable-opposing cases and 0.335 for conflicting cases. Magnitudes
are reported to make the sign summaries interpretable; these values do not
define a useful-benefit or equivalence threshold. Every scalar and its coverage
are retained in [ROWS.json](runs/main/ROWS.json) and [RESULTS.json](runs/main/RESULTS.json).

## What changes relative to the uploaded recommendation?

[The source/scope review](literature/SCOPE_REVIEW.md) supports the report's order:
qualify evidence and transfer boundaries before evaluating acquisition or Agent
contributions. FDC remains a proposed evidence interface. This result neither
establishes its novelty nor proves the dual-core system effective.

The original [PRISM methods](https://doi.org/10.1038/s43018-019-0018-6) document
independently treated assay plates, but each treatment is jointly ComBat-corrected
across pool-replicate batches. Agreement or reversal in released repeats cannot
validate raw preprocessing independently. Shared pools, drugs and plates also
preclude treating pair counts as independent culture n. No stress, compensation
or platform-cause labels are inferred.

A complete-outcome oracle bounds realized selection utility on its fixed fully
observed menu. It is not by itself an estimate of expected EVPI, achievable EVSI
or a cost-effective observation policy. Under an explicitly specified common
distribution and utility, standard EVPI bounds EVSI; this packet estimates neither.
The prior P0 hindsight-regret results must retain their narrower scope.

Equal permissions, budget and menus for B2/B3 are necessary for the future policy
comparison. A further control with identical **realized observations, missingness,
history and source evidence** is needed to isolate Agent reasoning from different
evidence access. If only B3 can use literature, its contrast measures the whole
information/planning package. Current data supply no such Agent attribution.

## Next evidence commitment

Keep the fixed-eight-probe stop. The current same-plate subset is too incomplete
and narrow to justify a new functional policy or global reliability claim.
First qualify repeated outcomes for the **original primary HTS conditions** and
the full intended decision menu, with published QC, plate/pool hierarchy and
missingness explicit. The retained official source page advertises
`primary-screen-logfold-change.csv` (107.7 MB), file ID 20237703; availability was
confirmed from the cached official listing, not by downloading its values here.
The [source page receipt](../budgeted_feedback_20261011/data/sources/prism_official.body)
and existing P0 primary-treatment metadata can seed a separately frozen design.
Primary collapsed outcomes must not be presented as independent validation of
their own constituent repeats. Raw-QC/preprocessing claims need raw MFI/control
data and a different isolation design.

Any later correction study additionally needs a qualified distinct observation
channel, pre-action recruitment, justified useful margin and actual cost basis.
It must demonstrate terminal decision improvement over a strong batch and a
same-information deterministic planner before an Agent claim. The small number
of stable-opposing cases here cannot be selected retrospectively as a new sealed
benchmark. A source limitation is an acceptable outcome, not a reason to reopen
probe, KG or LLM tuning on exposed data.

## Reproduction and verification

Run from `D:/MAESTRO` in the existing `maestro` environment:

```powershell
& D:/anaconda/envs/maestro/python.exe -m pytest research/replicate_stability_20261012/tests/test_safety.py -q
# Require a fresh directory; do not overwrite runs/main or its freeze.
& D:/anaconda/envs/maestro/python.exe research/replicate_stability_20261012/run.py --output research/replicate_stability_20261012/runs/reproduction
# Verify retained results without rewriting the historical pre-outcome gate.
& D:/anaconda/envs/maestro/python.exe research/replicate_stability_20261012/review/verify_results.py --output research/replicate_stability_20261012/runs/main
```

`prepare.py` and its fixed metadata outputs are already frozen. Recovery on a
clean checkout requires the exact ignored source files recorded in
[SOURCES.json](data/SOURCES.json), especially the 237,567,060-byte secondary
response file and archived NPZ inputs. Missing sources are errors; another screen
must not be substituted. The preparation script must not overwrite a retained
frozen packet to manufacture a rerun.

Eighteen safety tests pass, including missing-repeat retention, wrong-plate and
identity rejection, tie treatment and no-eligible-context retention. An independent
reviewer reconstructs all 10,600 rows and 106 context summaries without importing
producer selection/scoring helpers; [VERIFICATION.json](review/VERIFICATION.json)
passes. There are 441 metadata/integrity checks and 16 source/scope checks. The
producer takes 16.03 seconds including source hashes and CSV projection, with
zero new fits, LLM calls, external downloads or wet measurements. These are
artifact/arithmetic/design checks, not independent biology. The final
[execution receipt](EXECUTION_RECEIPT.json) records hashes and documentation checks.
Experimental code remains in this research directory; no `src` or `tools`
component is promoted.
