# Conditional splice-choice transport: scientific question v1

2026-10-31. Scientific question and untested restriction, not a numerical protocol, recommended learner or observed result. No response records, fitted models or author-code execution informed this version. Published aggregate findings are exposed literature. Whole-round allowance remains48HTTP attempts/192MiB, three shared evidence passes and at most two substantive revisions after v1.

## Biological question and practical output

Can an RNA-drug discovery team predict redistribution among a fixed local set of alternative splice choices after a regulatory change, using source-background drug responses and target-background untreated choice frequencies? The proposed output is the entire previously unmeasured target treated choice distribution at the same drug, dose and endpoint. It could inform desired/unintended exon-selectivity experiments. Splicing is a molecular functional endpoint; drug-discovery benefit is proposed, and killing or clinical efficacy is not the claim.

The potential object is a closed set of at least three mutually exclusive junction choices with a common biological denominator, such as alternative donors to one acceptor. Arbitrary overlapping cassette-exon PSI margins are not such a vector. A local conditional junction-use distribution might be measurable without full transcripts; whether the acquired records support a biologically appropriate choice set remains unqualified.

## Proposed restriction and observable consequence

Let p and p' denote untreated and drug-treated source choice probabilities, and q the untreated target probabilities. Suppose the regulatory intervention changes baseline competitive weights but preserves the relative drug multipliers a_j. For supported positive source probabilities, a_j is proportional to p'_j/p_j. The target prediction is

`q'_j = (p'_j/p_j) q_j / sum_k[(p'_k/p_k) q_k]`.

For one drug-responsive choice T with multiplier lambda and alternatives A/B with equal reference multipliers, the rule predicts equal proportional suppression of A/B and preservation of their ratio. Distinct untreated T abundance can therefore predict different drug effects on A even if A's own untreated abundance is equal. This is a conditional prediction, not evidence that any regulator obeys it.

For T versus an aggregate alternative, the equation is exactly `logit(q'_T)=logit(q_T)+log(lambda)`, an ordinary context-strength/odds model. For a full vector, it is ordinary multinomial odds/density-ratio reweighting. Every positive source untreated/treated pair admits fitted factors, so source fit cannot test the restriction. Its empirical content is reuse of the same relative factors in an independently withheld regulatory context. Arbitrary target-specific factors eliminate that content. No novelty follows from the equation or a new model name.

## Assumptions and strongest alternatives

The load-bearing unresolved assumption is an eligibility rule, specified without target treated responses, identifying regulatory changes/choice sets that preserve relative drug action. U1C depletion affects the drug-compatible complex and could directly violate this assumption. One such perturbation does not authenticate a general intervention family. A second choice may become directly drug-responsive. RNA degradation, alternative transcript production, incomplete junction ascertainment, shared sample noise and changing denominator composition can also break the interpretation.

Source p/p' and target q are paid measurements, not free sequence features. A new-combination claim differs from an unseen-exon, unseen-compound or unseen-dose claim. Unsupported/zero source probabilities leave factors unidentified; absent rows cannot simply be set to biological zero. Reads and exon rows do not replace independent biological samples.

Relevant ordinary comparators are the Ishigami context-strength/allelic-manifold model, the exact shared multinomial model, and an equally informed flexible ordinary predictor given all competing-choice baselines, sequences and measured source responses. The paper's XGBoost/local-U1/baseline features remain relevant to sequence-driven prediction. Improving over an isolated-exon predictor would not establish value over the complete-information alternatives. A useful scientific regularity could be implemented by an ordinary model, but its intervention class and prospective predictions require evidence.

## Actual evidence and unresolved observation contract

Lenkeit2026 (DOI10.1038/s41467-026-74594-9) already changes target exon space through U1 changes and models sequence/baseline inclusion. Its event discovery is partly treatment informed. A plot script's common-baseline filenames and absent-row zero fill do not authenticate a matched interaction panel. Publisher SourceData has figure-selected tables; headers alone do not establish an event universe or replicates.

U1C2026 (DOI10.1038/s41467-026-74765-8) already studies same-cell-line U1C depletion by branaplam/risdiplam dose, including response loss, dose shifts and unmasked targets. Sec11/12/28 are original load-bearing passages. Supplementary Data2 has22condition-summary PSI fields, not authenticated replicate columns. Official GEO GSE304951 metadata and the first line of its complete29713285B junction-count gzip authenticate48sample columns (two backgrounds; four vehicles and two replicates at each of ten compound-dose conditions per background). No count records were projected. GEO/Results say HEK293 while Methods say HEK293T; GEO protocol concentration prose has mM inconsistencies against sample titles/original Methods. The metadata discrepancies are retained.

Ishigami2024 (DOI10.1038/s41467-024-46090-5) is necessary older prior. Sec6 assumes a local drug effect independent of other context factors and reports exceptions; Sec8 models two branaplam interaction modes; Sec11 explains why EC50 changes can arise from baseline/context strength. Endpoint dose shifts alone do not identify affinity or kinetic rates.

Historical DEDSeq source at9181a015163354c015485fba3e0c3a153b7ae0d8 (2021-12-19) is inert evidence, not an authenticated paper-specific pipeline. Selected01source unions sample-observed junctions, zero-fills missing counts and filters across all samples. Selected06source aggregates splice-site support, constructs multiple skipping junctions and computes event-wise inclusion/exclusion margins. This does not by itself authenticate complete multibranch choice sets. The original says minor modifications; actual settings/export filtering are unknown. The full code archive is incomplete; three selected source files were acquired separately.

Carlson2025 (DOI10.1073/pnas.2509444122) and Crona2017 (DOI10.7554/eLife.28629) support an ordinal scalar-null check: a credible drug-order reversal within the same exon across contexts rejects a shared monotone scalar-additive family. This is established sign/qualitative interaction. Multiple latent dimensions can also reverse ranks; no molecular contact or new learner follows. Reversal across unrelated exons is a different question. The donor's DMS Poisson bootstrap is not admitted for this RNA design.

## Admission decision still required

No numerical endpoints, eligible choice universe, reconstructable observation/support rule, held-out unit, training/measurement costs, likelihood, split, tuning, metrics, thresholds or implementation are frozen. No fitting or effect analysis is admitted by this question. Independent scientific review should assess the useful claim, ordinary equivalence, current observation contract and exact missing constructive step. A later experiment requires its own complete freeze and actual scientific/code admission review; it must permit failure or an inconclusive result. Data access failure or unknown eligibility does not refute the biological hypothesis.
