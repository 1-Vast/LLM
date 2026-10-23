# Executable narrow functional contract and source followup

Date: 2026-10-22. **Recommendation: permit a preregistered published-endpoint prediction pilot; do not yet certify unsmoothed local experimental-feedback provenance.** No new functional values were opened by this review, no signal gate was chosen, and no molecular matrix join was performed.

## Source-only work and new findings

Scope was saved in `PRE_SCOPE.md` before the HTTP requests. Research code is `research/decrypte_feedback_assay_20261022/fetch_sources.py`; exact response bytes and SHA256/status/headers/UTC receipt files are in `source/`. There were **seven** HTTP attempts, not six: one Shiny timeout and six successful HTTP responses. No assay result endpoint was requested.

1. The author-linked Shiny HTTPS landing page timed out at a 45-second read timeout. This is a failed access in this session, not proof the site no longer exists.
2. The author-linked ProteomicsDB landing HTML returned 200 and is a JavaScript application shell. Its referenced app bundle returned 200. The app routes `/decrypte` to chunk 8291; that exact chunk returned 200. The decryptE frontend links the author Shiny site but contains no matches for cytotoxicity/confluency/metabolic/viability/raw-signal/relative-intensity terminology. These frontend bytes do not settle the fitness export semantics; no result APIs were called.
3. Public GitHub repository metadata searches `decryptE proteomics`, `decryptE shiny` and `decryptE in:name` were archived. The proteomics query returned `kusterlab/curve_curator`; the Shiny query returned no repositories. The broad name query is dominated by unrelated results. CurveCurator's presence is not evidence that it generated the study's fitness columns and was not treated as such. No candidate repository implementation was downloaded or claimed authenticated.
4. The already saved original text, `decryptE_PROSE.txt` paragraph [90] (line 302), explicitly states: **"All code used for data curation, analysis and visualization is based on publicly available R packages as indicated in the respective section and will be made available upon request with no access restrictions."** This is an author offer of access, not an authenticated public repository. No author was contacted; sending messages was not authorized for this task. A precise reproduction of the exported fitness pipeline may therefore require later author-supplied code, but that is not a prerequisite for all published-endpoint prediction.

Existing supplement metadata establishes 144 Jurkat drugs x three assays, five dose-labelled Raw and Relative columns, and no duplicate drug/cell/type keys. It does not provide independent replicate/control values in the inspected structure. Existing author method establishes measurement of fitness across the doses, normalization rules in prose, and a four-parameter fitting stage; it does not explicitly map every exported column to an unprocessed instrument observation.

## Most defensible task available now

**Target:** predict the author-published `Relative intensity` endpoint at an unrevealed dose for a specified Jurkat drug and specified assay. Initially one assay must be chosen and frozen before values are opened. Metabolic activity is a defensible narrow choice because its stated readout is alamarBlue fluorescence after 3.5 h of the functional assay following 18 h drug pretreatment; it has a clearer read time than the exported IncuCyte time summary. This is metabolic activity under the published protocol, not cell killing, growth rate, clinical efficacy or a safety threshold.

**Numerical target columns:** K:O only, with fixed dose order 1,10,100,1000,10000 nM. J (`Relative intensity 0`) is neither a free experimental replicate nor a noise estimate. C:I (whole-curve parameters) and V (`Effect`) must remain excluded from limited-support input and from the definition of independently held-out observed targets. P:T may be inspected later under an explicit numerical-access protocol for validation of exporter consistency, but the word Raw alone does not justify claiming raw independent feedback.

**Unit and split:** a task is a drug within the single Jurkat background and fixed assay. All dose labels from a later drug stay out of source-rule learning/selection except the predeclared target support reveals. Predetermined drug identities/class groupings may inform source/later assignment before outcomes are accessed. Multiple doses, assay rows, proteins or fields do not become independent drug tasks. The 24 primary-T-cell rows are outside this contract.

**Reveal and information budget:** predeclare one or two allowed dose reveals and evaluate the remaining published endpoint entries. Without fuller export provenance, call this a **limited-entry published-endpoint prediction replay**, not verified adaptive local laboratory feedback. A revealed normalized entry may be treated as one published scalar observation operationally, but no claim that it contains only dose-local raw information is established. This qualification must appear beside any budget comparison. If metadata/code later establishes that all-dose fitting generated K:O, stop that local-feedback interpretation and relabel any experiment as prediction of an all-dose-derived published target.

**Molecular contribution:** begin with a functional-only replay if needed; it is legal to test ordinary priors, constant/DMSO and dose-conditioned predictors on the available endpoints. World-model contribution requires a separately authenticated molecular drug x dose x background x protocol join and like-information controls. Same-well mapping is unnecessary for condition-level prediction but would be needed for individual-state/pair-residual claims.

**Evaluation:** freeze metric, source/later identities, reveal schedule, finite training/search budgets and comparisons before opening values. Report all predefined later tasks, including flat/nonresponsive cases; do not postselect response-rich drugs to substantiate broad utility. This review introduces no minimum effect, significance or success threshold. No verified replicate noise means observed residual cannot be partitioned into biological variation and measurement noise; report this limitation instead of borrowing the proteomic 19% CV. Author-reported marginal fitness effects motivate a direct constant baseline, not an advance declaration of impossibility.

## Remaining contract uncertainties and their actual consequences

| Uncertainty | Consequence |
|---|---|
| K:O local-normalized measurements versus offline all-dose transformations | Prevents verified dose-local laboratory-feedback/budget claims; does not forbid declared published-entry prediction. |
| Cytotoxicity P:T before/after confluency correction; exact correction formula | Raw cytotoxicity is not yet a uniquely defined target in instrumental units. Published Relative endpoint remains usable with declared semantics. |
| IncuCyte time point/aggregation across 3 h and five fields | Avoid exact-time cytotoxicity/confluency mechanistic claims until resolved. Does not convert all endpoints into the metabolic 3.5 h readout. |
| DMSO controls' plate scope, individual values and exported J semantics | Shared normalization dependence and noise remain unidentifiable. No interpretation of J as an independent raw control replicate. |
| Per-condition independent repeats and upstream averaging | Restricts noise, reproducibility and individual-level claims; does not prohibit observed-endpoint model comparisons. |
| Molecular identities and condition matching not yet read here | No completed multimodal pairing or world-model benefit claim. |

No source found here authenticates an independent raw-functional replicate inventory. That is a scoped negative result from this source/code search, not a claim that no such files exist anywhere in MassIVE. No new biological performance, agent utility, inherited updating rule or improved-improver result follows from this qualification. Existing novelty STOPs remain in force.

## Failures and access disclosure

The Shiny request failure is preserved in `source/shiny_landing.receipt.json`; no response body was returned. Broad GitHub repository search is a low-specificity lead, not an exhaustive code-availability audit. One local Python context-extraction command failed with exit 1 because of shell quoting; a corrected command then extracted the static bundle chunk identity. This failed local command did not request a URL or read biological values. Long initial displays in the prior addendum were truncated and relevant identity/header facts were explicitly re-extracted; no global integrity certification is asserted.
