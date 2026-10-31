# Can a local splice-site action predict context-dependent changes in complete RNA outcomes?

Proposer version v1, frozen for fresh independent scientific review. No response exposure or fitted result underlies this version.

## Decision

A concrete, consequential question survives, but a new Virtual Cell method or a validated molecular mechanism does not yet follow. The question is whether changing a defined donor site has a portable local action while promoter or drug context changes the mixture of competing RNA products. If so, a sign reversal in aggregate exon inclusion need not imply reversal of the local action. The additional observable is the joint distribution of splice-site use and complete isoform identity, which the source attempted to measure. It is not a different transformation of the same PSI value.

The strongest present-resource lead is a prospective prediction for a GT/GC donor construct pair: measure both constructs under reference conditions and the GT construct under a target promoter or drug condition, then predict the GC construct's full RNA outcome in that target condition. The predictive rule below is ordinary constrained multinomial reweighting. Its possible contribution is an experimentally supported functional restriction, including its precise failures, rather than a new mathematical principle. The closest inspected prior already transfers a scalar mutation parameter across starting PSI values. If the extra isoform channel does not carry independent information, this lead reduces to that prior and should stop as a main research direction.

The intended user is a team developing functional splicing assays for drug discovery. Its present alternative is to measure every constructed variant-by-drug combination directly, and aggregate inclusion can obscure loss of the intended RNA product to retention or cryptic splicing. The conditional payoff is prediction of an unmeasured variant's molecular drug response with a separate intended-product and aberrant-product readout. The available perturbations are general transcription drugs in synthetic HEK293 reporters; the question does not establish endogenous allele-specific response, RNA-targeted drug action, ASO activity, protein rescue, or therapeutic efficacy. That limited application must still use physically authenticated RNA outcomes; an easier prediction of processing artifacts would not satisfy it.

At present, output eligibility, junction identity, and the causal donor-edit interpretation remain unqualified. No response table was read and no numerical experiment was run. This is a developed, falsifiable lead, not execution admission or an innovation recommendation.

## Provenance and independent development

The pre-feedback reasoning is preserved in `initial_reasoning.md`. This report incorporates subsequent root messages establishing a design-only projection and a locally saved eLife original. No root verdict was requested or inherited. Requested role settings were Astra/MAX; effective model, effort, token use, and cost were not supplied by runtime telemetry.

Inspected sources and scope:

- `../investigator/sources/promoter2026.xml`, DOI 10.1038/s41467-026-76370-1: bounded original sections Sec3-Sec8, Sec10, Sec12, Sec14, Sec21-Sec23, Sec26-Sec30, plus cited-reference identities. The primary evidence is the actual article, not search snippets.
- `../investigator/promoter_schema2.json`: column names only. The processed table has one row per observed isoform and includes counts and splice coordinates; it is not a table of independently designed intervention-outcome pairs.
- `../root/promoter_design_identities.tsv` and `../root/promoter_design_census.json`: identity-only projection. Historical response columns remain opaque. The projection has 9608 unique library IDs; the native subset has 264 rows and 132 nonempty gene labels, so the article's nominal 134 endogenous families cannot simply be substituted for a verified eligible family count. Root subsequently reported the completed exact pair audit in `../root/local_donor_design_pairs.json`; that update is attributed to root and was not independently recomputed here.
- `../root/sources/splice_scaling_elife2020.xml`, DOI 10.7554/eLife.59959: original abstract; sections s2-1, s2-7, s2-9, and s3. Cell 2019 DOI 10.1016/j.cell.2018.12.010 was identified through the original reference lists; its full methods were not inspected.
- The innovation-research skill and `references/idea-development.md` informed the constructive-case, ordinary-equivalence, and measurement-cost requirements.

No HTTP requests, response-data access, fitting, numerical execution, author-code execution, installation, protected-data use, or additional agents occurred in this role.

## Observation, limiting premise, and changed research object

