# Frozen question: pooled drug-response measurements and discovery decisions

2026-10-30. Scope: drug discovery, a virtual cell predicting intervention consequences, an Agent framework, cheap accessible data. No main mechanism is assumed established. Determine what the actual source measurement supports and whether it can support a useful further claim.

## Source and exact observed quantity

Rhaister v1,2026-06-12, DOI10.64898/2026.06.09.731197. Inspect original HTML sources/root10_rhaister_article_redirect.body, original JATS sources/root07_rhaister_explicit_redirect.body, and the original equation image derivative sources/rhaister_eq18.png (original GIF receipt sources/root12_rhaister_eq18.json). Eq18 defines P[c,group]=n[c,group]/sum_c n[c,group] and sensitivity[c,p]=log2(P[c,p]/P[c,control]). Selected methods state five-day pooled cell harvest with minimalQC for sensitivity and fullQC for transcriptomics. The publisher HTML and HF README sources/root11_emerald_readme.body identify public data and the relative cell-proportion endpoint. The README advertises DMSO_T0 and endpoint vehicle controls, per-cell sample identifiers, and a compact cell_line/condition/growth_rate summary table. Numerical values from that table have not been accessed. Source data/replicate/normalization details outside the inspected material remain unknown, not absent.

## Proposed conditional analytical relation

For matched endpoint drug and vehicle cultures let N[c,p] be the true viable burden for line c, g[c,p]=N[c,p]/N[c,control], and G[p]=sum_c N[c,p]/sum_c N[c,control]. If recovered counts are proportional to true viable burdens with a common sample-specific sampling factor, then exp2(sensitivity[c,p])=g[c,p]/G[p]. Thus a matched absolute total-burden factor identifies g, while the relative observations alone admit different positive Gvalues. Within-drug differences of log-relative responses identify ratios between cell-line treated/control folds under this model. Absolute thresholds and cross-drug absolute rankings for a fixed line may depend on unobserved G. This is a standard identification claim, not a new mathematical method.

The observation model is critical. Cell-line-specific stable capture and condition-dependent capture must be distinguished; total counts need not correct every recovery distortion. DMSO_T0 proportions do not automatically supply an endpoint total scale. The source may possess other calibration not yet inspected. Drug-sensitive dissociation, cell assignment, live-cell selection and QC could alter the mapping to viable burdens. The observed statistic may be the intended scientifically valid relative estimand.

## Possible discovery use to assess

A virtual cell could represent both functional burden and its measurement mapping. An Agent considering a specified absolute advancement threshold might request a matched total-count or reference-line observation, revise the inferred outcome, or abstain. This is a proposed capability, not demonstrated advantage. Strong rivals include the same deterministic compositional correction, fixed total-count recording on all conditions, ordinary response prediction with the same corrected labels, and direct population-resolved functional assays. Charge historical/initialization/calibration/preparation/repeats and biological time equally. If no defensible bounds on Gexist, an adaptive threshold policy may have no selective query advantage.

## Independent assessment requested

1. Check the algebra, source interpretation and recovery assumptions; identify a counterexample to any overbroad statement.
2. Distinguish relative-selectivity questions that remain identified from unqualified absolute claims. Do not assume an intentionally relative endpoint is an author error.
3. State the strongest existing/simple explanation and what substantive useful contribution remains to be tested, including what an Agent would add.
4. Assess whether current metadata can admit an empirical effect/benefit test, or which actual missing observations could change that decision. Do not inspect numeric outcome values or run scientific code.

Read this neutral question and raw sources before any proposer discussion or draft report. Save initial_assessment.md before receiving further interpretations. No desired verdict is supplied. Only this question and source evidence are frozen; provisional exploration notes remain separate. No network/model calls, protected/sealed/confirmation outcomes, installs, author code or scientific experiments are assigned.
