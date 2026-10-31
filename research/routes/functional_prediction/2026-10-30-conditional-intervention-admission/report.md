# Conditional functional interventions: resource admission and first information test

2026-10-30. Repository baseline: `580ccb8333d9c93b39d685eba97455e804c209e8`. Overall goal: **ACTIVE / NOT_ACHIEVED**.

## Decision

The first chemical-genetic information test failed its continuation gate. On 231 development compounds held out by scaffold within three folds, the best fixed chemistry method recovered **3.5498%** of its Top-20 rare sensitizer predictions, versus **6.1688%** for historical gene-call frequency. The difference was **−2.6190 percentage points**, with a conditional exploratory scaffold interval **[−3.6759, −1.7030] percentage points**. All four chemistry settings fell below frequency. This stops the tested Morgan-only scaffold-transfer diagnostic; it does not refute conditional genetic vulnerability or every functional Virtual Cell model.

The corrected result passed the independently authored, frozen arithmetic verifier and a separate outcome interpretation. The first execution had a real mathematical-tie implementation defect and is **not accepted**, even though its displayed aggregate numbers were similar. The one reserved implementation-failure rerun is exhausted. The 63 held-out compounds remain unscored and unreleased. No full Stage-2 Virtual Cell, Agent or core-code promotion was admitted.

## Scientific object and practical use

The intended user is a laboratory prioritizing genetic perturbations that might sensitize cells to an existing compound. A usable predictor would rank compound-specific genetic candidates for follow-up, beyond selecting genes frequently called across prior screens. The initial prerequisite was narrower: can pre-existing chemical structure predict a complete unseen-compound sensitizer-call profile without a target genetic-response panel?

The endpoint is recovery of the source's significant negative CRANKS calls. It is not physical sensitization magnitude, calibrated false-positive rate, direct target engagement, drug-combination efficacy or clinical utility. No cell-background transfer is tested. A genuine functional benefit and a separate cost-matched Agent comparison would still be needed before integration.

The previous B1 low-rank and C2 scaled-dose stops remain intact. This round changes the measurement object and sources; it does not rerun those configurations or access HTS031 treatment values or historical sealed/confirmation outcomes. Scope and budget were fixed in [brief.md](brief.md).

## Three-resource admission

| Resource | What was authenticated | Current disposition and missing requirement |
|---|---|---|
| Chemical-genetic matrix, NALM-6 | Authenticated bioRxiv preprint v2, DOI `10.64898/2026.01.28.701823`; Mendeley `zdnrtmyfgh/1` Table S1/S2 match provider hashes. Metadata contains 305 compounds, 297 parseable SMILES, 404 retained screens and 19,031 gene rows. | Conditional admission for a fixed published-call diagnostic, which ran below. CRANKS is an essentiality-matched rank-tail score, not the illustrative four-term log-fitness contrast. Source-selected regimens, shared controls and incompletely documented artifact correction limit prospective/biological interpretation. |
| Environment-dependent GI, K562 | Molecular Cell, DOI `10.1016/j.molcel.2026.01.025`; GEO `GSE312636`, original methods/code, paired transduction/passaging replicates, three interventions and two untreated references. Eight processed matrices share 303 genes plus NTC. | Conditional resource only; no model or numerical GI analysis. Certify the exact supplementary-file/environment binding and missingness, or preregister reconstruction from the condition-bound raw counts. The 45,753 unordered-pair positions per map are structural identities, not certified finite measurements or independent experiments. |
| External dose, Simplicity / DrEval | Original methods, artifact manifests, source ancestry and selected preprocessing code distinguish observed measurements from fitted/calculated exports. | Not ready for observed-dose outcomes or prediction. Exact drug/cell forms, measured concentration intersections, timing, endpoints, controls and replication need qualification. No external flip result, positive or negative, was obtained. |

The owning contracts retain exact source locators, acquired files, versions and reading scope: [CGI](cgi_source/evidence_contract.md), [environment GI](egi_source/admission_contract.md) and [external dose](external_dose/admission_report.md).

Several details change the proposed interpretation. CGI co-cultured sequencing samples are not extra independent screens; hypothesis-selected round-9 validation is excluded. Native sensitization uses negative CRANKS with FDR <0.05. A missing significant call is a **non-call**, not established negative biology. CRANKS2 uses global outcome-derived essentiality information and was not downloaded or used. S2 describes a 7p artifact correction without the recovered algorithm; the source also describes 21q arm-loss artifacts.

Environment GI uses ATR−DMSO1, ETOP−DMSO2 and glucose-deprivation−DMSO2 differences of separately fitted and standardized GI maps. These are descriptive standardized changes rather than direct four-term fitness interactions. Etoposide and glucose deprivation share the second reference. The follow-up validation is selected and uses an altered regimen. Two biological replicates constrain uncertainty; guide constructs and network edges cannot replace independent cultures.

Simplicity's generated concentration points and fitted objects cannot supply observed-only replication. PRISM's preprocessing itself includes fitted-curve corrections; its raw archive's processing stage remains unresolved. DrEval and Simplicity reuse original screen families, with GDSC release differences that prevent asserting exact duplicate-well overlap. Matching dose ranges is insufficient to establish shared observed dose points.