**Observed in the source.** Promoter context changes inclusion, motif activity, cryptic donor/acceptor choice, and retention. Drug treatments under pEF1alpha also change splicing. The source already owns promoter-response clustering, sequence/structure prediction of those clusters, motif-direction differences, promoter-dependent exon-length effects, integrated-reporter and endogenous-promoter follow-ups, and an upstream-intron rescue of weak donor fidelity. It explicitly checks DeltaPSI, log2(I/S), and mutation-effect scales. Repeating these observations with a new encoder or link would not be a contribution.

**Limiting premise.** A scalar inclusion measurement treats multiple final RNA products as one phenotypic axis. The paper's computational definition counts an exon as included when the sequenced region contains two spliced-out introns, after coverage and evidence filters. This is not the same as the fraction of one intended, fully canonical product. In particular, a cryptic donor product can contribute to the two-intron class, while upstream intron retention with use of the intended cassette donor can be outside it.

**Changed relation.** Separate (i) whether the edited, design-annotated donor is actually used from (ii) which full RNA product results. Ask whether context changes the baseline association between these two measured properties while the edit's donor-use effect remains the same. This turns an uninterpretable PSI reversal into a falsifiable allocation prediction.

**Operable inference.** A source-context pair measures the donor-use effect of the construct change. The target-context reference construct measures the current mixture of competing products. A fixed local-action law combines those two measured quantities to predict an unobserved target-context edited construct.

**Discriminating prediction.** The law fixes more than a mean: all RNA products that share donor-use status must preserve their relative proportions under the edit, and the change in donor-use odds must transfer between contexts. It predicts when aggregate PSI and the intended-product fraction change in different directions. A model that merely learns a promoter embedding makes none of these restrictions unless they are explicitly imposed.

## Exact biological and intervention scope

Root's completed design-only audit identified 72 family labels with a `cassetteconstvar` pair whose acceptor label is `constitutive` and whose donor labels are `constitutive` versus `GC`. All 72 pairs have exactly one T-to-C difference at oligonucleotide position 163, zero-based, outside barcode positions 18:30. All 72 also differ in the barcode; there are zero matched-barcode pairs. The 72 verified design pairs are not a qualified response count.

One directly inspected example is SZRD1, library IDs 17064 and 17065. Their cassette-body donor sequences contain the GT-versus-GC contrast in an otherwise common synthetic acceptor/donor background. They are not natural WT versus one-base mutant. The neighboring native row, 17063, differs at multiple designed splice-site positions from both synthetic constructs. The paired barcodes also differ.

Therefore the present-resource intervention is a change between two complete reporter constructs. Calling it the isolated causal effect of one donor nucleotide would require a further barcode assumption. At least one matched-barcode contrast, preferably the donor-base by barcode crossing described below, is needed to separate the donor action from barcode effects. Source barcode-control results are useful context but cannot establish absence of a context-dependent barcode effect for every edited construct.

Define the donor by its fixed design coordinate, not by the source's `canonical` donor flag. The source defines canonical donor dinucleotides as GT, so the intended GC donor can fail that flag even when the intended junction is used. Sequence-locality must be checked after masking only the authenticated barcode span, without selecting pairs according to their responses.

The source's eight transcription-drug dose conditions are under pEF1alpha. There is no authenticated drug-by-non-pEF1alpha promoter crossing. A test can separately transfer the construct effect across promoters, or across drugs at pEF1alpha; it cannot claim to predict the unmeasured combination of both. The drug conditions are not authenticated paired biological replicates merely because there are two concentrations.

## Minimal model and its ordinary reduction

Let `p_c(j)` denote the reference construct's probability of mapped RNA outcome `j` in context `c`. Let `G(j)` be 1 when the fixed, design-annotated cassette donor is used and 0 otherwise. Outcomes must be assigned using the same physical junction definition in both constructs. Let `q_c(j)` denote the edited construct's probabilities.

The proposed restriction is:

