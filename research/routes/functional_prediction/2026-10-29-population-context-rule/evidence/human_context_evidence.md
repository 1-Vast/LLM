# Bounded human-oncology population-context evidence audit

2026-10-29. Evidence role only. Requested `gpt-6.1-sol` / `high`; effective runtime model/settings, native tokens and paid cost are unknown. No candidate design, mechanism verdict, experiment, data-table access, code execution from authors, or library/index edit was performed.

## Finding and boundary

A current original human-cell source provides an explicitly manipulated extracellular-support effect and an important **source-owned conditional restriction**: stiffness-associated resistance to gemcitabine does not imply equal NRF2 dependence across PDAC backgrounds. In its tested cells, NRF2 deletion sensitizes MIA PaCa-2 on stiff substrates but not PANC-1; additional BRG1 loss/reconstitution experiments attribute the dependency largely to BRG1-positive backgrounds. This is the paper's own conclusion, not a new mechanism or an untested MAESTRO hypothesis. It supplies neither a general density/mixture law nor evidence that the restriction predicts an unmeasured drug/background from inexpensive functional observations.

The local library `reference/papers.tsv` was actually searched for density/mixture/population/coculture/stromal/support terms and its matching records read. The existing PNAS DOI `10.1073/pnas.2423894122` already owns CAF/dormancy/support/therapy-resistance findings; none is reclassified as new here. `research/INDEX.md` was inspected (first 100 lines; output partly truncated), including the current functional-rule and population-context ancestry. The new source is distinct support-stiffness evidence, not a claim that CAF effects themselves are new.

## Source identity and actual reading scope

- **Title:** Chemotherapy-induced senescence promotes stroma stiffness and antioxidant adaptation to promote chemoresistance in pancreatic ductal adenocarcinoma.
- **Authors:** Xinxin Liu; Zhihua Huang; Bohan Yang; et al.
- **Journal / date:** Nature Communications; original JATS epub date **2026-07-18** (not inferred from DOI suffix).
- **DOI:** `10.1038/s41467-026-75772-5`; PMID `42471321`; PMC `PMC13493974`; PMC version `PMC13493974.1`, version 1.
- **Primary source:** <https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13493974/fullTextXML>. Exact original 193,399 bytes retained as `p03.body`; SHA256 `ba359fefa4c39682b11a080d7bb2ad0f242fbb576931a5dfbbb0b91301292b53`. This is the main article XML, not supplementary evidence.
- **Evidence level:** P, selected original sections. Read metadata/abstract; Results Sec4–7, Sec9, Sec11; Fig2/3/4/6 captions as embedded in those sections; Methods Sec19/20/26/27/29/44; reporting-summary pointer and Data availability note. `p03_readable.txt` is a local extraction aid; generating it is not whole-article reading. No figure pixels, supplementary figures, reporting-summary document, Source Data workbook, linked numerical raw tables, or full remaining sections were inspected.
- **Exposure:** Published qualitative response outcomes and the published substrate-stiffness means/SD were read. These outcomes are exposed development/prior information and cannot be called untouched confirmation. No response effect was recomputed.

## Physical intervention and crossings

