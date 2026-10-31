# Mechanism development: a concrete partial opening, not a new learner

2026-10-31. Requested Astra/MAX; effective runtime model/effort metadata unavailable. Mechanism researcher, not independent reviewer. `initial_mechanism_framing.md` was saved before reading the scout handoff. No response/count/PSI records, notebook outputs, fits, simulations, author-code execution, external model calls, HTTP requests, installs or weights were used. Writes were confined to `developer/`.

## Decision and concise hypothesis

**No developed Virtual Cell learning recommendation survives the present evidence and prior comparison.** There is a concrete, incomplete opening: distinguish a change in *competition between splice choices* from a change in a drug's effective action on a choice. The former can create predictable effects on another choice without changing that choice's local drug-recognition sequence. The latter is already central to the U1C paper and need not obey the same transport rule.

The conditional hypothesis worth preserving is: **within a fixed, fully observed set of mutually exclusive splice choices, a regulatory change that only changes their baseline competitive weights preserves their relative drug multipliers, allowing source drug responses and target untreated choice frequencies to predict the entire unmeasured treated distribution.** This is an untested biological restriction implemented by ordinary multinomial reweighting. Its applicability to U1C depletion is unknown and particularly questionable. It is not a recommendation to fit the acquired table.

The constructive step still missing is a way to specify and support, independently of the withheld drug responses, **which regulatory changes and splice-choice sets preserve those relative multipliers**. Letting every event/context acquire its own drug multiplier removes the restriction and its predictive content. Baseline controls, local motifs and one U1C knockdown do not currently supply that eligibility rule.

## Parent premise, changed object and source ownership

The parent question asks for unmeasured exon/regulatory-context consequences beyond ordinary baseline/context-strength and flexible equal-information prediction. I considered changing the predictive object from an isolated binary exon-inclusion margin to a joint, local set of mutually exclusive choices. This is a different question, not evidence that the papers incorrectly ignored competition.

| Original source, directly read | What belongs to the source | What it does not establish for this proposal |
|---|---|---|
| Lenkeit, DOI `10.1038/s41467-026-74594-9`, XML nodes 797, 834, 904, 918, 1060, 1104, 1228, 1250, 1279, 1303, 1343 | U1 complementarity and bulge-compatible structure, changing responsive exon sets through U1 mutations, local/regulatory sequence and baseline PSI in XGBoost; residual context effects | A new joint-choice transport law or an independent test of it. Structural compensation and U1-mutant-by-drug effects are not our discoveries. |
| U1C2026, DOI `10.1038/s41467-026-74765-8`, nodes 296, 392, 439, 455, 538, 549, 594, 601, 683–706 | U1C/Helix-H dependence in the branaplam binding preparation; risdiplam's inactivity in that preparation; knockdown-by-dose effects, reduced attainable responses, dose shifts and newly unmasked targets; proposed conformational explanations | Which endpoint changes are due to local drug-compatible complexes, competing splice choices, exposure, or other factors. Node 703 expressly leaves the class-III suppression mechanism unresolved. |
| Ishigami2024, DOI `10.1038/s41467-024-46090-5`, nodes 282, 319, 332, 405, 697, 754, 926, 932, 950 | Allelic-manifold separation of sequence-specific drug effect E from locus context strength S; an explicit assumption that E is independent of other context factors; reported exceptions to that assumption; two proposed branaplam interaction modes; context-strength explanations for dose shifts | Novelty for merely transporting an exon-specific drug effect, introducing two latent modes, or interpreting a dose shift as changed affinity. Kinetic proofreading is a source hypothesis, not an identified rate mechanism. |

In particular, Ishigami nodes 319–332 are a stronger prior than a generic baseline regression: the original already estimates shared drug effects for identical splice-site sequences across genomic contexts and reports deviations caused by context outside the local site. The proposed opening must therefore concern an additional, jointly testable choice relation, not rename context-independent E.

## Constructive case and exact ordinary equivalence

The following is a symbolic thought experiment, not data or a simulation. Consider genuinely mutually exclusive donor choices at one common downstream acceptor. Let `p_j` be the untreated choice probabilities in a source background, `p'_j` the probabilities after a specified drug/dose, and `q_j` the untreated probabilities after a regulatory change. All probabilities refer to the same closed local choice set. They are not arbitrary cassette-exon PSIs summed across a gene.

Assume drug exposure multiplies the productive weight of each choice by a factor `a_j`, and the *relative* factors remain the same across these two backgrounds. Then

`q'_j = a_j q_j / sum_k(a_k q_k)`.

For supported nonzero source probabilities, the source measurements determine `a_j` proportional to `p'_j / p_j`; a common scaling factor cancels. Thus the law makes a definite unmeasured-context prediction without observing the target treated distribution. It does not require a new learning architecture.

A minimal example with an additional joint prediction has a drug-responsive choice T and two alternatives A and B. Suppose the drug multiplies T by `lambda`, while A and B share the reference factor. Then

`q'_T = lambda q_T / [1 + (lambda - 1) q_T]`,