`q_c(j) = p_c(j) * gamma^G(j) / Z_c`,

`Z_c = 1 + (gamma - 1) * p_c(G = 1)`.

The source-context observations estimate `gamma` from the change in donor-use odds. The same value then predicts the target-context distribution from its measured reference distribution. The hypothesized biological content is that the construct change alters only one local donor-recognition preference, with a context-invariant factor, while promoter/drug context changes the other competing-product weights.

This can arise in a model where local recognition contributes one separable statistical weight to all products using the site. It is not guaranteed by a one-base sequence change. Finite transcription windows, irreversible assembly, RNA structure, cooperative exon definition, factor recruitment, RNA decay, and barcode effects can all violate it. A good fit would establish the endpoint restriction under the measured assay conditions; it would not identify binding energy, kinetic rates, or a particular recruited factor.

The mathematics is an exponential tilt, a log-linear model with one known binary feature, or a constrained multinomial odds model. These descriptions are equivalent. Introducing a graph, encoder, latent context matrix, or neural parameterization would not change that fact.

When `G` is exactly the binary inclusion label, the model reduces to the familiar mutation-scaling relation:

`q(Y = 1) = gamma * p(Y = 1) / [1 - p(Y = 1) + gamma * p(Y = 1)]`.

The inspected eLife 2020 original explicitly says that a mutation parameter A estimated at one starting PSI can predict its effect at another starting PSI, and it discusses trans context differences and splice-site mutations. This scalar transfer is inherited, not novel. Cell 2019 is a closer originating prior, but only its bibliographic identity was authenticated here. No uninspected methods or claims of absence of prior multi-isoform extensions are inferred.

## Constructive case: identical marginal readouts, different predicted response signs

This is a hand-derived thought experiment, not an observation or simulation. Let `Y = 1` mean the source-defined two-intron inclusion class. Consider four physically distinct reporter products:

| Product | `Y` | `G` | Reference profile in context A | Reference profile in context B |
|---|---:|---:|---:|---:|
| Intended donor and intended two-intron product | 1 | 1 | 0.4 | 0.1 |
| Two-intron product using a cryptic cassette donor | 1 | 0 | 0.1 | 0.4 |
| Upstream intron retained; intended cassette donor used | 0 | 1 | 0.1 | 0.4 |
| Cassette skipped without that donor | 0 | 0 | 0.4 | 0.1 |

Both contexts have baseline PSI 0.5 and baseline intended-donor usage 0.5. Even those two marginal measurements cannot distinguish them. Their joint isoform distributions do.

Suppose a weakening edit has `gamma = 1/2` in both contexts. The predicted source-defined PSI becomes 0.4 in A and 0.6 in B. Nevertheless, the intended two-intron product decreases in both contexts, from 0.4 to 4/15 in A and from 0.1 to 1/15 in B. An apparent inclusion improvement can therefore accompany reduced intended-product abundance without changing the sign of the edit's local action.

The exact identity is:

`q_c(Y = 1) - p_c(Y = 1)`

`= (gamma - 1) * Cov_p_c(Y, G) / [1 + (gamma - 1) * p_c(G = 1)]`.

Thus the extra information doing the work is a measured association between site use and outcome class. It is neither a saturating scalar link nor the mere number of model parameters. The source's alternative PSI-scale analyses do not determine this joint distribution.

This construction proves only that the proposed distinction is possible. It does not establish that the 72 candidate pairs populate the necessary discordant products. Their constitutive acceptor background could suppress those products so strongly that `G` effectively equals `Y`; in that event there is no substantive extension beyond scalar mutation scaling.

## Indistinguishable inputs and failure cases

Even complete reference-context reference/edit distributions plus the target-context reference distribution do not identify the target edit response without a transport assumption. Two biological systems can match all three observed corners exactly and differ only in a target-context interaction between the edit and promoter-associated recruitment. One can have target `gamma` equal to the source value; the other can have any different positive value, or different effects among products sharing `G`. The missing fourth corner separates them. No flexible encoder can remove this information limit without additional measurements or assumptions.

