# Independent content review

Verdict: PASS for the report bytes SHA-256 `a8d343bafab1d49bbb2c02823d7c6a3e4b33a3c5b9789863afbc28ccafaa3487`. This is a source-interpretation check of a focused paper reading, not independent experimental or clinical validation. No remaining required correction was found after two local fixes described below.

## Scientific interpretation

The note accurately identifies Bai and Su's article as a published review (JATS `/article/@article-type="review-article"`; title/authors/DOI and dates agree with saved Crossref and EuropePMC metadata). Sections2.1.1-2.1.2 describe cell-based organoid digital counterparts, not a demonstrated complete human organ. Sections6.1/6.4 discuss organ/whole-body simulation and interconnected VOs as future directions.

The UR/VI account is faithful to section2.1.1 and bib11. Decoding states and approximating perturbation effects do not establish causal mechanisms. Section2.2 explicitly rejects assuming equivalent latent representations across heterogeneous models: shared anchoring observations, typed state variables and uncertainty-aware adapters are needed. The three-layer description and cell/shared-field coupling agree with sections2.2,3.3 and the reviewed examples in4.2.2/4.3. Section3.3.1 explicitly says each simulated cell follows predefined agent rules; neither this definition nor PhysiCell (bib73,2018) requires an LLM scientist agent.

Sections4.2.2/4.3 support exposure, spatial injury, oxygenation, intracellular networks and spatial immune-response hypotheses under their particular reviewed conditions. The note expressly says the complete original methods behind these examples were not audited. The virtual-memory T-cell distinction is correct: section4.2.1 describes biological mouse immune-cell populations and prospective computational embedding, rather than proof that a computational twin has already been built.

Review structure and all six numbered figure captions support a conceptual construction/application account. I independently inspected the whole saved original Figure2: it shows data collection, preprocessing, model training and evaluation, with no experimental performance comparison. I did not independently inspect every figure image. JATS has no non-bibliographic external links, no supplementary-material node and no original AIVOs Methods/Results programme; this supports the report's scoped statement about this review, not a universal absence-of-code claim. The note also gives due weight to the authors' own limitations and withheld-perturbation requirements in sections2.4/3.4, so the criticism is not unfairly presented as a limitation the authors entirely overlooked.

## ODFormer and the exact citation mismatch

Saved official bioRxiv API metadata, collection versions1/2, independently confirms the reported abstract figures:183 PDOs,98 drugs,14000 response assays, pretraining on30000 pan-cancer bulk profiles and one million pancreatic-cancer single-cell profiles, and PCC>0.9. Dates are2025-07-10/11 and the returned `published` field is `NA`. These are reported preprint claims, not an audit of splits, endpoint design, calibration, spatial simulation, prospective benefit or causal improvement in patient care. The report keeps this boundary correctly.

The mismatch is literal in `//sec[@id="sec5.1"]/p[1]`: the sentence asserting that physical patient-based organoids resemble tumors better than traditional2D cell lines and yield clinically related drug-sensitivity spectra ends with `xref rid="bib129"` and `xref rid="bib130"`. Bib129 is Huang et al.'s origin-destination forecasting paper, DOI10.1016/j.eswa.2023.119835; bib130 is Wang et al.'s fundus segmentation paper, DOI10.1016/j.inffus.2024.102533. Those bibliography entries do not supply that organoid claim. This is not the citation for PCC>0.9: the correct ODFormer preprint is bib33, DOI10.1101/2025.07.08.663664. No motive or failure of all cited work follows.

An optional adjacent observation is that the PDAC subtype sentence's bib127/128 entries have colorectal-organoid titles. The report need not expand into a complete bibliography audit, and this observation does not establish that the colorectal studies are scientifically invalid.

## MAESTRO proposal and corrections

The exposure-versus-intrinsic-resistance question, suggested matched conditions, validation splits and comparators are explicitly future proposals. Mature transport, pharmacology and ABM mechanisms are acknowledged. The note claims neither an available qualified dataset, a newly admitted experiment nor a verified new mechanism. The proposed LLM measurement-selection use is conditional and includes ordinary experimental design as a rival.

Two issues in an earlier draft were corrected by the coordinator before this binding. First, `low aggregate viability response` became `weak aggregate killing`, preventing confusion between low survival and resistance. Second, the inaccurate `160` reference count was removed; direct XPath count finds157 reference entries. The current report states that complete original methods of all cited studies were not audited.

The locally saved ledger supports the exact access statements: full AIVOs JATS200, tested PDF403, older NCBI OA endpoint404, PMC HTML403 and exact ODFormer version2 JATS429. These endpoint results do not prove universal inaccessibility. Every receipt-linked saved body's hash matched its ledger entry at binding time. No network was used in this review.

Exact claim locators, material correction records and consulted-file SHA-256 bindings are in `content_bindings.json`. Only the two files in this review directory were written by this reviewer; report and sources were not edited.