`q'_A / q_A = q'_B / q_B = 1 / [1 + (lambda - 1) q_T]`,

and `q'_A / q'_B = q_A / q_B`.

Two backgrounds can have the same untreated abundance of A but different untreated abundance of T. The rule then predicts different drug-associated suppression of A, although A's own baseline and local recognition sequence are unchanged. This is the concrete useful opening: a measured change in a competing choice can predict an otherwise unmeasured consequence. It would help an RNA-drug team anticipate redistribution among alternative junctions at a locus when prioritizing selectivity experiments. This practical benefit is proposed, not observed.

The reductions are decisive:

- With T versus one aggregated alternative, the first equation is exactly ordinary odds/context-strength transport: `logit(q'_T) = logit(q_T) + log(lambda)`. This supplies no new mechanism beyond the closest prior.
- For a full choice vector, the rule is exactly a multinomial model with context-independent drug changes in pairwise log odds, or ordinary compositional/density-ratio reweighting. It is closely related to the independence-of-irrelevant-alternatives restriction. Probability conservation alone does **not** imply this restriction.
- Any positive source untreated/treated pair admits such a vector of factors. Fitting the source pair therefore cannot validate the law. Its empirical content is that the same relative factors predict the withheld context.
- An equally informed flexible ordinary predictor can receive all competing-choice baselines, local sequences and source responses and can learn this relation too. A gain over an isolated-exon predictor would not establish superiority over that comparator. A confirmed biological regularity could still matter with an ordinary implementation, but only if its applicable intervention class and out-of-context predictions are supported.

This construction predicts a new **combination for a previously measured choice set**. It does not predict a completely unseen exon from sequence alone: its source drug response is an input. It does not predict an unseen compound or an unmeasured exposure without an additional, separately justified relation.

## Counterexample, identification and meaningful rivals

An explicit counterexample is the same set with `a_T` changed by U1C depletion because the target's drug-compatible U1 complex changes, while all untreated target probabilities remain compatible with the measured controls. The held treated distribution then differs from the transported prediction. The U1C biochemical results make this possibility biologically substantive. Alternatively, a second choice may itself become drug-responsive in the changed background; the A:B ratio then need not be preserved.

More generally, for any positive target treated distribution `r_j`, choosing context-specific factors proportional to `r_j / q_j` reproduces it. Therefore source responses plus target untreated frequencies cannot identify the target response without an invariant-factor assumption. This is an information limit, not a missing neural architecture. Zero or unsupported source probabilities also prevent estimation of the corresponding multiplier; replacing absent rows with zero or adding arbitrary pseudocounts does not restore identification.

The main biological rivals are:

1. **Direct change of the drug-compatible U1 complex.** U1C changes conformer availability or productive recognition at the target. This is source-motivated, but endpoint curves do not identify a conformer population, affinity, association/dissociation rate or U1-to-U6 transition rate. Adding a latent state without an independent observable is not progress.
2. **Ordinary isolated-event context strength.** Baseline inclusion changes with a fixed effective drug effect. This is the exact binary equivalent and must be retained; a different raw delta PSI or conventional EC50 is not evidence against it.
3. **Joint competition with stable relative drug action.** This is the conditional opening above. Its additional predictions concern a full local choice vector. It becomes ordinary flexible interaction regression if the relative factors are allowed to vary freely by context.
4. **U1 stabilization versus productive handoff.** Excessive stabilization might impede later splicing steps; U1C2026 node 703 and Ishigami node 950 already discuss related possibilities. Endpoint inclusion cannot identify a kinetic window. New residence/transition or appropriate time-resolved measurements would be necessary for that mechanistic claim; no such input is authenticated here.
5. **Observation changes.** Treatment-dependent discovery, mapping/support, transcript production and isoform-selective decay can change mature-RNA proportions without the proposed productive-choice law. Source decay perturbations do not eliminate every such explanation in another study/background.

Under the stated measurement assumptions, relative effective multipliers can be estimated from a supported joint source distribution and tested for transfer. Their common absolute scale, molecular binding parameters, reaction rates and cause of invariance remain unidentified. A successful endpoint prediction establishes an effective response relation, not molecular mechanism or clinical benefit.

## Inputs, cost, timing and actual resource limit

At use time, this conditional rule needs all of the following:

- A fixed human locus and authenticated mutually exclusive choice set with a common denominator, defined without looking at the held treatment responses. A common-acceptor junction set may support a *local* choice distribution without full transcript phasing; arbitrary cassette-event margins cannot. A local junction set is not automatically a complete full-transcript path set.
- Matched source vehicle and drug measurements at the declared compound, exposure and endpoint for every relevant choice, with biological replicate identity and read support; target-background untreated measurements of the same choices are also required. These are real measurement costs. It is not a sequence-only or zero-measurement prediction.
- Consistent mapping and strand/coordinates; sufficient untreated/source support to estimate the needed ratios; a treatment-independent reference or a carefully limited independently supported event universe; uncertainty that respects samples and shared junctions rather than counting every exon as an independent experiment.
- A supported intervention class in which relative effective drug factors can be transported; comparable cellular exposure and measurement process; and either stable transcript survival or an explicit restriction of the output to measured mature-RNA composition. Motif compatibility alone does not certify these assumptions.