Further failure cases are substantive:

- **No informative donor competition.** If the allowed calibration data put nearly all probability on donor use or nonuse, a finite assay does not identify a stable donor-use odds multiplier. Treating a missing product as a true zero or adding an arbitrary pseudocount does not solve this biological information problem.
- **New product appearance.** Exact reweighting cannot create a product with truly zero reference probability. A genuine edit-induced splice option violates its support restriction. An undetected rare reference product and a genuinely unavailable one are different cases; finite counts cannot automatically separate them.
- **Local edit changes conditional outcomes.** If reference and edited constructs have different outcome proportions even after conditioning on `G`, the single-site action law fails already in the calibration context. A context-specific factor per isoform would remove the restriction and return to generic multinomial transport.
- **Context changes the effective action.** If conditional distributions remain stable but donor-use odds shifts differ between contexts, the global `gamma` fails. The endpoint data cannot by themselves say whether recruitment, kinetics, decay, or barcode behavior caused the failure.
- **Read assignment changes.** A mutation that changes mapping correction or ascertainment can produce apparent donor-use changes even without a corresponding physical change. A predictive score under that selection process is not evidence for local recognition.

Broad context invariance of arbitrary motif insertions is not proposed. The source's promoter-dependent motif activity already contradicts that broad version, and motifs can influence multiple recognition events. A motif insertion is also not an ASO intervention.

## Which physical channel separates which explanation?

| Competing explanations | Discriminating channel | Present status |
|---|---|---|
| Scalar PSI scaling versus redistribution among distinct RNA products | Joint identity of the used donor and the full splice product | Attempted by the processed isoform table; assignment and complete denominator not yet qualified |
| Donor nucleotide effect versus linked barcode effect | Donor-base by barcode crossing, or matched-barcode donor edits | Not established for the current pairs |
| Fixed local action versus context-dependent action | The held edited construct in the target context, evaluated on full outcomes | Potentially measured in the source, still unopened and not admitted |
| Sequential upstream-splicing memory versus endpoint pathway association | Nascent or time-resolved joint measurement of upstream excision and downstream recognition/commitment, with a discriminating perturbation | Absent from the known mature-RNA table |
| Kinetic window versus recruitment or stability changes | Independently measured elongation/pausing, factor occupancy or engagement, and/or isoform production-decay dynamics under the actual perturbation | Not supplied by the current schema |

The source's added upstream-intron rescue does not by itself measure chronological splice history or isolate the cause of rescue. Final retention can result from multiple event orders. Conditioning on final retention can also induce selection between competing pathways. This report therefore does not call a conditional endpoint relation a causal splicing-history gate.

## Exact paid inputs and held unit

For a held gene-family construct pair `i`, the allowed calibration inputs are:

1. Authenticated design sequences and identities of the GT and GC constructs, fixed donor coordinate, barcode identities, promoter and drug-dose labels.
2. The complete reference-context GT outcome counts.
3. The complete reference-context GC outcome counts.
4. The complete target-context GT outcome counts.

The target-context GC counts are withheld until prediction is fixed. The output is their RNA outcome distribution and resulting changes in intended-product fraction, cryptic/retained-product fraction, and source-defined PSI. For drug transfer, the reference is untreated pEF1alpha and the target is a declared transcription-drug dose at pEF1alpha. For promoter transfer, both contexts are untreated promoter constructs.

All variants derived from a held endogenous family, and conservatively from the same gene when family identity is uncertain, stay outside supervised training and model selection. The three allowed calibration profiles from that held family are explicitly revealed to every competing method. This is calibrated prediction for a new family/construct combination. It is not zero-shot unseen-family prediction, a completely unseen-drug prediction, or an independent-source validation. Holding out a target edited cell while hiding its paired reference information from competitors would be unfair.

