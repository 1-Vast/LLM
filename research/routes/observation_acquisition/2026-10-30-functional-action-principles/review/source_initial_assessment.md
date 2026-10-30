# Independent source-evidence challenge — initial assessment

Date: 2026-10-30. Scope: claim-specific factual checking of `target/evidence.md` and `scout/evidence.md` against the supplied originals. This is not a candidate review, independent biological validation, novelty clearance, or a recommendation among unseen developer candidates. No preferred candidate or desired verdict was provided.

## Assessment

The four requested evidential boundaries are substantially supported. The originals restrict the strength and unit of the claims; they do not establish that average-signature prediction, tests conditioned on a selected response panel, pooled-population prediction, or predictive-state reasoning are useless. No material reversal of those boundaries is warranted from the passages read. One bibliographic omission should be corrected, and several enabling interpretations deserve explicit preservation.

### 1. CPgenes averaging restricts pairing claims while allowing an average-signature target

**Original locators:** `target/multivcdiff.xml`, paragraph IDs p0305, p0310, p0165, p0415; held-out readouts p0070, p0105, p0115; inference inputs p0155.

p0310 says that all corresponding L1000 expression profiles are averaged to obtain one representative vector per chemical compound or genetic target, and that this vector is assigned to every associated morphology sample. p0305 identifies the morphology contexts as MCF7, U2OS, and A549 across the respective resources. p0165 states static endpoint prediction and no explicit dose or combination encoding.

This directly supports the packet's warning: many images sharing one RNA label are not evidence of single-cell co-measured RNA/image pairs or of the RNA distribution conditional on the particular imaged cell. The inspected construction also does not specify a matched context/dose/time/replicate join. It therefore does not establish those matched units. **It does not establish that all retrieved RNA necessarily mixes different cell backgrounds, doses, or times either.** “All corresponding” leaves upstream retrieval/filtering scope unspecified in this paragraph. The appropriate status for those matching fields is unverified, not proven mismatched in every instance.

The same construction defines a legitimate supervised target: the perturbation-level RNA average used by this corpus. Image and structural information can, in principle, help predict that average. p0115 explicitly describes comparison against RNA logFC for 30 held-out compounds; p0070/p0105 instead concern 54 held-out compounds without RNA matches and a morphology readout. Those are source-reported assessments under different contracts, not a reproduced result here. Their existence supports preserving the possibility of predictive utility without promoting it to dose/context-specific paired biology or functional efficacy. p0415's RNA sample unit is distinct perturbation conditions; its generated-image counts cannot be counted as new biological assay replicates.

### 2. Response-informed selection changes the tested population; it does not invalidate every conditioned test

**Original locator:** `target/comparison.xml`, root.iter() zero-based element 1157, “Datasets and preprocessing.”

The original explicitly says TRADE transcriptome-wide impact scores were computed and the top five and bottom five ranked conditions retained for Srivatsan, Burkhardt, Tahoe, Parse Biosciences, and both in-house datasets. This is response-informed selection, not merely a random sample of a drug universe. Treating the released retained subset as an untouched prospective screen universe would need additional justification.

The packet's wording “NOT automatically representative” is appropriate. Selection does **not** alone rule out prediction/evaluation conditional on the selected conditions, an explicitly declared closed-pool experiment, or a prospective test with independently acquired later outcomes. Such tests answer their stated conditional question; they do not automatically estimate performance across the unscreened drug population or savings from discovering previously unknown high-response drugs. Whether a particular design leaks information depends on what selection information and outcomes it uses, not merely on the existence of the selection paragraph.

The original also names broader upstream resources. It does not say that the retained files exhaust the available source data, that every released object has exactly the inferred schema/coverage, or that no suitable broader pool can be constructed. Those are separate unresolved access/schema/design questions. No release data were opened here.

### 3. Donor pooling justifies unknown independence/retention, not a blanket absence of replication

**Original locators:** `target/comparison.xml`, elements 1118, 1124, 1127, 1130; general limitation element 1096.

KHP cultures use HDFs and PBMCs from the same two donors (1118). Its multiplexing procedure mixes the two donors treated with the same drug before oligo incubation; it prepares two pooled samples each for K562, HDFs, and PBMCs (1130). cmo culture text mentions frozen PBMCs from **three healthy donors**, then says cells from **two vials originating from two donors** were mixed before seeding (1124). The text does not resolve the full allocation of all donors across experiments. cmo uses 111 drugs at 1 micromolar with DMSO controls and four-day treatment (1124/1127); 16 multiplexed pools contain eight treatment groups per sample (1130).