| Item | Verified original scope | Missing / limiting field |
|---|---|---|
| Human drug × cell | Fig3e: gemcitabine dose–response in MIA PaCa-2 and PANC-1 on Soft/Medium/Stiff collagen-I-coated PDMS. Fig4f crosses the same drug/backgrounds with NRF2 knockout and control under soft/stiff/stiff+GsMTx4. Fig6a,b adds BxPC-3 and MIA PaCa-2 BRG1/NRF2 genotypes on stiff substrates; Fig6g–k uses BRG1-deficient/reconstituted PaTu-8988T ± NRF2 deletion. | Not a many-drug crossing. Erastin and Ferr-1 appear in later mechanistic work, not a held-out monotherapy transfer panel. No new density or mixture-fraction dose series established. |
| Support manipulation | PDMS base:curing agent mass ratios 40:1, 30:1, 25:1; cure 60°C/24h; UV–ozone treatment; collagen I 0.1mg/mL overnight. Reported measured Young's moduli 61.93±3.54, 164.20±4.53, 485.8±15.7kPa. | These are tested substrates, not proof of a continuous monotone law or physiological coverage. Starting density, surface area/medium volume and adaptation interval not specified in the selected main method. |
| Matrix-remodeling bridge | CAFs exposed to control or gemcitabine-induced-senescent-cell CM deposit ECM, then are removed by detergent/NH4OH/DNase treatment. Cancer cells are reseeded on decellularized ECM for gemcitabine assays. | CAF source identity for every displayed curve and ECM-deposition duration are not resolved from selected passages. Decellularization does not establish stiffness is the only altered matrix property. |
| History/CM preparation | Human MIA PaCa-2/PANC-1 GIS induced at 200nM gemcitabine for 4d, daily medium replacement; wash; serum-free medium 24h; 30%/60% v/v CM used for PSC treatment. Caption gives PSC treatment 48h. | These are induction/CM steps, not the dose grid or duration of the Fig3/4 functional dose response. No residual-drug assay was verified. |
| Functional readout | CCK-8, 450nm absorbance; dose-response/IC50, captions n=3 independent experiments. | CCK8 is a metabolic bulk signal, not additive surviving-cell/founder output. Source itself reports stiffness-dependent ATP/mitochondrial changes. Dose grid, drug exposure duration and normalization/linearity calibration not stated in selected main methods. |
| Units | Captions explicitly label dose-response n=3 independent experiments. Molecular NRF2 imaging counts cells within 3 experiments. Mouse orthotopic support experiments are separate. | Technical wells, culture preparation independence, plate randomization and donor-level replication not verified. Individual imaged cells are not independent experimental replicates. |

## Exact source passages and their implications

**Sec6, physical support and response:**

> “To directly test the effect of matrix stiffness on gemcitabine sensitivity, we adapted PDAC cells to PDMS substrates of defined stiffness (Fig. 3e).”

> “Both MIA PaCa-2 and PANC-1 Cells cultured on stiff substrates exhibited markedly elevated IC₅₀ values for gemcitabine compared with soft or medium conditions, indicating reduced drug sensitivity (Fig. 3e).”

Fig3e identifies dose–response curves for these two human cell lines and n=3 independent experiments. Sec6 also states no significant senescence difference across stiffness conditions (Supplementary Fig10; **this is a reported result, not inspected supplementary evidence**). This supports a tested extracellular-support dependence; it does not isolate a new density law.

**Sec7, genetic restriction / counter-background:**

> “Functionally, NRF2 deficiency reduced the IC₅₀ of gemcitabine in MIA PaCa-2 cells under stiff conditions, whereas PANC-1 cells exhibited no change in gemcitabine sensitivity following NRF2 loss (Fig. 4f).”

NRF2 knockout was validated by western blot in the Fig4 caption. The same section reports GsMTx4 pharmacological Piezo1 blockade and NRF2 localization/ROS readouts, while explicitly recognizing cell-line differences. This already prevents the unrestricted inference that the same measured support change implies the same NRF2 dependence.

**Sec9, source-owned BRG1-conditioned restriction:**

> “In BRG1-deficient cells, additional NRF2 knockout did not further affect gemcitabine sensitivity (Fig. 6a, b).”

> “By contrast, ectopic BRG1 expression rendered these cells dependent on NRF2: under stiff-matrix conditions, NRF2 deletion significantly increased gemcitabine sensitivity, accompanied by higher lipid ROS and MDA levels and lower GSH levels following gemcitabine treatment.”

> “Together, these findings indicate that the NRF2-dependent antioxidant program conferring protection against gemcitabine on stiff matrices is largely restricted to BRG1-positive PDAC cells, identifying BRG1 as a critical determinant of stiffness-driven redox adaptation.”