The known number of contexts, doses, barcode variants, and isoform rows does not multiply the number of independent biological families. Biological replication must be authenticated separately. The source's row-stratified classifier evaluation cannot substitute for this split.

## Exact unresolved measurement claim and the next discriminator

The unresolved premise is that the reported outcome count for a row can be assigned to use or nonuse of the same physical donor coordinate in GT and GC, without silently combining reads from both states. The row may also represent only a selected subset of RNA products. This is a claim about the observation process, not the truth of the proposed biological invariance.

Root can perform a narrow identity-only projection of processed control rows while keeping `nreads`, fractions, PSI, and historical responses opaque. For the authenticated GT/GC pairs, the useful projection is the literal isoform identifier; candidate original intron coordinate tuples; corrected splice coordinate tuples; exon/intron counts; design donor coordinate; and any already-exported read-geometry identities needed to interpret coordinate conventions. The exact questions are:

1. Does the literal isoform identifier encode candidate pre-correction coordinates, corrected coordinates, or something else? Coordinate offsets and start/end conventions must be fixed from design and source, not selected to maximize agreement.
2. Can the same reported isoform key correspond to candidate original junction tuples on both sides of the donor-use classification? Conversely, are identical candidate original junctions split into different reported classes by a genotype-dependent MaxEnt reassignment?
3. Do `_o` tuples, literal isoform identifiers, and corrected fields disagree about use of the intended GC donor? In particular, does a GT-only canonical flag disagree with a junction at the intended GC coordinate?
4. Are original coordinates absent or merely representative metadata attached after a grouping operation that may already have combined distinct original junctions?

A grouping or classification conflict can directly refute the proposed observable `G` for that export. Absence of conflicts cannot prove count preservation: one row could store only the first representative coordinate of an already merged group. Root reports that the inspected official Git tree contains figure code/data rather than the upstream mapper implementation, and that figures use corrected MaxEnt coordinate fields. This leaves the grouping operation unauthenticated.

The positive discriminator would be the actual inert upstream aggregation implementation, an authoritative specification of its order and grouping keys, or equivalent trace evidence showing that each exported count is the sum of reads with a homogeneous pre-correction donor-use status. Separately, retained/discarded/unassigned read accounting must establish the endpoint denominator. No bulk sequencing reprocessing is proposed or authorized here.

Formally, the observed table is generated by a measurement kernel `M_(construct, context)` applied to physical RNA products, followed by selection and normalization. A sufficient condition for local donor reweighting to survive that observation process is that the kernel is identical between the paired constructs within a context and only merges physical outcomes sharing `G`. A context-specific but construct-invariant, `G`-preserving kernel can still support a conditional assay test. Genotype-dependent junction correction or merging across `G` can break this implication. A measured fit could then arise from the kernel itself, while a mismatch could arise despite a true physical local-action law.

If physical `G` cannot be authenticated, a reweighting law on the published corrected labels remains mathematically well-defined and potentially falsifiable as a reported-assay statistical restriction. It cannot answer the stated biological question about the intended versus aberrant RNA products, cannot attribute the donor action, and cannot support the drug-discovery usefulness claim made for that question. It would be a data-processing diagnostic or ordinary prediction exercise, not a substitute main candidate. This report retains the stronger question as incomplete rather than lowering its endpoint to obtain an easier positive result.

Nothing here requires the local-action law, discordant isoform channel, or predictive gain to be demonstrated before a falsifying test. Once the measurement contract is qualified, those are the objects of the frozen test, and a negative result is informative.

## Smallest discriminating test and same-information rivals

The first test is a **source/observation audit**, not a fit: the exact sequence-pair audit is complete; now identify uncorrected junction coordinates and qualify how all intended construct-by-condition observations, including zero-read and unmapped cases, enter a fixed outcome universe. The identity-only discriminator above can refute observability before numerical response exposure, although its passing is not by itself sufficient positive authentication.

