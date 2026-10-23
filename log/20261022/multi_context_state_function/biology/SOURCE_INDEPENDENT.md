# Independent primary-source assay qualification

2026-10-22. Author: qualification_assay. Read after sealing HISTORY.md. Inputs: root-fetched official PMC9380471 XML (`replogle.body`), extracted `REPlOGLE_PASSAGES.json`, resource links and metadata-only browser/page manifests. No new HTTP, response arrays, model fitting, peer report or independent numerical rerun.

## Verdict

**CONDITIONAL GO for a bounded K562 artifact/schema qualification**, then a static across-gene state-to-independent-growth capability test if paired payloads exist. The primary establishes separate assay modalities and the intended bridge. It does not establish a downloadable joined table merely by promising it, nor demonstrate a new world-model or RSI mechanism. A single K562 context is enough for this first capability question; RPE1, multi-task inheritance and recursive strategy improvement are later claims, not prerequisites.

## What the primary establishes

DOI 10.1016/j.cell.2022.05.013, *Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq*. K562 uses CRISPRi dCas9-BFP-KRAB (KOX1-derived). Paired sgRNAs target the same gene. K562 day8 genome-wide state and day6 essential-scale state are separate named experiments; their cells or guides are not independent research tasks.

Growth is independently assayed through bulk gDNA dual-sgRNA enrichment, in biological replicate, not inferred from scRNA cell capture or transcriptomic DEGs. The paper reports growth-versus-transcriptional-response associations already, including Spearman -0.51 for response strength and 771 transcriptionally affected perturbations with negligible growth effect. These author-reported findings motivate availability, but also make a bare RNA/growth correlation non-novel.

K562 growth is described in Methods as initial day7 plus ten days, whereas Figure S1 says day6→16 and gamma is log2 guide enrichment per cell doubling. Preserve both descriptions until payload metadata resolves them. This conflict need not block a static contemporaneous association/increment test; it does block an unqualified exact early→late temporal or dynamics claim. Day8 RNA can overlap the bulk-screen interval, and consists of sampled surviving cells. It cannot establish prediction of future growth conditional on pre-intervention state alone.

RPE1 is not a simple second context: growth used KOX1-derived KRAB, while Perturb-seq used ZIM3; growth endpoint/normalization also differs from K562, with a day6 Methods versus day7 legend discrepancy. Leave RPE1 out of the minimum test and do not pool endpoints as exchangeable measurements.

## Actual minimum payload and lineage checks

One traceable gene/dual-guide-level K562 pseudobulk state matrix, a separately assayed bulk gamma column and shared stable perturbation identifiers are sufficient. Full raw cells are unnecessary if documented pseudobulk is available. Need schema/provenance for normalization, control definition, day8 versus day6 library, TSS/dual-guide identity, and original fitness missingness; need not require raw growth replicates as an absolute gate. Replicates, if available, improve uncertainty accounting.

Author data availability names gwps.wi.mit.edu for downloadable single-cell and pseudobulk populations and PRJNA831566 raw data. Current metadata manifests authenticate a K562 genome-wide pseudobulk heatmap interface and separate K562 essential/RPE1 pages; **they do not yet authenticate a usable state download plus fitness payload**. The historical Zenodo/Harvard expression loaders likewise do not alone authenticate growth. Do not call a heatmap UI a download, nor infer an absent artifact from that limited UI.

The primary says Table S1 holds library sgRNAs and that growth screens informed oligo overrepresentation. Initial library/guide selection also used Horlbeck growth information for known essentials. This is assay-design dependence, not an independent randomized sampling frame. Restrict inference to the covered perturbation population. Keep identifiers mapping multiple constructs/TSSs to one gene together across splits. Do not impute the authors' excluded discordant-growth outliers from RNA. Count gene-level units, not captured cells.

## Minimum fair scientific question

Does measured perturbation-induced RNA state improve held-out-gene bulk-growth prediction beyond strong direct models using the same available pre-existing gene features, known growth priors, baseline expression, guide/knockdown efficacy and assay metadata? Fit preprocessing/feature selection on training folds. Fit RNA-to-function ridge/regularized nonlinear decoders and simple fusion/residual competitors. Compare against transcriptomic response strength alone, since the paper already reports this signal. Give every eligible arm identical external annotations, training growth labels and hyperparameter opportunities.

Explicitly separate an arm receiving newly observed RNA from an arm predicting RNA from intervention identity. The former can show measured-state acquisition value; it cannot establish a virtual-cell simulator's necessity. Any predicted-state/world-model arm must beat direct growth prediction at the same information and budget. Knockdown efficacy/cell count/total-UMI nuisance-only comparators help identify guide potency or sampling proxies. They are not biological growth labels. Keep essentiality priors frozen and disclose their role in library selection.

For this small first study, preregister one main continuous growth metric and a modest practically meaningful increment plus gene-level uncertainty; decision ranking is optional and needs its own endpoint. Failure versus a strong ordinary decoder is a capability STOP, not a reason to add an agent. A positive measured-RNA increment permits a subsequent, separately preregistered model-update test. It establishes neither causal RNA mediation nor drug inhibition/CRISPRi equivalence, agent contribution, inheritance, joint gain or improved-improver RSI.
