# Initial biological questions before source-data schemas

The original2026 paper studies compound-specific exon inducibility with explicit U1 binding/sequence features. Its mechanistic findings and predictive model are direct priors. None of the following is a new mechanism yet.

One possible object is a conditional **response restriction** across cells: distinguish an RNA element's pharmacological susceptibility from its current inclusion fraction. Baseline inclusion, regulatory availability and compound binding can each produce context-dependent changes. A transferable relation would need a condition where these explanations make different predictions; an unrestricted nonlinear regressor already covers their association.

A different object is **specificity under regulatory-context intervention**. If actual perturbations change a defined binding context, ask whether a relation learned from one such context predicts the compound response in another. This needs matched intervention/compound controls, defined event support and a holdout not chosen by the observed response. An apparent interaction can arise from a bounded measurement scale or sample selection. Calling it a changed regulatory operator is not a result.

A third object is **the boundary of a proposed biochemical explanation**: when can sequence/binding measurements anticipate cellular exon response, and when do cell-specific regulatory conditions invalidate it? The original directly studies RNA duplex binding and structure, so any contribution must state what observation it could newly predict beyond those experiments and XGBoost. More sequence features or a frozen RNA embedding alone is not that contribution.

The next decisive source check is whether actual economical tables jointly retain untreated reference events, matched controls/replicates and relevant interventions, rather than only selected induced examples or author-derived labels. We have not inspected those data values or selected a candidate. Molecular selectivity is the intended scientific output; cytotoxicity and clinical effects remain separate.
