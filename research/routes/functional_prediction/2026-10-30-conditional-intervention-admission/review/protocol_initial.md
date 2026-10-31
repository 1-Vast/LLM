# Independent initial review of the frozen Stage 1 protocol

Date: 2026-10-30. Overall research status: ACTIVE / NOT_ACHIEVED.

This is the challenger's initial assessment of the original pre-score proposal, saved before any reply to the coordinator, discussion of this assessment, or exposure to candidate implementation code or numerical CGI outcomes. The reviewed `stage1_protocol.md` SHA-256 was `9c449f551690b7104db3b5212a61c7ceb3395db1a152ed7beedb99faffb816f4`; `identity_freeze.json` SHA-256 was `b975cf8f5570f0e9714e3e5f30b376f3f0b51c1b99a34174789eb7b26c31a3be`.

The coordinator sent one unsolicited metadata-only update while this review was being prepared: duplicate source gene identifiers, Excel-corrupted EKO strings, and an intended pre-label identity/arm-mask amendment. I did not discuss or accept a proposed resolution before saving this assessment. I independently verified only the four cited identity rows below; the duplicate counts in that message have not been independently recounted. No desired verdict, numerical result, S1E hit row, protected outcome, or implementation code was supplied or read.

## Initial disposition

**AMEND BEFORE NUMERICAL ACCESS.** The narrow scientific question is legitimate and a small development diagnostic could be useful. The written permutation procedure does not yet justify the nominal significance gate for the joint cross-validation statistic, model selection is underspecified, and the exact gene-identity/artifact mask is not auditable from the frozen artifacts read. These are pre-access protocol blockers that can be resolved without opening any call labels. They are not evidence that chemistry lacks information or that the resource is unusable.

Even after those changes, this would establish at most structure-associated recovery of a selected, fixed, processed call panel in one cell background. Passing it would not establish physical sensitization, an independent prospective label pipeline, practical assay savings, mechanism transfer, an innovative algorithm, or a completed research goal. The 63-compound held-out boundary must remain intact. A positive Stage 1 result is permission to design and challenge a later protocol, not permission to open those labels.

## Primary evidence actually checked

- `cgi_source/paper.xml`, Methods S29: screens were conducted in rounds over four years and the round-1 library yielded “similar but less complex signatures” for compounds that were later re-screened. Deterministic first-screen selection avoids outcome-directed picking but can retain these weaker early measurements.
- Methods S32: concentrations were “chosen to cause an estimated IC30 for proliferation inhibition (a.k.a. GI30), based on 384-well dose response curves for each compound.” It also says that “when compounds failed to cause sufficient inhibition of proliferation, we increased the concentration on day 4.” Therefore the target is a source-selected assay regimen, sometimes adaptive, rather than a general response at an arbitrary intended dose. Structure-only prediction still conditions on that selection process.
- Methods S35: “For each round separately, read counts across all untreated or 0.1% DMSO or ethanol-treated control samples were added together to generate a single background sgRNA frequency distribution averaged across the 8-day screen.” The same paragraph says that co-cultured samples were summed to represent “a single independent screen.” Round control/library dependence remains after eliminating pseudoreplicate screen rows.
- Methods S35 requires a minimum of four usable sgRNAs and discards screens with inadequate library representation. Methods S36 says some extremely essential genes “generally had too few reads in both test and control samples to pass the critical thresholds to calculate a score.” Absence from a significant-call list therefore combines several measurement states.
- Methods S36 describes the native score as an average of `log(d)-log(e)` using guides against similarly essential genes. The original `CRANKS_README.md` defines “synthetic sick/lethal (negative scores) and synthetic rescue interactions (positive scores).” Original `cranks.pl` lines 108–123, 142–198 and 201–270 support normalized guide fold changes, guide-count exclusion, signed rank-tail scoring and direction-specific within-screen p/FDR processing. I read the original author source, not candidate implementation, and did not run it.
- Original S1 Overview: “E) Complete list of CGIs detected in this study at FDR<0.05. FDRs of zero indicate <0.001.” This supports the published-call endpoint; it does not supply complete nonsignificant p/FDR or biological-negative labels.
- Original S2 Overview: “Scores were corrected for artifactual chromosome 7p hits caused by chromosome arm loss.” Original Results S11 paragraph 2, displayed with numerical quantities masked, says that scores of all genes on 7p in the relevant screens were biased toward rescues, attributes this to loss of distal MAD1L1, and describes a milder 21q signature involving SLC19A1. These are arm-level phenomena, not just two problematic target genes. No correction algorithm was established by this review.
- Methods S57 defines the second CRANKS2 essentiality dimension from gene-score/population-doubling correlations “across all chemogenomic screens.” Excluding CRANKS2 and post-treatment descriptors is necessary for this question.

