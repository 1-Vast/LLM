# Independent initial assessment of conditional splice-choice transport v1

Recorded 2026-10-31 before receiving a coordinator rebuttal or reading developer interpretation, root synthesis/decision, investigator interpretation, or scout handoff. Inputs were the frozen `choice_transport_question_v1.md`, `choice_question_freeze.json`, original papers, metadata-only records, and inert historical code. Requested role/configuration: fresh independent challenger, Sol/high; effective model and effort are not confirmed by runtime metadata. No agent was spawned.

## Finding

The question has a legitimate, falsifiable biological content: does a specified regulatory intervention preserve the relative effect of a drug across a fixed local set of splice choices, sufficiently well to predict the missing treated combination? The distributional output could be useful for molecular selectivity work. The formula itself is a standard odds-transport restriction, with no new learning principle. The potentially valuable result would be an independently justified intervention class and a prospective domain of validity, with measurement costs included.

Neither that eligibility class nor an authenticated observation universe is currently established. U1C depletion is an especially adverse example because the paper directly implicates U1C in drug-compatible conformations and reports context-dependent loss and unmasking of responses. Those findings challenge broad invariance; they do not logically refute every conditional local-choice instance. There is no numerical experiment admitted now. This is an informative scientific question with unresolved feasibility and importance, rather than a supported recommendation to build a new Virtual Cell learner.

## Ordinary equivalence and what actually has to be learned

Choose any supported reference choice r. The proposed rule is exactly

`log(q'_j/q'_r) - log(q_j/q_r) = log(p'_j/p'_r) - log(p_j/p_r)`.

For J choices there are J-1 independent transported contrasts. This is an ordinary multinomial logit model with background-specific baseline logits and a shared drug coefficient for each choice. In a positive choice-by-background-by-treatment contingency table it also corresponds to the absence of the three-way interaction, while retaining the pairwise terms. This equivalence is an algebraic deduction, not a claim that a particular published splice paper already performed this exact prospective experiment.

Every positive source pair determines the factors up to a common multiplier. Source reconstruction therefore cannot support transport. Predicting A differently when its own baseline is unchanged but competing T changes is a valid consequence of the full denominator. It establishes information missing from an isolated-exon input; it does not establish an advantage over an ordinary model given the full vector. An exact shared multinomial comparator must make identical point predictions. Performance against it can only differ through estimation, regularization, measurement treatment, or an altered restriction.

Ishigami2024, DOI 10.1038/s41467-024-46090-5, Sec6, is close prior at the level of the central biological separation: the drug-effect model assumes drug effect E depends on the 5' splice-site sequence but not other locus-specific context-strength factors S. The authors also explicitly report statistically significant deviations for some exons, showing that outside context sometimes changes E. Sec8 adds sequence-dependent drug-binding energies and two modeled branaplam interaction modes. Sec11 shows why baseline/context strength can explain EC50 changes without altered drug cooperativity. Thus baseline/drug-effect separation is established prior, including known exceptions. V1's possible difference is an explicitly multichoice, held-out regulatory-combination question. No inspected source establishes that this is an unprecedented question, and no comprehensive absence-of-prior search was performed.

## Source-located objections

### T1. The intervention eligibility rule carries the contribution and remains missing

Affected claim: transport to an unmeasured regulatory combination while preserving relative drug multipliers.

U1C2026, DOI 10.1038/s41467-026-74765-8, Sec11, reports reduced maximal responses, right-shifted responses, substantial or complete response loss, and exons with drug activity enhanced upon U1C knockdown. Effects can be compound specific. Sec12, especially paragraphs 6-9, relates this to drug-compatible conformations and additional cellular factors. Unchanged sequence preferences or preserved rankings of the most potent exons are weaker statements than unchanged relative multipliers at a fixed dose.

These are good reasons not to treat U1C depletion as a baseline-only intervention by default. Conversely, an EC-dPSI30 shift alone is not a direct test of v1: with a nonlinear probability readout, a baseline shift can change a dose threshold without changing the local odds effect. The multidose aggregate findings do not supply the exact positive multichoice observations required here. The decisive missing object is an intervention/choice eligibility rule specified without target treated responses, not another model component. Selecting a subset because its withheld response obeyed the rule would remove the prospective empirical content.

Resolution requires independent biological justification of eligibility, followed by held-out predictions. A failure in the U1C panel would reject that application or rule; it would not disprove the existence of another valid regulatory class.

### T2. The measured object has not yet been authenticated

Affected claim: a full local multichoice distribution with a common biological denominator, rather than overlapping event margins.

U1C Sec28 says that DEDSeq, with minor modifications, uses junction reads and computes inclusion/exclusion PSI; biological replicate PSI values are averaged. It does not say that its published event rows are complete multinomial branch distributions. Historical `root/sources/dedseq-06-ana-exon-PSI.R`, lines 214-215, does build shared-site adjacency lists. Lines 278-320 construct potentially multiple skipping junctions. Lines 357-361 sum upstream/downstream inclusion support, halve the sum for exon events, and divide by inclusion plus exclusion support. These event margins cannot simply be stacked and normalized into exclusive branches.

