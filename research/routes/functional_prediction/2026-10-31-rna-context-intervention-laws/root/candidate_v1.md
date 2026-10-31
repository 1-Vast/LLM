# RCI-01, version 1: transport of a local donor action across RNA contexts

Frozen candidate for independent scientific review, 2026-10-31. This is an untested restriction, not an observed result. English artifacts and Chinese conversation follow the project brief.

## Question and possible use

Can measured joint splice-product composition predict an unmeasured GT/GC reporter construct's promoter or transcription-drug response, including a divergence between aggregate exon inclusion and the intended RNA product? The potential user is a functional-splicing drug-discovery assay team. The output would be a molecular reporter-response forecast. Endogenous rescue, therapeutic benefit, kinetics, and assay savings are not asserted.

## Minimal restriction

For reference-construct outcome distribution p_c(j), define G(j)=1 when the fixed, design-annotated donor is used. Let q_c(j) be the edited-construct distribution. The hypothesis is q_c(j)=p_c(j)*gamma^G(j)/[1+(gamma-1)*p_c(G=1)], with gamma invariant across the declared contexts for a construct pair. Estimate gamma from reference-context GT and GC profiles; combine it with the target-context GT profile to predict target-context GC. All rivals receive these same three paid profiles, sequences, identities, and contexts. The fourth profile is withheld. Entire gene families stay outside supervised training and tuning, while those three calibration profiles are explicitly permitted for a held family.

If Y is the source's two-intron inclusion class, DeltaP(Y)=(gamma-1)*Cov_p(Y,G)/[1+(gamma-1)*P_p(G)]. The question requires joint information beyond both marginals: G cannot effectively equal Y. The rule also requires outcome proportions within G groups to be preserved and cannot create a truly absent product.

This is ordinary exponential tilting/log-linear multinomial transport. When G=Y it reduces to the previously published scalar splicing mutation-scaling law. The potential scientific content is an empirical, transferable restriction tied to measured joint RNA products. No algorithmic or universal novelty is claimed. Scalar scaling, full-outcome multiplicative transport, a same-information ordinary nonlinear predictor, and a no-edit-effect forecast are necessary rivals. Family-level likelihood, intended/aberrant product error and calibration, coverage, and abstentions would matter; numerical protocol, criteria, and code have not been admitted or frozen.

## Resource and adverse facts

The original Shanas et al. 2026 study, DOI 10.1038/s41467-026-76370-1, supplies synthetic HEK293 reporter outcomes. The design-only audit finds 72 labelled constitutive-acceptor/GT-versus-GC donor pairs. Each differs by T>C at zero-based oligonucleotide position 163 outside barcode positions 18:30. Every pair also has different barcodes; none is a matched-barcode edit. Thus present contrasts are complete-construct effects unless a further barcode assumption is justified. There is no authenticated clean donor-only/acceptor-only/double-edit rectangle.

Five main promoters have a/b replicate labels. Eight transcription-drug dose conditions are under EF1alpha only; neither a full promoter-by-drug crossing nor drug biological replicate identity is authenticated. The single acquired processed control table is pm425a. No count, PSI, historical-response, or score field in it has been read or used. A design workbook's historical responses remain withheld.

The source already analyzes promoter-specific effects, alternative PSI scales, cryptic splicing, retention, clustering and ordinary sequence-based classification. Sec23 corrects detected junctions to the highest MaxEnt position within +/-3 nt, defines canonical donors as GT, and aggregates counts by splice isoform. Sec26/27 filter reads, low-coverage isoforms/variants and evidence for a cassette exon. A GT-only canonical flag cannot define the edited GC site's use. The inspected official tree contains the figure notebook and ancillary data, but no identified upstream mapper implementation. Figure code uses corrected coordinates. Exact pre-correction grouping and retained/discarded read accounting remain to be authenticated.

The identity-only check v2 corrects an omitted library prefix in the first audit. Literal keys match corrected-coordinate keys in 34697/35729 rows under a (0,0)-absent convention; missing-value conventions remain partly unresolved. These unweighted identities neither demonstrate RNA effects nor authenticate upstream count preservation. The original failed key comparisons are preserved and are superseded only for their literal-key interpretation.

## Independent-review question

Assess the strongest defensible claim, its closest-prior overlap, biological/practical importance, the minimum measurement assumptions, whether current evidence permits a falsifiable scientific count analysis, and a specific decision-changing discriminator if it does not. Distinguish an incomplete measurement premise from a refuted local-action law. Consider whether ambiguity can be bounded without replacing the intended product question with a processing-label score. Do not assume that a candidate must be accepted or rejected, or that any positive result exists.

Review original source passages and code; do not execute author code or open response/count/score fields. Preserve the initial assessment before discussion with the proposer/coordinator.