The complete `brief.md`, `stage1_protocol.md`, `identity_freeze.json`, and `cgi_source/evidence_contract.md` were read. Other checked saved sources were `primary_methods_selected.txt`, source manifests, original README and both original Perl programs, schema/identity audits, S1 overview, the existing HGNC receipt, and small identity-only excerpts. The main paper was not read indiscriminately; S11 was extracted from the XML with numerical quantities masked before display. No workbook outcome body or S1E roster was read.

## Blockers to resolve before numerical access

### B1. The training-only permutations do not yet calibrate the reported joint statistic

Protocol line 37 keeps validation labels fixed while separately permuting source profiles within each training fold and round. The three source sets overlap. A compound can consequently receive different pseudo-profiles in its two training roles while retaining its original profile in its validation role. This is not one coherent exchangeable reassignment of the data on which the complete three-fold statistic is evaluated. In particular, it can change the dependence between fold gains; fixing the frequency baseline or subsequently bootstrapping scaffold groups does not restore that dependence.

It is a reasonable training-alignment stress test. I cannot justify treating its tail fraction as a calibrated conditional permutation p-value for the aggregate statistic from the stated exchangeability assumption alone. The acknowledgment of shared training and exploratory intervals does not resolve the significance gate at line 41.

Before access, either specify a coherent randomization of the entire development statistic with a defensible unit/exchangeability argument, or explicitly demote the current quantity to a heuristic reference and replace the inferential continuation rule. One possible coherent design to assess in an amendment is a single shared whole-profile permutation within each fixed development-fold/round stratum, applied consistently in every training and validation use, followed by recomputation of the entire statistic. Such strata preserve the fold-specific training call totals, rarity set and frequency baseline. This is a proposed protocol correction, not a newly performed test or a guarantee that the biological observations are exchangeable. Any revised null still needs its assumptions stated, including residual within-round library, selection and measurement dependence.

There must be no resampling scheme or stratum change chosen after observing gains. No held-out compound is needed to resolve this issue.

### B2. The family maximum must include the actual alpha/model selection

Line 31 offers ridge alpha in `{1,10,100}` but only calls its selection “exploratory source-development selection.” Line 37 then refers to identical settings and maximum model gains. It is unclear whether there are four fixed evaluated predictors (neighbor plus three ridge alphas), an inner source-only selector, or an alpha chosen using the same reported development predictions.

Freeze this choice and all selection/tie rules now. The aligned statistic and every null statistic must apply the identical complete selection operation. In particular, selecting the best aligned alpha using the reported fold labels and then holding only that winning alpha fixed in permutations would omit selection from the reference distribution. The minimal option is to declare the maximum over the neighbor and all three ridge settings, repeat that same maximum in every permutation, and label the reported winning predictor exploratory. An inner selector is possible but would require a fully specified source-only procedure and would add cost.

The paired bootstrap for the selected predictor remains conditional/exploratory; the written caveat is appropriate. It must not be relabeled as a confidence interval with population coverage. With 49 permutations, the attainable plus-one p-values are coarse (multiples of 0.02); this is a bounded resolution limitation, not a reason to add permutations after seeing a borderline result.

