# A — PPC cross-system functional response transport

**Decision: STOP acquisition and do not select A for a numerical pilot in this round.** The paper identity and abstract are authenticated, but no PPC response table, data dictionary, or paper-linked implementation was obtained. The cross-system transport hypothesis was not tested. Missing overlap is **unobservable, not zero**; inaccessible public resources do not refute the hypothesis.

## Observed evidence

Official bioRxiv API and exact Crossref metadata agree on the preprint:

- Karl Pichotta et al., **A Pan-Cancer Ex Vivo Drug Screen Atlas for Functional Precision Oncology**.
- DOI: <https://doi.org/10.64898/2026.02.14.705918>; bioRxiv version 1, dated 2026-02-17; official API reports `published: NA`.
- Official metadata: <https://api.biorxiv.org/details/biorxiv/10.64898/2026.02.14.705918>.
- Crossref record: <https://api.crossref.org/works/10.64898/2026.02.14.705918>.
- Europe PMC identifier `PPR1223457`; exact record retrieval: <https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.64898/2026.02.14.705918&format=json&resultType=core>.
- BioRxiv and Crossref explicitly report CC BY / CC BY 4.0 **for the preprint**. A license for response data, metadata, model weights, or linked code was not established.

The **abstract's claims**, not independently counted data, are 2.1M experiments, 1,982 ex vivo samples, 3,100 drugs, 134 cancer indications, 26 studies, and a cell-line comparison across 55 cancer subtypes. It describes a contrastive Bayesian model to harmonize studies and an ex vivo foundation model. No methods, evaluation split, normalization recipe, clinical endpoint, or transport performance was readable from the authenticated abstract.

The original full-text route returned HTTP 429. Crossref's deposited HighWire syndication route returned HTTP 403. These are access failures, not content reads. An official JATS locator is supplied by the bioRxiv API but was not requested after the full-page restriction: <https://www.biorxiv.org/content/early/2026/02/17/2026.02.14.705918.source.xml>. No authentication, proxy, or access-control bypass was attempted.

## Actual numerical availability and support

| Required item | Observed status |
|---|---|
| PPC numerical response rows downloaded | **0** |
| PPC numerical download locator verified | **None** |
| Independent biological sample count | 1,982 is an abstract claim; not recounted |
| Meaning of the 2.1M observation unit | Unknown: sample-drug, dose point, replicate, or another unit not authenticated |
| Actual response/endpoint columns and units | Unobserved |
| Actual system, assay, study, drug, cancer, duration, dose, donor fields | Unobserved |
| System × study × assay incidence | Unobservable |
| Shared drugs/cancers across cell-line and ex-vivo studies | Unobservable; abstract's 55-subtype claim does not provide the incidence table |
| Same donor/model lineage across studies or systems | Unobservable |
| Overlap supporting leave-study-out, leave-drug-out, or joint holdout | Unobservable |
| Replication and uncertainty available for target ranking | Unobservable |

Consequently there is no defensible numeric overlap count, holdout partition, independent test size, or fitted comparator result for A. Do not substitute headline counts for usable support.

## Source-code disambiguation

GitHub exact project name and README searches returned zero hits in the tested queries; this does **not** establish that the project/code is absent. The authenticated first-author GitHub account is <https://github.com/kpich> (`name: Karl Pichotta`, profile links <https://kpich.com>). Its 22 public repositories and the linked homepage supplied no PPC-2026 release link. The homepage says updated 2020. The official Tansey lab inventory supplied 26 public repositories.

The laboratory repository <https://github.com/tansey-lab/UnitedPPC> needs qualification: its description concerns drug-response prediction, but it is a fork created/pushed in 2024, its README describes UnitedMet metabolomics, and no paper-to-repository link was authenticated. **Relationship to the 2026 PPC atlas remains unverified.** Do not treat it as the atlas implementation or a verified unrelated project.

Pinned inspected tree: `9e82fb2c7ee72dcdd268e4f035b73a0f8b3ab24b`, `truncated: false`. The only visible `data/` CSV is `MasterMapping_ccRCC.csv`, not downloaded; it cannot substitute for a PPC response release.