The reconstitution paragraph concerns PaTu-8988T, with similar PANC-1 results cited only to uninspected Supplementary Fig18. The report preserves this distinction. The paper owns the conditional biological statement; generic context-conditioned fitting would discard the intervention-specific necessity evidence, but this audit does not claim any new predictive method follows from it.

**Sec29, functional measurement:**

> “CCK-8 assay was performed to detect the sensitive of PC cell to drugs (gemcitabine or Erastin), and absorbance was measured at 450 nm using a 96-well plate reader.”

A separate colony assay described here uses 1000 cells/6-well plate, 200nM gemcitabine for 10–14d after BRG1 knockdown ±2µM Ferr-1, in BxPC-3 GR/MIA PaCa-2 GR. It is **not** a verified matched stiffness-series founder assay and must not silently replace the CCK8 support endpoint.

**Data availability note:**

> “Source Data and Supplementary Information are provided with this paper. All other data are available from the corresponding authors upon request.”

This is an article-level availability claim only; no functional workbook was downloaded or qualified. Public GEO GSE205013 and TCGA-PAAD concern transcriptomic/clinical material, not automatic access to an independently partitioned functional support experiment.

## Unresolved relation / data condition

The original source demonstrates one drug's support-dependent response and tests a molecularly conditioned dependency in selected backgrounds. What remains unresolved is whether **cheap functional measurements alone**, acquired before target outcomes and under matched timing/physical support, can identify a concise restriction that predicts an unmeasured drug or background better than direct context screening and ordinary history/context models. The source does not supply that result, a held-out evaluation, or a support-density equivalence.

A future resource contract would first need the actual well/culture/preparation identities, starting cell numbers and media/surface geometry, substrate adaptation/drug exposure duration, dose grid, matched control normalization and a validated count/death or reproductive endpoint (or a justified CCK8 observation model). An outcome-exposure boundary would have to exclude all article-read Fig3/4/6 claims from untouched confirmation. This is a data-condition statement, not an admission recommendation or a biological negative.

## Search accounting and local exclusions

3/3 allocated logical requests used; HTTP200 for each; 25s timeout; 0 retries; redirect handler rejects redirects; no redirects occurred; **961,365 total new body bytes**. Exact URLs, literal queries, times, headers, status and SHA are in the matching receipts. Underlying transport bytes unknown. No further request is authorized for this worker.

1. `q01`: full indexed-text Europe PMC search for density/population/mixture plus cancer/drug terms, 2025-01-01–2026-10-29; 13,047 hits; first 50 returned, titles screened. The broad route was noisy (full-text matches), not comprehensive coverage. Selected original source above was found here.
2. `q02`: TITLE_ABS density/seeding/inoculum plus cancer/drug terms, same dates; 124 hits; first 50 titles read, returned abstracts partly read for leading/relevant hits. It was not a 124-paper review. The murine BRAF organoid DOI `10.1002/ijc.70453` is explicitly a murine system in its abstract and does not qualify as human evidence. The direct density/ferroptosis item “The Warburg Effect Suppresses Ferroptosis Through Activation of NADPH Sensing” is DOI `10.21203/rs.3.rs-9860072/v1`, first date 2026-06-08, Research Square v1; only abstract inspected, no current journal status or full method verified. “Generation of mixed ovarian cancer and fibroblast spheroids by bioprinting”, `10.21203/rs.3.rs-8345818/v1`, first date 2026-02-16, is also a preprint abstract only; it reports CAF growth support without carboplatin protection, but no full primary intervention/readout contract was verified. These remain leads, not source-qualified findings for a new rule.
3. `p03`: selected original main JATS above; exact 193,399 bytes.

No protected/verification page, bypass, download of numerical raw outcome tables/workbooks, .env access, PRISM24Q2/CTRP access, installation, scientific experiment, or subagent occurred. All new files are confined to this evidence directory.