If that succeeds, a frozen, bounded scientific test would evaluate the predicted fourth corner for all design-eligible pairs under one declared transfer task. No response-selected subset of visually attractive reversals is allowed. Source-context calibration failures, unidentifiable pairs, and abstentions remain in the full design-based denominator. A rule that abstains based on permitted calibration data must be fixed in advance and offered to rivals under the same conditions.

The decisive checks are:

- Whether edited and reference constructs preserve relative frequencies of products within each donor-use group.
- Whether the source-context donor-use odds shift transfers to the held target context.
- Whether the target reference joint distribution predicts the sign and magnitude of divergence between aggregate PSI and intended-product response, including any reversals.
- Whether a gain survives equally informed ordinary prediction, evaluated by family rather than by isoform rows or barcode instances.

Necessary rivals include a scalar mutation-scaling model from the closest prior, an unconstrained per-outcome multiplicative transport model using the same three profiles, a supervised ordinary nonlinear predictor receiving those same profiles and design/context information, and target-reference/no-edit-effect prediction. A scalar rival can be extended to a full-distribution forecast by preserving target-reference proportions within inclusion classes; it must not be deprived of the extra paid observations. The unrestricted transport rival is especially important: if it performs as well, there is no algorithmic novelty in the local-site restriction.

The paper's sequence-based XGBoost cluster predictor is a relevant prior but solves a different output task. An adapted comparison must use the allowed calibration information and avoid training targets or cluster labels derived from the held target responses.

Use outcome-count predictive likelihood and family-level error/calibration for the intended and aberrant fractions, with direction errors as a secondary measure. Coverage, missing products, and failure to identify the multiplier are part of the outcome. Read-count uncertainty is not biological replicate uncertainty; unreplicated drug cultures cannot establish reproducibility. The likelihood, tolerances, minimum useful effect, split, and rejection rules must be frozen under the root admission contract before any response access. This report does not pretend that these execution-specific quantities have been finalized.

Matching a scalar baseline but improving only a cosmetic score is not sufficient. A meaningful empirical advance would require correct previously unmeasured product allocation or correct prediction of a misleading aggregate response that an equally informed ordinary alternative does not achieve at the same information and resource budget. A successful constrained law can still be biologically informative if ordinary predictors tie, but that is evidence for the restriction's utility, not a unique new algorithm or molecular cause.

## Measurement and resource accounting

No assay-saving claim follows from masking existing MPRA response cells. The source measured pooled libraries, so an individual reporter profile is not an independent wet-lab assay whose cost can simply be subtracted. All three calibration profiles are paid observations. The complete original library and culture/sequencing work remain the actual retrospective acquisition cost, regardless of which labels a model sees.

A clean prospective causal test for `F` preselected families can use the two existing barcode sequences crossed with GT/GC at the fixed donor: four constructs per family. Pool those `4F` constructs and assay the complete pool in one reference and one target condition, with `R` independent biological cultures per condition and a frozen sequencing budget. This requires `2R` cultured library samples plus synthesis/cloning and sequencing for the `4F` constructs. In the target condition, both GC-barcode outcomes are computationally withheld until prediction; both matched GT-barcode outcomes and all reference-condition outcomes are available. Every rival receives exactly those observations.

This design separates the donor effect from barcode effects and avoids assigning all held target mutants to a different experimental batch. It does not save the cost of the validation experiment. A one-family version can falsify a strict universal law; general portability requires multiple independently held families. `F`, `R`, and the sequencing budget must be chosen from the actual precision and resource requirements, not retrospectively increased after a favorable pilot. No prospective assay was run or authorized by this report.

For future deployment, an acquisition saving would require a workflow in which the target-context reference library already exists and otherwise each new mutant panel would require additional construct/culture/read allocation. That saving must be demonstrated against ordinary three-corner predictors and the real pooled-library alternative. It is currently a conditional application, not a measured advantage or a justification for calling the reference measurements cheap.