## Frozen development test

The [initial protocol](stage1_protocol.md) was amended before calls were accessed following an independent initial challenge. The controlling [v1.1 amendment](stage1_protocol_v1_1.md), [implementation amendment](stage1_implementation_amendment.md), [input freeze](input_freeze.json) and [output contract](stage1_output_contract.md) preserve the actual design. The correction after the failed first execution is separately disclosed below; it is not a new unexposed scientific preregistration.

Metadata-only preparation produced 374 eligible single-compound molar screens and one deterministic representative per compound: **294 compounds / 240 scaffold groups**. The fixed split is **231 development compounds / 181 scaffolds** and **63 held-out compounds / 59 scaffolds**. Development folds contain 70, 97 and 64 compounds. Bemis–Murcko grouping ignores chirality and puts all acyclic compounds in one group. This is scaffold transfer to previously seen gene identities, not mechanism-class or unseen-gene transfer.

Morgan radius-2, 1,024-bit fingerprints include chirality. Classes/subclasses with uncertain outcome ancestry, population doublings, hit counts, response probes and costly omics are excluded as features. Source IC30-selected and sometimes adaptively modified regimens mean this is prediction under the published assay conditions, not arbitrary-dose or zero-assay-cost prediction.

An HGNC2020 identity projection through a pinned public HGNC snapshot retains **18,415 unique canonical genes**, excluding 486 source rows on 7p/21q, 87 duplicate canonical source rows and 43 unknown/ambiguous identities. This conservative pre-label mask does not reconstruct the author's unknown correction or certify independent label construction. The gene roster and source hashes are pinned in [gene_universe_freeze.json](gene_universe_freeze.json).

Each training fold defines rare eligible genes from its own calls: at least one source call and at most 10% source-compound prevalence. All query compounds, including those with zero eligible calls, remain in macro P@20. Canonical-gene lexical order resolves prediction ties. The eligible counts are 792 / 659 / 840. There are 2,333 retained development sensitizer rows; no S2 numerical values are used.

Methods are gene frequency, the mean of five Tanimoto-nearest source profiles, and ordinary full-rank multioutput Ridge with alpha 1, 10 or 100. Ridge uses training-only fingerprint standardization and an intercept. These are a bounded information diagnostic, not a complete comparison of the user's proposed local conditional model against every listed baseline. LightGBM was unavailable and not installed. Stage 2 was conditional on useful incremental information here.

For each of **49 null draws** (seed 20261030), whole scaffold blocks are reassigned within matching ordered screening-round tuples. The same reassignment supplies training and validation truth throughout all folds; eligibility, frequency and predictions are recomputed. All genes in each profile move together. Each aligned/null statistic selects the maximum full-CV gain over the same four chemistry settings. Of 181 blocks, 170 / 177 compounds can move; 11 blocks remain fixed, and all 49 mappings are distinct. Interpretation depends on this conditional block-exchangeability assumption.

The information gate requires **positive gain AND conditional p≤0.05**. The paired scaffold bootstrap uses 2,000 draws, seed 20261031 and exact recovered-call differences. Its interval is conditional and exploratory after model selection, with shared training and source controls; it is not a population-coverage or biological-replication certificate. Passing this gate would only support a later protocol, not release the 63 outcomes or establish exceptional practical benefit.

## Corrected accepted arithmetic

| Fixed method | Macro P@20 | Recovered calls / 4,620 selected positions |
|---|---:|---:|
| Gene frequency | **6.1688%** | **285** |
| Nearest five | 2.7056% | 125 |
| Ridge alpha 1 | 3.0736% | 142 |
| Ridge alpha 10 | 3.1169% | 144 |
| Ridge alpha 100, selected chemistry setting | **3.5498%** | **164** |

Selected gain is −121/4,620 = **−0.026190476**. The 95% paired-scaffold interval is **[−0.036758801, −0.017029803]**. The source-eligible oracle P@20 is **25.4545%**. Thus frequency is not at a mathematically saturated call-recovery ceiling; the negative point comparison is distinct from an impossible-headroom gate. Neither the oracle nor its gap measures attainable physical drug-discovery benefit.

Conditional max-selection permutation **p=0.04**: one of 49 null gains is at least the observed gain, with the add-one calculation `(1+1)/50`. This retains limited evidence that aligned chemical/profile information does better than most prescribed reassignments. All null gains and the observed gain are negative relative to frequency. Consequently the positive-gain conjunction fails. It would be wrong either to announce a successful predictor from p=0.04 or to conclude that chemistry contains no information.

The corrected output is under [stage1_corrected](../../../../data/processed/conditional_interventions_20261030/cgi/stage1_corrected). [Independent audit](review/independent_metrics_corrected/audit.json) reports **PASS / MATCH** for saved-rank arithmetic and completeness; [independent outcome interpretation](review/corrected_outcome_check.md) supports stopping this candidate at its continuation gate. These checks do not refit models, reconstruct full unsaved predictions, independently certify label extraction/normalization, resolve leakage ancestry or validate biology. This is selected development evidence, not a score on the 63 held-out compounds.