The available U1C study uses a regulator treatment before drug exposure and a 24-hour drug endpoint. Its paper specifies different dose series for the two compounds. Those conditions cannot be pooled as equal exposure, equilibrium binding or independent cross-study replication. Root reports HEK293 versus HEK293T and dose-unit typography discrepancies between GEO metadata and the paper; these remain provenance issues to resolve before a quantitative protocol. No new timing, replicate allocation or decision threshold is proposed here.

I directly read the safe `root/u1c_dose_schema.json`: one sheet contains 22 **condition-level** PSI headers, not explicitly replicate-numbered PSI fields. Identities, sequences and derived comparison fields do not certify a complete universe or independent units. The workbook itself was not opened. Root subsequently reports complete acquisition of the separate junction-count gzip and exact header matching to 48 drug-experiment sample labels; that is a new access fact, not inspection of its response values or verification of local choice support.

The root-authorized inert DEDSeq reading provides a relevant limit. At pinned commit `9181a015163354c015485fba3e0c3a153b7ae0d8`, `06-ana-exon-PSI.R` lines 214–248 aggregates junctions sharing sites, lines 251–334 constructs exon-skipping sets, and lines 357–360 forms a binary PSI margin from inclusion/exclusion aggregates. These event margins do not certify multibranch molecule choices. The historical code also limits the skipping-junction set through `max_skip_juns` (lines 307–310). `01-combine-junction.R` lines 44–66 unions sample-observed junctions, zero-fills missing counts and filters using pooled support. These are inspected historical defaults, not authenticated paper-specific modifications. The newly available junction table could permit a separate local graph/support qualification, but the existing processing does not establish the required observation contract by itself.

## Smallest decisive planned test and stopping point

The first useful check is structural, before outcomes: determine whether an independently supported human common-acceptor set with enough alternative donor choices for the joint prediction exists in the admitted identities and whether its count denominator can be reconstructed without outcome-derived omissions. If only binary margins or an unknown selected universe can be authenticated, the proposed additional prediction is unavailable. No fit is needed to reach that conclusion.

If a suitable set is authenticated and a separately reviewed experiment is authorized, freeze the source-factor rule using source vehicle/drug measurements and target vehicle measurements; withhold the complete target treated choice vector. Predict that vector, including the relative change of the non-target alternatives, without target-response-dependent factor adjustment. Compare the identical shared-multinomial equivalent, the source-owned isolated-event context model, and a flexible ordinary predictor given the same choice-set information. A comparison against the identical equivalent cannot establish method novelty. A held drug/dose/background observation is the unit of condition generalization; many junctions within the same treated sample do not create many independently tested regulatory contexts.

For **biological attribution**, the most discriminating follow-up would selectively alter a competitor while leaving the target recognition sequence unchanged, rather than relying only on U1C depletion, which acts directly on the relevant complex. The conditional hypothesis predicts transported relative drug factors and the resulting joint redistribution after that competitor change. A reproducible failure rejects the restriction for that intervention class; successful prediction is consistency evidence and must be checked against exposure and RNA-survival alternatives. The selective perturbation is a proposed additional human-RNA experiment, not an available authenticated resource, authorization to perform it, or a reopening of the closed ASO task. No protocol thresholds or success claims are supplied.

The scout's rank/sign-reversal idea can reject a shared scalar monotone explanation, but it does not select among these rivals or identify the missing transport rule. Its donor mathematics and novelty were not independently re-audited in this role. No crossover was measured here.

**Preserved opening:** joint splice-choice redistribution could expose a useful biological restriction beyond a single-exon curve. **Unsolved step:** justify and test the intervention class that preserves the relevant relative drug action, with an authenticated joint observation. The current U1C resource improves access to response measurements but does not supply that law. The strongest novelty threat is already-existing context-strength transport plus ordinary competitive/multinomial splicing models; no target-field novelty claim follows from this local, no-HTTP development pass. There is therefore no recommendation to run a numerical learner merely because the table is now available.

## Reading and exposure record

Original files: `reference/papers/doi-10.1038-s41467-026-74594-9/supp-scsp_fulltext.xml`; episode `investigator/sources/u1c2026.xml`; episode `investigator/sources/ishigami2024.xml`. XML node numbers are zero-based document-order traversal positions, matching the investigator's locators. Original mechanistic Results, relevant Discussion and U1C processing/timing Methods were read; scientific mathematical supplements were not. Published aggregate outcomes in those paper passages were necessarily encountered as literature, never projected from a response dataset.

Other reads: episode `record.md`, `root/initial_questions.md`, `investigator/source_findings.md`, the schema/inspection contract, the two explicitly authorized inert DEDSeq files, and `scout/handoff.md` after freezing the initial framing. The innovation-research idea-development and scientific-significance guidance informed the constructive case, equivalence and stopping decision. This development note is not fresh independent review.