## Critical eligibility unknowns

1. **Complete intended units.** A finite design list and exact GT/GC sequence-pair verification now exist, but family identity and the inclusion of every intended sample/construct must be closed. The source's native-row counts and nominal family description are not interchangeable.
2. **Physical donor coordinate.** Sec23 P4 reports moving observed splice sites to the maximum MaxEnt score within plus/minus three nucleotides. That score depends on the changed sequence. The meaning of the exported `_o` coordinate fields must be authenticated; their name alone does not prove that pre-correction junction positions are recoverable.
3. **Count denominator.** Sec23 filters aligned length, deletion count, start position, and more than three exons/two introns. Sec26 further excludes low-coverage observations and single-read isoforms in some analyses. Sec27 requires evidence of a cassette exon. Complete design IDs do not restore the mass of excluded products, unmapped reads, or no-assignment variants.
4. **Absent versus zero.** An absent isoform row can be an unobserved rare outcome, a filtered outcome, a mapping failure, or a true zero. It cannot silently become a biological impossibility. A test restricted to the exported selected-read distribution must say so and cannot be promoted to a full-transcript distribution claim.
5. **Nontrivial physical channel.** The required discordant products must actually be measured in the GT/GC pairs. If nearly all retained products have `G = Y`, the proposed result is old scalar scaling on a new dataset.
6. **Causal attribution and replication.** Barcodes differ within the existing pairs, and drug dose labels do not supply independent biological replication. These limitations affect both the mechanistic and generalization claims.

Root/investigator own the provenance audit. This report neither opens responses to resolve these questions nor treats the source's broad schema as sufficient execution eligibility.

## Material alternatives and stop conditions

**Promoter changes recruitment or timing directly.** This can produce the same three calibration profiles while changing the fourth, and can invalidate the invariant local action. A context-dependent statistical correction could improve forecasts, but adding it without a measured physical discriminator would turn the candidate into ordinary conditional prediction. The proper next step would be to obtain the discriminating channel, not declare a discovered recruitment mechanism.

**Splicing-history dependence.** The source-owned weak-donor/upstream-intron interaction motivates a question about whether prior splicing alters later recognition. That remains a distinct, incomplete causal question. It needs temporal or nascent observations and a controlled history manipulation. The current mature RNA table cannot resolve it, and repeating the source's added-intron rescue is not a new contribution.

**Promoter-dependent donor-acceptor cooperation.** Matched donor-only, acceptor-only, and double-edit rectangles could test whether context changes a cooperative exon-recognition relation rather than only marginal site preferences. Root's complete typed census instead contains endogenous/endogenous, constitutive/constitutive, constitutive/GC, and unsplicable/unsplicable in 72 families each, plus constBP/endogenous in 71. It does not authenticate a clean donor-only/acceptor-only/double-edit rectangle. Classical epistasis mathematics would be inherited in any case; no new cooperation claim is made without the required intervention design.

**Kinetic-window transfer.** Modeling the drug as a scalar change in an unmeasured transcription window would only exchange one link function for another. The drugs have multiple actions, and initiation, elongation, recruitment, and stability are not separated by these mature endpoints. A physically measured timing channel would be required to develop this line beyond an unsupported latent-rate interpretation.

Stop the current version as a main idea if physical junction identity or the observation denominator cannot be qualified; if the paired intervention cannot support the stated construct-level interpretation; if the necessary joint-isoform channel collapses to PSI; if the local-action invariants fail materially; or if all useful predictive behavior is accounted for by the closest scalar law or equally informed ordinary transport without a new empirical finding. A failure would refute this restriction under the tested assay, not all RNA-context learning.

The smallest justified next action is the remaining identity/processing provenance check. If that passes, the next scientific decision is whether a frozen full-outcome test can distinguish portable site action from context-dependent action on the actual designed construct pairs. No new fitting, method stack, or core promotion is justified merely because the hypothesis is now concrete.