The original loader was actually read at <https://raw.githubusercontent.com/tansey-lab/UnitedPPC/9e82fb2c7ee72dcdd268e4f035b73a0f8b3ab24b/UnitedPPC/data_processing.py>. Lines 35–44 expect a sample metadata CSV, an RNA matrix, and a response CSV pivoted by `sample_id`, `drug_id`, and `z-score`. Lines 57–70 sort metadata by `study_id`, use `id_sample`, and construct a study batch index. These are **code expectations only**, not an observed PPC-2026 data dictionary. No assay, system, concentration, duration, or lineage field is used in this loader. The loader does not give a download URL. The repository API identifies an MIT license; that does not establish licensing or lineage for absent PPC-2026 data.

## Identifiability and a future eligibility gate

To attribute a response difference to model system, a study-fixed-effect analysis needs model system to vary within at least some studies, or a credible bridge using repeated samples/models under multiple systems/assays. If every study contributes exactly one system, then a system indicator is determined by study membership. A system effect cannot be separated from unrestricted study effects from that design alone. Crossing only drugs and cancer types does not resolve this aliasing. Assay platform, concentrations, exposure duration, culture conditions, and measurement metric must also be checked; even within-study crossing can retain assay confounding.

A later PPC pilot could qualify only after obtaining numerical data plus source licenses and constructing a system × study × assay × drug × cancer support census. Require multiple source and target studies with overlapping compounds/cancers, traceable biological sample identities, and raw or consistently recomputable response metrics. Report support per held-out study and drug rather than a pooled random-row score. Repeated donor/model lineages must remain within a partition. For an unseen-drug test, a model must use legitimate drug descriptors or predeclared target features; free drug-ID factors cannot infer a new drug. For an unseen-study test, adaptation labels/calibration must be explicitly accounted for. Any global response normalization or harmonization estimated from all labels would contaminate a new-study test.

Even a feasible grouped evaluation would support prediction under that dataset design, not biological mechanism or patient clinical efficacy. There is no evidence here that PPC's original foundation model used or passed those tests.

## Lab decision and ordinary explanation

Concrete user: a screening laboratory choosing which compounds to test next in expensive patient-derived organoids or ex-vivo preparations after a cheaper cell-line screen. A useful endpoint would rank compounds for target-system follow-up in a held-out study/cancer context, with uncertainty and a fixed experimental budget. It requires a measurable gain in prospective candidate prioritization over ordinary drug/cancer effects, concentration-aware response summaries, study calibration, and regularized or hierarchical prediction.

The strongest ordinary explanation for an apparent system advantage is a mixture of study/assay calibration, tested drug/cancer composition, dosing/exposure range, and proliferation-dependent viability readout. The abstract itself reports cell-line preference for proliferation-targeting drugs. That is compatible with genuine biology and with assay/culture differences; the accessible evidence cannot distinguish them. A new label for transport, a large atlas, or a contrastive embedding does not establish a new mechanism.

## Exposure, budget, and limits

This episode exposed only bibliographic/abstract metadata, public repository inventories, a repository README/tree, and one loader source. **No PPC response labels, model weights, protected files, reserve/confirmation outcomes, or pre-existing local experimental outcomes were opened.** Public preprint release is dated 2026-02-17; the individual 26 study releases, sample reuse, model pretraining exposure, and any earlier local exposure are unverified. Therefore no independent/untouched confirmation status can be claimed.

One scoped A reconnaissance plus one targeted official-author/source-resolution follow-up; no additional source pass, fitting, experiments, or external model APIs. 29 requests total: 3 ephemeral discovery API responses plus 26 preserved request receipts. Of the logged requests, 18 returned 200, one 403, two 404, one 429, and four had connection-reset errors. Completed saved payload: 928,107 bytes in 22 files; including the 46,127 initial ephemeral bytes, completed observed response payload was 974,234 bytes. Partial network transfer on connection failure was not measured. This is far below the 80 MB cap. API monetary/model token usage is unavailable, not zero.

Files: `requests.jsonl` preserves exact URLs, purposes, per-request byte bounds, HTTP/error status, final URL, complete saved byte counts, and hashes. `support_census.csv` records unavailable counts explicitly. `collect_ppc.py` is the bounded acquisition script; nothing downloaded was executed. All writes stayed in this assigned new audit directory and the assigned PPC download directory.