Historical `dedseq-01-combine-junction.R`, lines 52-66, unions observed sample junctions, fills missing sample counts with zero, and filters by total support across samples. This is evidence of a possible observation-dependent discovery/filter path, not proof of the exact 2026 export settings. Its 2021 provenance and unknown paper-specific modifications materially limit inference. No author code was executed.

The metadata audit authenticates 48 sample columns, not junction identities, complete branch sets, count support, strand/gene disambiguation, or biological closure. An identity-only graph projection could answer a narrower useful question: whether the export contains unambiguously identified common-anchor groups with at least three distinct observed alternatives. It cannot by itself establish sufficient source support, absence of unobserved branches, independent biological replication quality, or the eligibility rule.

Full transcript reconstruction is not automatically necessary for a clearly defined conditional distribution over junctions sharing an anchor. A stable observed subset may also support a conditional estimand. However, that estimand must be named accurately; a conditional vector over observed junctions is not the entire distribution of molecular fates. Treatment-dependent detection or filtering can make the apparent branch universe response selected. The observation contract must resolve this before response analysis.

### T3. Baseline competition and drug action are not identified mechanistically by endpoint fractions

Affected claim: changes in competitive weights preserve a mechanistically meaningful drug effect.

Ishigami Sec6 assumes equilibrium U1 occupancy maps to PSI. Its Sec11 explicitly shows that several model parameters can shift EC50. U1C Sec12 considers multiple conformational explanations and retains uncertainty about suppression and risdiplam factors. Endpoint odds invariance would be compatible with an effective phenomenological law; it would not identify binding affinity, association/dissociation rates, a unique molecular interaction mode, or a causal drug-binding mechanism.

Lenkeit2026, DOI 10.1038/s41467-026-74594-9, Sec3, shows that gene expression strongly affects which inducible exons are observed. Its NMD experiments argue against degradation explaining most absent AGA targets in that particular setting; they do not eliminate degradation or transcript-mixture effects for every proposed choice set. Common gene-expression scaling would cancel from a genuine within-anchor conditional fraction, so gene expression alone is not a generic refutation. Branch-specific production, survival, assay efficiencies, or changing latent transcript/cell mixtures can change observed odds.

Resolution requires matching the scientific claim to the actual measurement. If the claim is prediction of mature-RNA junction-use frequencies, these processes may be part of the effective response. A stronger claim about primary splice competition needs additional evidence. V1 should not inherit that stronger mechanism from the formula.

### T4. Existing U1 perturbation studies make the conceptual difference narrower

Affected claim: usefulness or novelty of predicting combination-induced exon redistribution.

Lenkeit Sec4 directly changes U1 complementarity using U1-G6C7, assays drug combinations in biological triplicates, and identifies exons induced only or more strongly in the altered U1 background. The stated experimental intent was to change complementarity while leaving the small-molecule binding site unchanged. This is close biological territory. It does not prove invariant response factors: leaving the nominal local binding site unchanged need not preserve all conformational or kinetic effects.

Lenkeit Sec16 discovers novel exons using sample junction support and requires support in a fraction of experiment samples. Sec21 trains XGBoost inducibility classifiers with five-fold stratified cross-validation. Thus neither its discovery universe nor its classifier evaluation automatically supplies a prospective held-out regulatory-combination test with v1's available measurements. The valid distinction would be that particular prediction and eligibility contract, not merely using U1 context, baseline inclusion, or a full vector.

Resolution requires a precise closest-prior comparison at the eventual task definition. The current sources suffice to reject an assertion that the broad biological combination question or baseline/context separation is new. They do not settle whether the exact multichoice transport application has already been tested elsewhere.

### T5. Economy and useful output remain hypotheses

Affected claim: useful, economical Virtual Cell learning for drug discovery.

The team must already measure source untreated, source treated, and target untreated distributions for the same choices. Source cost may amortize over multiple target combinations, and target untreated assays may already exist. Neither saving is yet established. If obtaining target untreated data costs as much as obtaining the target treated endpoint, the practical advantage can be small unless the source information is reused at scale or untreated measurements serve other workflow purposes.

The plausible user is a splice-modulator R&D team prioritizing molecular selectivity experiments. Full redistribution could expose unwanted alternate splice choices that a single target-exon margin misses. Yet predicting a local conditional fraction does not determine absolute transcript production, protein function, toxicity, or therapeutic response. Reliable selectivity benefit also requires calibrated uncertainty, especially when source baseline probabilities are very small. A finite read-count zero is not a verified biological zero, and arbitrary pseudocount choices can dominate estimated ratios.

Resolution requires a concrete assay-selection use case and a cost-matched ordinary alternative with the same paid inputs. No agent-specific mechanism or benefit is implicated by v1.

### T6. An ordinal reversal test is not a replacement for testing multichoice transport