These details do not demonstrate independently retained donor-resolved replicates in the released objects. They also do not prove their absence: donor identity might be recoverable through other metadata/genotype processing, and distinct culture/well/experiment replication cannot be inferred solely from sequencing-pool counts. Pool/library counts and cell counts are not, by themselves, counts of independent treatment replicates. The packet correctly leaves release-level donor identity and independent replicate structure unknown.

A pooled-population response target may remain usable, conditional on the actual experimental units and compatible question. Generalization to unseen donors, independent donor-level validation, and uncertainty calibrated across biological experiments require more information. Element 1096's broad call for sufficient replication is a benchmark limitation statement; it is not proof that each particular dataset has zero biological replication.

### 4. Original PSR provides predictive representation and model-based construction, not sparse-data learning/control

**Original locator:** `root/request03_predictive_state_original.body`, read through its supplied `request03_predictive_state_original.txt` extraction. Locators below use the extraction's PDF file page numbers.

- pp. 3/5: a PSR is sufficient to determine predictions for all possible action-observation tests. A chosen finite outcome panel without an additional sufficiency argument gives a restricted task representation, not this exact guarantee.
- p. 5: discrete action and observation sets; explicit statement, “We consider only predicting the system, not controlling it,” with no designated reward observation.
- p. 7, Eqs. 1–3 and Theorem 1: linearity concerns the projection from state to test probability. The update is a normalized conditional-probability ratio. The existence/size theorem is for environments representable by a finite POMDP.
- pp. 7/9/11, Section 2: polynomial construction starts with a supplied POMDP, uses hidden-state outcome vectors, tests their linear independence, and constructs projection vectors. This is constructive predictive equivalence under the stated model, not an empirical algorithm or sample-complexity guarantee for discovering a sufficient state from sparse public cell-response data.
- p. 11, Section 3 **Conclusion**, “Learnability”: simple counting for PSRs remains an open question; the multiple-action case conditions outcomes on behavior and violates some required independence assumptions. Other advantages are explicitly left for future work.
- pp. 3/5, float/reset: the example distinguishes exact unbounded-memory representation from any fixed finite history. Its two-test informational representation requires a nonlinear update; the later linear construction has five tests (p. 9). It does not show superiority over a full-history dynamic predictor in drug data.

Thus the scout's main restriction is supported. The paper does provide an exact prediction-equivalence theorem and explicit update/construction, so it should not be reduced to a mere metaphor or an unproved sufficiency proposal. Conversely it does not supply the cheap-data estimator, empirical biological sufficiency, reward/utility specification, control policy, or experimental savings being sought in the target application. A zero-probability conditioning denominator is outside the defined conditional update; instability with small estimated denominators is a reasonable later statistical concern, explicitly an inference rather than a measured finding in this original.

## Corrections and wording limits

1. **Bibliographic omission:** the scout's official-title citation names Michael L. Littman and Richard S. Sutton but omits **Satinder Singh**, a third author visible on original PDF p. 1. Add Singh to the citation. This does not change the technical conclusion.
2. The scout calls the learnability passage “Section 3 ‘Learnability’.” More precisely, Section 3 is **Conclusion**, with a Learnability paragraph. This is a locator correction, not a substantive fault.
3. Preserve the distinction between “matching details not established in the inspected construction” and “matching is absent everywhere”; between “independence not established” and “no independent replication”; and between “selection limits prospective population claims” and “all evaluation is invalid.” The reviewed evidence mostly already respects these distinctions.
4. A source's inclusion of a diagnostic establishes that this diagnostic was previously described there. The broad phrase “already-owned/routine” cannot by itself settle novelty of an unspecified future implementation or integration. No candidate-level novelty conclusion is drawn here.

## Actual reading and accounting

Read both supplied evidence documents. Independently parsed the actual supplied XML and read MultiVCDiff p0070, p0105, p0115, p0155, p0165, p0305, p0310, p0415, and comparison elements 1096, 1118, 1124, 1127, 1130, 1157, 2729, 2822, 2876, 2894. Read the supplied PSR original text extraction across its substantive PDF file pages 1, 3, 5, 7, 9, 11, 13, including definition, update, theorem, construction, lemma/proof text, and conclusion. This is text-level original reading, not a figure-rendering inspection or full mathematical proof audit. No supplementary tables/PDFs, released response objects, donor genotypes, author code, biological outcomes, other candidate archives, or external literature were inspected.

Local read/parse and this single report write only. Network requests 0; external model/API calls 0; dataset/ZIP/outcome downloads 0; experiments/tests 0; installs 0; author-code executions 0; other agents 0. Requested configuration: **Sol/high**. Effective backend/model/reasoning, runtime, token accounting, and cost are not independently exposed and remain unknown. No source/evidence document was changed; only `review/source_initial_assessment.md` was written. This check supplies factual implication bounds, not independent biological validation or novelty clearance.