### B3. Freeze the exact identity join, gene universe and both-arm mask

The protocol's “matrix gene identities” and “lexical source gene identity” do not identify whether EKO or HGNC(2020) is authoritative, how duplicated or multiply mapped canonical genes are handled, or how S1E and S2 identities join. This matters before any rarity count or top-20 ranking is formed.

The identity-only `gene_identity.tsv` explicitly has:

- line 4311: EKO `46082`, HGNC(2020) `MARCHF1`;
- line 4386: EKO `46083`, HGNC(2020) `MTARC2`;
- line 11843: EKO `46082`, HGNC(2020) `MTARC1`;
- line 13604: EKO `46083`, HGNC(2020) `MARCHF2`.

Thus the same corrupted EKO string can refer to two different genes; it cannot be a unique key. A canonical-field, metadata-only mapping plus predeclared exclusion of ambiguous/multiply mapped identities is defensible. Choosing one duplicate by call magnitude, hit presence, convenience or downstream performance is not. If labels have no unique admissible identity match, the policy must be a fixed exclusion/error policy rather than outcome-guided repair.

The reviewed freeze identifies descriptor/split hashes but not a finalized 7p+21q gene roster/hash. The source worker's saved roster covers candidate 7p rows only. Before access, save the complete exact inclusion/exclusion roster, HGNC source hash, canonical/previous-symbol policy, handling of unmatched/ambiguous arm assignments, and artifact-mask hash. Unresolved location cannot silently certify that a gene lies outside both arms. This is an audit-completion blocker; it does not require downloading a new source or inspecting a response cell.

## Bounded limitations and interpretation

### Selection, chemical generalization and experimental units

One fixed representative per source compound, exclusion of round-9 hypothesis tests and co-treatments, grouping all related doses, and scaffold separation are appropriate safeguards. The split establishes separation under the specified standardized Bemis–Murcko definition only. Closely related structures can have different Murcko scaffolds; a pass would not show distant chemistry, new-target or new-mechanism transfer. Keeping acyclic molecules together is conservative and may concentrate a chemically heterogeneous group into one fold. Unequal fold sizes are acceptable if P@20 is averaged over all representative compounds, as written, rather than averaging three fold means equally.

The drug is the prediction unit and scaffold is the resampling group. Gene rows, guides, repeated doses, sequencing samples and shared controls cannot inflate the effective drug count. A one-cell-line panel with source-selected compounds and tolerated regimens is neither an unbiased chemical population nor independent biological replication. Bootstrap resampling over scaffolds does not incorporate round-level control uncertainty, guide-level uncertainty, assay repeatability or the model-selection process.

The deterministic earliest screen is a transparent selection rule, but round-1 under-representation and later reruns mean it need not select the best measurement of a compound. That is a limitation to retain, not an invitation to choose a later signature after seeing outcomes. Adaptive schedules can remain only under the explicit source-regimen claim; they cannot be described later as fixed-dose zero-assay prediction. A GI30-selection curve is already assay information even though a genetic panel is unmeasured.

### Rarity and no-call definition

The source-fold-only rarity rule avoids selecting genes from the query outcomes. The lower bound of one source call makes this a transfer task over previously called gene identities; it cannot discover a gene never called in training. “Rare” means infrequently called among that fold's source compounds, not a low-prevalence biological vulnerability or rarity in the full chemical universe. The upper bound can legitimately differ between folds because source counts differ.

It is valid to encode absence from the complete S1E significant-call list as zero for the literal endpoint “published called sensitizer.” It is not valid to interpret that zero as measured resistance, lack of sensitization, or a biological false positive for a prediction. Nonsignificance, insufficient guide coverage and genuinely absent effect remain mixed. The amendment should make this binary call-absence convention explicit and specify joins/unmatched cases. It should also define whether “all-call recall” uses all unmasked query calls or only source-eligible calls; the former, alongside eligible-call recall/coverage, reveals how much biology the source-eligibility restriction makes unrecoverable. No choice may depend on which yields a better result.