Affected claim: inference drawn from the scalar donor literature.

Carlson2025, DOI 10.1073/pnas.2509444122, introduces a monotone function of a single additive latent trait and derives preservation of mutation ordering across backgrounds. Its “Model Misspecification” and Discussion passages explicitly warn that additional latent traits can yield spurious inference of specific epistasis. Crona2017, DOI 10.7554/eLife.28629, Introduction, already defines sign epistasis as a background-dependent change in the sign of an effect and connects it to ordinal incompatibility with additivity.

A credible within-exon drug-order reversal can reject a shared monotone scalar-additive representation under its assumptions. It does not establish a direct molecular contact or identify the replacement dimension. Conversely, v1's multichoice transport can fail without an ordinal reversal. With multiple non-reference multipliers, an aggregated exon margin can change because competitors and the normalization change, even when all branch-specific relative drug factors remain invariant. Thus scalar ordinal failure and vector-transport failure are separate claims and need distinct nulls. DMS Poisson resampling is not justified for this biological-replicate RNA design merely by citing the donor.

## Smallest useful next check and experiment admission

The smallest currently useful check is observation qualification, not a fit: establish from authenticated junction identities, assembly/strand conventions, provenance and filtering information whether a prespecified observable common-anchor choice set can be constructed. An exact identity-only projection is potentially informative if separately admitted. It should report ambiguity and selection provenance, retain the same v1 question, and leave count values inaccessible. Its success would establish only graph-level feasibility. It would not establish count support or drug-factor invariance.

After an independently justified eligibility rule and a complete numerical protocol exist, the smallest direct scientific falsification is one independently withheld, eligible target treated vector at one fixed drug/dose/endpoint, predicted entirely from source untreated/treated and target untreated measurements. The comparison must assess the J-1 relative-log-odds restrictions with biological-sample uncertainty and shared-baseline covariance. It must allow an inconclusive outcome when support or replication is inadequate. One credible failure can refute that specific application; one success cannot establish a transferable intervention family, savings, or new learner advantage. Those require broader independent eligible combinations and a cost-matched decision comparison.

The exact shared multinomial model is the scientific null/equivalent implementation, not a rival that v1 should be expected to outperform. A flexible predictor with the same inputs addresses whether the restriction provides a useful bias. An isolated-exon predictor only addresses the value of omitted competitor information. Source self-fit, treatment-selected examples and nominally large numbers of exon rows cannot substitute for independent held-out combinations or biological samples.

No numerical response analysis is permitted by the existing freeze. Missing items include the authenticated eligible universe, support/zero rule, held-out unit, treatment of noise and denominator covariance, measurement/training costs, analysis choices, comparison criteria and stop rules. Data access uncertainty is not a negative biological result. The evidence currently supports completing those prerequisite decisions or parking the line, not constructing a more elaborate learner.

## Actual reading and resource use

- Frozen candidate and freeze JSON read. No protected response records, gzip count rows or XLSX response rows opened or projected.
- U1C original XML: Sec11, Sec12 and Sec28 read; bounded rereads recovered the truncated Sec12 tail and Sec28. No reliance on the missing middle of a truncated tool return.
- Ishigami original XML: Sec6, Sec8 and Sec11 read. Supplementary derivations were not inspected; the assessment relies on the explicit main-text assumptions and results.
- Lenkeit original XML: Sec3, Sec4, Sec16 and Sec21 read; section titles mapped. Other results sections, supplementary response tables and author repository were not inspected.
- Carlson original XML: abstract, original monotone single-trait/rank passages, rank/noise discussion, model-misspecification and Discussion passages read. Crona original XML: Introduction/sign-epistasis and selected mathematical passages read. An overbroad first extraction also exposed some eLife reviewer text, which was not used as original-paper evidence. No scout interpretation or handoff was read.
- Metadata: `u1c_dose_schema.json` first-row/header information inspected in part, including the PSI condition headers; `junction_header_audit.json` read in full; GEO metadata projection inspected for sample mapping and protocol fields; raw Series summary/design and selected raw sample title/characteristic fields checked. The projection contains 57 Series samples; the dose panel is the matched 48-column subset, not all Series records. Some broad tool returns were truncated; no claim of complete metadata/code-file reading is made.
- Inert code: load-bearing source portions of historical DEDSeq 01 and 06 read with line-numbered targeted extraction. DEDSeq 02, full tree and commit JSON were not independently inspected; their stated provenance remains a supplied limitation rather than newly authenticated evidence.
- Independent HTTP searches/acquisitions: 0 attempts, 0 bytes; no fresh prior-absence claim. No budget pass was consumed through HTTP. Local parsing/search only; no model calls, fits, simulations, author-code execution, installs, weights, commits, uploads, shared index edits or writes outside `challenge/`.

No new HTTP search was needed to decide numerical admission or the exact ordinary equivalence. A future claim that this exact multichoice application is new would need a targeted current prior search; this review makes no such claim. Effective runtime configuration remains unknown.
