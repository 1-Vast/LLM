# Original-source grounding for the independent mechanism branch

2026-10-29 episode; completed after the session date changed to 2026-10-30. Only local original-text inspection and reasoning were used. No HTTP/API calls, raw outcome tables/workbooks, scientific tests, installs or author-code execution. Python was the assigned `D:\anaconda\envs\maestro\python.exe`, standard-library XML extraction only. Initial directions were preserved before current worker material was opened. The original `evidence/p03.body` and its original-text rendering were then inspected; the evidence worker's interpretive report and other workers' assessments were not read.

## P1: the already-owned live-stromal/contact result

DOI **10.1073/pnas.2423894122**, *Breast cancer cell coculture induces normal lung fibroblast transition to CAFs, promoting tumor cell dormancy and therapy resistance*. Local original: `../../../reference/papers/doi-10.1073-pnas.2423894122/supp-branch_c_PMC12663926.xml` (relative from the mechanism directory).

Actual reading: abstract; section titles; S7 juxtacrine/integrin/JAK mechanism paragraphs; S9 Discussion; S11–S12 methods; selected reference entries. This is selected original reading, not a complete SI or methods audit.

- **S7, first paragraph:** physical separation by permeable inserts removed the tested LF effects on MB231 proliferation, MB231/MB468 autophagic flux, and MB231 resistance to MCB-613. The authors already attribute the tested resistance to contact-dependent cues, partly mediated by integrins. This does not establish a quantitative contact-capacity law or protection as a function of mixture fraction.
- **S7, second paragraph:** IL-6 neutralization or addition did not change the tested LF-mediated growth/resistance phenotypes; JAK inhibitors modified the phenotype. Consequently, high measured cytokine abundance is not by itself a valid support coordinate.
- **S9, paragraph beginning “The results of our MB231-LF drug screen…”:** the authors say pathway disruption mitigated resistance “even in TNBC lines that did not exhibit dormancy-like growth suppression.” This blocks a blanket reduction of stromal resistance to one cycling/growth scalar in this setting. It does not disprove every cycle-dependent drug effect.
- **S12:** the reported 2D and 3D cocultures use a **1:1** BCC:LF ratio; BCC-specific fluorescence or bioluminescence tracks proliferation. The selected main-text methods do not establish a factorial ratio-by-total-density response resource. Detailed methods are in SI, which was not read here.

Owned by this prior: contact-dependent stromal resistance, dormancy/autophagy coupling and exceptions, inhibitor sensitization, screening with stromal context. Neither these findings nor the archived prevention-versus-maintenance question are a new candidate in this branch.

## P2: the newly acquired matrix/redox result

DOI **10.1038/s41467-026-75772-5**, *Chemotherapy-induced senescence promotes stroma stiffness and antioxidant adaptation to promote chemoresistance in pancreatic ductal adenocarcinoma*. Exact original: `../evidence/p03.body`; main JATS XML. The coordinator supplied its provenance and 2026 publication identity; this worker independently checked the title, abstract and passages below from the original. Its SHA was supplied by the coordinator, not independently recomputed here.

Actual reading: abstract; Sec6–9 relevant mechanism narratives (Sec6 via original-text rendering; Sec7–9 from JATS); relevant Discussion paragraphs; Sec19, Sec26, Sec27, Sec29 methods; selected reference entries. Figure captions embedded in article paragraphs were visible; no source-data outcomes, workbook values, plotted values or effect estimates were extracted or analyzed. No SI was opened.

- **Sec6:** the authors report CAF-deposited, decellularized ECM after GIS-conditioned-medium exposure and drug responses after reseeding PDAC cells. They also manipulate collagen-coated PDMS stiffness. Thus the source supplies an extracellular-material intervention, not only a correlation between a living stromal population and tumor response.
- **Sec7, second paragraph:** NRF2 deletion sensitized MIA PaCa-2 under stiff conditions; PANC-1 showed little change in the tested NRF2-dependent redox/gemcitabine phenotype. The authors describe cell-line-specific reliance on NRF2.
- **Sec8:** BRG1-positive BxPC-3 provides another tested background, while BRG1/NRF2 interaction and SLC7A11 regulation are directly investigated. The source owns this proposed mechanistic gate.
- **Sec9:** BRG1-deficient versus BRG1-reconstituted PaTu-8988T and the BxPC-3/MIA PaCa-2 interventions further support the source's claim that NRF2-dependent protection on stiff matrices depends on BRG1. Therefore “predict gemcitabine resistance from stiffness plus BRG1” cannot be represented as our new finding.
- **Discussion:** the authors acknowledge that the detailed Piezo1-to-NRF2 interface remains unresolved and that senescent burden and fibrosis are not strictly linearly coupled. They also consider damage-associated signals from dying cells. A scalar senescence fraction is therefore not an established extracellular-state sufficient statistic.
- **Sec19:** GIS induction uses gemcitabine with daily medium replacement, followed by removal of drug, PBS wash, serum-free conditioning, and CM at prescribed volume fractions. A finite extracellular drug-sink law is not supported by this protocol or narrative.
- **Sec26:** ECM is decellularized, DNase-treated, extensively washed and reused for gemcitabine sensitivity assays. This makes matrix provenance-versus-mechanics a conceivable comparison but does not demonstrate their equivalence.
- **Sec27:** prescribed PDMS base:curing-agent ratios define soft/intermediate/stiff preparation classes, with collagen I coating. Preparation ratio is not itself a measured universal stiffness value; matching materials by that ratio across different systems would be invalid.
- **Sec29:** drug sensitivity is assessed by **CCK-8 absorbance**, for gemcitabine or Erastin. The separate colony assay covers resistant BxPC-3/MIA PaCa-2 with BRG1 knockdown, gemcitabine and Ferr-1. It does not establish matched reproductive-output validation for the entire stiffness-by-genotype-by-drug matrix. Because the proposed biology changes metabolism, CCK-8 equivalence to live counts or reproductive survival must remain an explicit unverified measurement condition.

Owned by P2: GIS→CAF/ECM stiffening, Piezo1–NRF2/BRG1–SLC7A11 mechanism, background-specific dependence, and the reported senolytic/ferroptosis combination strategy. The current branch does not rename these findings as ours. Source-owned claims are not independently reproduced by reading the article.

## Closest-prior and availability boundaries

P2 cites **LeSavage et al., “Engineered matrices reveal stiffness-mediated chemoresistance in patient-derived pancreatic cancer organoids,” Nat. Mater. 2024, DOI 10.1038/s41563-024-01908-x**. Only its reference entry was read here; the original must be inspected before any broader claim about what matrix-based prediction already accomplishes. P2 also cites earlier NRF2/ferroptosis and BRG1/chemoresistance work. Reference titles do not establish that their detailed mechanisms are absent from the proposed extension.

A local keyword pass found no human original establishing the proposed finite-dose/number/volume relation in the available text subset. The coordinator likewise reports no foundation original from its bounded searches. This is a support gap, not evidence that such biology or prior work does not exist. A hit in PLoS Comput Biol **10.1371/journal.pcbi.1012185** was checked at abstract and keyword-selected methods: its density example was bacterial and cannot qualify this human-oncology task. Its generic structure-learning principle is a strong ordinary modeling precedent, not human biological support.

No newly qualified public resource has yet been established for an independent across-drug, across-extracellular-context transfer test with matched functional outputs and assay costs. The P2 source data have not been inspected or acquired by this worker.