Use the S1E call's own FDR and sign for this endpoint. The S2 matrix is a distinct processed resource with a stated correction; no equivalence of its correction/sign with S1E was authenticated. Do not switch between them to improve consistency or performance after inspection.

### Processed labels and artifact exclusion

Masking entire 7p and 21q is conservative, transparent if frozen, and scientifically preferable to masking only MAD1L1/SLC19A1. It also deliberately discards some genuine signals. It cannot establish that all artifacts, cross-screen corrections, power effects or source-selection dependencies have been removed. The source specifically describes rescue-biased arm artifacts, whereas this test focuses on sensitizers; broad arm exclusion remains a conservative choice and should not be described as a validated reconstruction of author correction.

Unresolved global processing is not an automatic blocker for a clearly labeled fixed processed-label diagnostic. It is a blocker to claiming prospective independence of label construction, and a pass here cannot resolve it. Raw-data or fully documented independent label construction, independent cultures and a separate experimental context would be different evidential steps, not benefits supplied by scaffold separation.

### Headroom, continuation and practical value

P@20 is a concrete fixed shortlist metric. Keeping zero-eligible-call query drugs in the macro denominator avoids a major source of optimistic selection. Oracle P@20 must be defined as `min(20, number of eligible query calls)/20` under the same mask/universe. Low oracle headroom can make a biologically ambitious gain impossible; report absolute recovery, baseline, oracle and the fraction of all query calls covered by source eligibility together.

A positive, properly controlled gain is an information prerequisite, not a useful-gain threshold. The written distinction from exceptional gain is appropriate. Practical benefit needs an assay decision and cost comparison, reproducible physical effects, and an estimate of what a twenty-gene recommendation replaces. Native within-screen FDR and the compound bootstrap do not supply these. Exact-dose repeated screens, if available, can be descriptive support only; freeze the repeat identity/dose-matching definition and retain all qualifying repeats rather than selecting concordant examples.

The likely scientific value of this stage is modest but real: it can rule in or fail to establish simple chemistry-associated prioritization beyond marginal gene-call frequency before committing to a larger virtual-cell direction. It cannot justify a novelty or agent claim, and it may stop even with statistical association if repeatability, headroom or cost support is inadequate. A negative diagnostic must remain failure to establish this particular transferable-call signal, not biological absence or rejection of all conditional-vulnerability prediction.

### Feasibility

The small sample count and fixed fingerprints support a bounded neighbor/ridge matrix using existing software. The full output matrix and repeated multioutput ridge fits still require care under the 30-minute/four-thread cap. Reusing feature-side linear algebra within a fixed setting is an implementation efficiency, not a new model. Log actual time, threads, all settings and failures; do not simplify the endpoint/model family, change alpha, drop difficult compounds, extend runtime, or introduce another run because results disappoint. The metadata sanitization correction was before labels and does not itself consume a scientific rerun.

## Traffic, independence and required next action

Reserved pass 6 public traffic used by this challenger: **0 HTTP request attempts; 0 completed response-body bytes; 0 known partial bytes.** Existing local originals were sufficient to identify the decisive protocol issues, so no named public-source gap justified spending the reserve. No network retrieval, installation, delegation, external model bridge, index/source-library/core edit or new numerical data test was performed. Candidate implementation was not inspected. This review file is the only artifact created by the challenger at this checkpoint.

The coordinator must resolve B1–B3 in a dated pre-score amendment and retain this initial assessment unchanged. The amendment should expose exact identities, mask and selection/resampling rules for review without any call labels or numerical result. The untouched 63-compound outcome boundary remains unchanged, and overall status remains ACTIVE / NOT_ACHIEVED.