## Implementation failure and correction

The first model matrix completed all nulls, but the frozen verifier rejected its frequency ranks. Weighted floating accumulation gave different values to equal source counts and violated lexical mathematical ties. Interim numerical results had already been shown; they are withdrawn as accepted evidence. [Failure diagnosis](review/initial_run_verification_failure.md), the original outputs and original script/launcher/freeze remain preserved.

The repair sums binary source/donor counts exactly before one division for frequency and nearest-five means. It changes neither Ridge nor features, labels, folds, nulls, seeds, metrics or gates. A [static repair review](review/repair_code_check.md) passed before using the sole reserved rerun into an isolated directory. The [correction note](implementation_correction.md) records the post-exposure timing and exact identities.

[Output comparison](review/correction_output_comparison.json) confirms identical calls, IDs, folds, scaffold groups, rounds and null assignments across runs; all saved Ridge Top-20 scores/indices are bitwise unchanged. Frequency ordering changed, and nearest-five scores received tiny rounding corrections. Original artifact hashes still match retained files. The verifier itself remains SHA256 `7dc11bfb045fcb8b51de64b8761e744f81c2f30645ab3b91cef65658e6be57af`. Agreement of aggregate numbers never rehabilitates the invalid first run.

## Method reading, prior work and resource use

The CGI worker read selected original design, scoring, control, correction and availability sections, plus CRANKS code; the EGI worker read matched-condition, phenotype/GI, selection/validation and normalization methods/code. Its source preview incidentally exposed nine growth-normalization constants and qualitative Results headings; no numerical GI scores were used. The dose worker read original Simplicity prose/supplemental methods and DrEval methods/preprocessing source, excluding notebook outputs. Their contracts give exact sections and exposure. These are targeted source audits, not complete readings of all Results/Discussion or all supplements.

The inspected earlier paper *Improving Measures of Chemical Structural Similarity Using Machine Learning on Chemical–Genetic Interactions* (DOI `10.1021/acs.jcim.0c00993`, 2021) already learns functional structural similarity from chemical-genetic information. Root read its complete Abstract and Methods subsections 11–14. A 2025 perturbation-encoding benchmark was only abstract/metadata-level evidence. Morgan, nearest neighbors, Ridge, sparse conditional interactions and module representations are not new algorithms. The audit does not clear novelty for a future intervention-dependent functional model.

The shared round ceiling was six search/retrieval passes, 80 counted HTTP attempts, 512,000,000 completed body bytes and four compute threads. Actual traffic was **54 attempts / 178,620,429 completed decoded response-body bytes**, plus a known saved 2,064,505-byte aborted Crossref body. Wire/redirect/compression and aborted traffic totals are not fully measured. Passes 1–4 were used; pass 5 and the reserved pass-6 network allocation were unused. Independent review added zero requests. No native browser/search capability was available; official public HTTP and saved originals supplied the bounded evidence.

Both matrices completed within the 1,800-second hard-launch limit. First child wall/CPU times were 18.717427/18.609375 seconds; corrected times were 16.756539/16.703125 seconds. Launcher totals were 27.261232 and 24.372720 seconds. Each execution decoded the same 12,816 authorized development score/FDR values; repeating these is not new data. No third model matrix is allowed. [usage.json](usage.json) and [record.md](record.md) retain failures, actual accounting and commands.

The owner CLI registered three authenticated original JATS files with truthful partial-reading notes. The existing library integrity check reports **184 unique papers / 154 files, zero errors or warnings**; this is an inventory total, not this round's new acquisitions, a reading count or novelty validation. The owner's main-status tally omits these three acquired JATS originals because they use technical supplement slots. See [library verification](library_verify.json) and the registration transaction records under `source_review/`.

No install, paid model API, commit, upload, external message, scheduler, protected-outcome access or core-code promotion occurred. Inherited effective model/effort, tokens and monetary cost were not exposed. Multi-agent source, initial protocol, repair and arithmetic roles are recorded; shared-model agreement is not independent biological evidence. Public workbook bytes are acquired locally and parsed as containers, so access filtering is not secure blinding; the 63 compounds' call pairs/score values have not been reconstructed, summarized or scored.

## Retained decision and next admissible step

Park this exact structure-only diagnostic. A new acronym, more tuning or a larger model is not justified by its negative comparison. No observed gain supports Agent integration or advancement into `src/` or `tools/`.

The chemical-genetic question remains open under a genuinely changed information contract: for example, verified functional descriptors available before the genetic assay, or a small measured query panel with its cost explicitly charged. The latter is a different conditional-measurement task and cannot be substituted for zero-response prediction. Any later study must define its own protocol and practical endpoint before using held-out outcomes; this round grants no release.

Environment-conditioned GI remains the most direct untested functional-relation object in this brief. Its next decisive step is the unresolved environment/file and normalization/missingness contract, followed by a metadata-frozen development contrast with both biological replicates retained. External dose work must first prove shared observed concentration points and comparable endpoints. Neither branch has numerical predictive evidence here. The current work supports these precise admission questions, not a validated new mechanism, biological benefit, external transfer, novelty or an achieved overall goal.
