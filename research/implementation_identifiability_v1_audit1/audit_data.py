"""Curated audit findings (hand-recorded from the full text, the SI PDFs and the supplementary tables that were read).

Vocabulary for every item (the five audit grades):
  not_read                    the material exists but was not read or could not be retrieved
  not_reported                the material was read and does not contain the item
  reported_qualitatively      stated in words or a significance statement only
  numeric_without_uncertainty a number is available without replicate spread or interval
  numeric_with_uncertainty    values with replicate channels, SEM/SD or an interval are available
"""

HEAD_AT_AUDIT_START = "f997c157c1b6b01026652beb0d4fc49879199086"
V1_BASE_COMMIT = "f997c157c1b6b01026652beb0d4fc49879199086"

MATERIAL_READ = {
    "S1": {
        "full_text": "Europe PMC full-text XML PMC7610535 (digest in v1 records.py), whole text including Methods and Extended Data legends",
        "supplement_files_read": [
            "Supplementary_Information_.pdf (synthesis, docking, modelling; 4 mentions of JB211, none of activity)",
            "Supp_Data_Set_3 (IMR5 TMT, AURKA channels extracted)", "Supp_Data_Set_2 (SILAC; catalogued, not mined)", "Supp_Table_2 (reagents; truncated tail, not used)",
            "Source_Data_Fig_1, 2, 4, 5 and Source_Data_ED_2, 4, 5 (PDF uncropped immunoblots; images, no numbers)",
            "Extended_Data_Figure_1-8 EPS (raster figure images)"],
        "not_read": [
            "Supp_Table_1 (BRET EC50 values): served by neither the Europe PMC bundle nor the PMC bin route; the PMC route returned a JavaScript 'Preparing to download' interstitial, which was not bypassed",
            "Supp_Data_Set_1 (kinobeads) and Supp_Data_Set_4 (interactome): not in the bundle, same PMC gate",
            "Source Data for ED1, ED3, ED6 and for Fig 6 / ED7: not published (listed Source Data covers Fig 1, 2, 4, 5 and ED 1-6 only in the paper; the bundle held Fig 1, 2, 4, 5 and ED 2, 4, 5)",
            "numeric values read off figure images (bar heights): not done by rule; figure interpretation is not a substitute for a measurement"],
    },
    "S2": {
        "full_text": "Europe PMC full-text XML PMC12833858 (digest in v1 records.py); the publisher page returned HTTP 403 and was not read",
        "supplement_files_read": [
            "jm5c03024_si_001.pdf (Figures S1-S11, Tables S1-S4, methods)", "jm5c03024_si_002.xlsx (Kelly proteomics, three sheets: CCT400028, 50, JB170)",
            "jm5c03024_si_003.csv (compound SMILES and HiBiT summary)"],
        "not_read": [
            "numeric pGI50 +- SEM in Figure S7B: shown as a figure image only; not digitised",
            "immunoblot images in Figures S8, S10, S11: not interpreted"],
    },
}

# ---- item-level audit of what the task asked to check -------------------------------------------
S1_ITEMS = [
    {"id": "S1-I01", "item": "ED7 numerical values and uncertainty", "values": "not_reported", "uncertainty_definition": "reported_qualitatively",
     "overall": "reported_qualitatively",
     "evidence": "ED7d legend: mean +- s.d. of n=3 replicate experiments, two-tailed unpaired t-test; values only as bars in a raster EPS; no Source Data for ED7 (supplement listing and bundle)",
     "consequence": "ED7d/6d outcomes cannot enter a quantitative unit"},
    {"id": "S1-I02", "item": "Fig 6 terminal values", "values": "numeric_without_uncertainty", "overall": "numeric_without_uncertainty",
     "evidence": "6a: 32% viable at 72 h, JB170 1 uM, MV4-11 (text; s.d. n=3 only in the plot); 6c: 56% annexin-positive at 72 h, 0.5 uM, performed once (Methods); 6d: bars, mean +- s.e.m. n=3 (legend), values not given",
     "consequence": "JB170 alone; no alisertib or JB211 arm in 6a/6c; 6d values not recoverable"},
    {"id": "S1-I03", "item": "JB170 / JB211 / alisertib matched conditions", "overall": "reported_qualitatively",
     "evidence": "matched in one place only: IMR5, 1 uM, 6 h TMT proteome, one TMT11 batch, no vehicle channel (numeric, SI DS3). Terminal: JB170 vs JB211 matched in IMR5, 72 h, 0.5 and 1 uM (qualitative); alisertib has no 72 h arm; alisertib vs JB170 cell cycle is matched at 1 uM, 18 h in IMR5 T217D panel (direction not extracted) and mismatched at 1 vs 0.5 uM, 12 h in MV4-11",
     "consequence": "no cell context carries all three on one terminal endpoint"},
    {"id": "S1-I04", "item": "cell line, genotype, dose, exposure time, assay lineage", "overall": "reported_qualitatively",
     "evidence": "cell line, genotype, dose and time reported per figure legend; Methods: cells from the Eilers laboratory (acknowledgement), routine mycoplasma PCR; cell-stock identity, authentication, passage, plate and culture-initiation dates not reported; replicate kind only partly labelled (biological / technical / once)",
     "consequence": "lineage not reconstructable; L3e fails"},
    {"id": "S1-I05", "item": "direct JB211 target engagement", "overall": "not_reported",
     "evidence": "no JB211 NanoBRET, kinobeads or occupancy value in text, SI PDF (0 IC50 mentions) or readable supplements; BRET values are in Supp Table 1, which was not read (not_read); docking of JB211 (ED4e) is a model, not engagement",
     "consequence": "AURKA binding of JB211 rests on an authors' statement; Supp Table 1 is the one open lead"},
    {"id": "S1-I06", "item": "direct JB211 catalytic activity", "overall": "not_reported",
     "evidence": "no pT288, substrate-phosphorylation or kinase assay for JB211 in text, SI PDF (0 pT288 and 0 kinase-assay mentions); AURKA abundance rises with JB211 and alisertib, which is abundance, not activity",
     "consequence": "catalytic inhibition by JB211 is an unresolved premise"},
    {"id": "S1-I07", "item": "genetic AURKA loss on the same terminal endpoint", "overall": "reported_qualitatively",
     "evidence": "siRNA gives S-phase accumulation similar to JB170 (ED6f-h; cell cycle only, cell line and knockdown efficiency not extracted); no knockdown viability or apoptosis; Source Data for ED6 not served",
     "consequence": "no genetic reference on viability/apoptosis; L3f fails"},
    {"id": "S1-I08", "item": "rescue controls and expression / localisation controls", "overall": "reported_qualitatively",
     "evidence": "doxycycline-inducible HA-AURKA T217D and wild-type lines in IMR5; JB170 depletion of T217D 'largely abrogated' (Fig 5c, blot); wild-type overexpression also rescues the S-phase arrest (ED6c-e), so rescue partly reflects overexpression; T217D lowers binding of an alisertib analogue (cited), JB170 binding to T217D not measured in read material; expression relative to endogenous and subcellular localisation of the HA proteins not reported",
     "consequence": "T217D rescue is limited on-target evidence; it does not exclude degradation-specific effects, off-target effects or expression confounding"},
]

S2_ITEMS = [
    {"id": "S2-I01", "item": "Fig S7 viability curves and uncertainty", "overall": "numeric_without_uncertainty",
     "evidence": "SI Fig S7: representative curves, mean +- SEM of n=3 technical repeats; GI50 geometric mean and pGI50 mean +- SEM over 3 biological repeats in panel B, which is an image; main-text GI50 values (JB170 1100, CCT400028 310, 50 130 nM) carry no SEM",
     "consequence": "uncertainty exists in the source but was not recovered as numbers"},
    {"id": "S2-I02", "item": "compound 57 terminal phenotype", "overall": "not_reported",
     "evidence": "SI Fig S10: AURKA immunoblot at 4 and 24 h in Kelly, 2 independent experiments; no viability or any terminal readout for 57 anywhere in text or SI (0 viability mentions within 300 characters of '57')",
     "consequence": "57 is a CRBN-null matched control for degradation only"},
    {"id": "S2-I03", "item": "matched controls", "overall": "reported_qualitatively",
     "evidence": "57 matched to CCT400028 for AURKA depletion (Kelly); rescue competitors MG132, MLN4924, CC220, alisertib (Fig 10; Fig S11C,D in KNS-42); no CRBN-null control for JB170 or 50; none at the terminal endpoint",
     "consequence": "degradation dependence is controlled; terminal phenotype is not"},
    {"id": "S2-I04", "item": "shared terminal endpoint among CCT400028, JB170, 57 and an inhibition comparator", "overall": "reported_qualitatively",
     "evidence": "MV4-11 72 h alamarBlue GI50 shared by JB170, CCT400028 and 50; 57 absent; alisertib is only a rescue competitor; no genetic comparator",
     "consequence": "no matched inhibitor or genetic terminal comparison"},
    {"id": "S2-I05", "item": "proximal and terminal measurements in one background and compatible window", "overall": "reported_qualitatively",
     "evidence": "HiBiT-AURKA MV4-11 6 h (engineered reporter line) and MV4-11 72 h viability (line identity as reporter or parental not stated); Kelly 4 h proteomics and Western with no Kelly terminal readout",
     "consequence": "proximal/terminal context compatibility not established"},
    {"id": "S2-I06", "item": "lineage and replicate metadata", "overall": "reported_qualitatively",
     "evidence": "Kelly and KNS-42 sourced from DSMZ and JCRB, SNP authentication, mycoplasma screening; HiBiT n per compound in SI Table S1 (JB170 n=5, CCT400028 n=3, 50 n=3); GI50 3 biological repeats; Kelly proteomics 3 independent experiments; the three proteomics sheets share the same DMSO channels (a shared control, not three controls); stock, passage and plate not reported",
     "consequence": "dependence structure partly recoverable; lineage still incomplete"},
    {"id": "S2-I07", "item": "internal consistency of numbers", "overall": "numeric_with_uncertainty",
     "evidence": "JB170 HiBiT DC50 39 nM in Results/SI Table S1, 28 nM in the Introduction; SI csv DC50 for 44, 48 and 49 (35, 47, 50) differs from SI Table S1 (37, 48, 48)",
     "consequence": "treat HiBiT summary numbers as approximate across SI files"},
]

CANDIDATE_UNIT_FIELDS = ("target", "target_family", "cell_background", "genotype", "intervention_method", "concrete_compounds", "modality", "nominal_dose_uM",
                         "exposure_time_h", "proximal_readout", "terminal_readout", "controls", "replicate_structure", "lineage", "source_locator_and_hash",
                         "publication_exposure_status", "costs_and_turnaround")

CANDIDATES = [
    {"unit_id": "U1_IMR5_AURKA_JB170_JB211_alisertib", "target": "AURKA", "target_family": "Aurora kinase (serine/threonine kinase)",
     "cell_background": "IMR5 neuroblastoma", "genotype": "WT; doxycycline-inducible HA-AURKA T217D vs EtOH control for the 72 h panel",
     "intervention_method": "chemical (small molecule), engineered resistance mutant for rescue",
     "concrete_compounds": ["alisertib", "JB170", "JB211"], "modality": ["ATP-competitive inhibition", "CRBN-recruiting degradation", "CRBN-null close analog"],
     "nominal_dose_uM": "1 (TMT 6 h); 0.5 and 1 (72 h JB170 / JB211); 1 (cell cycle 18 h)", "exposure_time_h": "6 (TMT), 18 (cell cycle), 72 (viability/apoptosis)",
     "proximal_readout": "TMT proteome AURKA abundance (numeric, 3-4 channels, one batch, no vehicle)", "terminal_readout": "alamarBlue viability and annexin/PI apoptosis (JB170, JB211 only; qualitative)",
     "controls": ["T217D rescue", "JB211 CRBN-null analog", "EtOH vs Dox"], "replicate_structure": "TMT channels n=3/3/4 in one batch; viability n=3 replicate experiments; apoptosis n=3 biological",
     "lineage": "TMT batch known; cell stock, passage, plate not reported", "source_locator_and_hash": "S1 ED3f-h, Fig 6d, ED7a,b,d, SI DS3 (see supplement_extracts.json)",
     "publication_exposure_status": "published; read by the designer; KNOWN_CASE_LOGIC_ONLY", "costs_and_turnaround": "not reported; wells design-derived in v1 actions"},
    {"unit_id": "U2_MV411_AURKA_JB170_alisertib", "target": "AURKA", "target_family": "Aurora kinase (serine/threonine kinase)",
     "cell_background": "MV4-11 leukaemia", "genotype": "WT; HiBiT-AURKA reporter line for HiBiT", "intervention_method": "chemical",
     "concrete_compounds": ["alisertib", "JB170"], "modality": ["ATP-competitive inhibition", "CRBN-recruiting degradation"],
     "nominal_dose_uM": "alisertib 1 vs JB170 0.5 (12 h cell cycle); 1 vs 0.1 (18 h RNA-seq)", "exposure_time_h": "6 (proximal), 12 and 18 (phenotype), 72 (viability JB170 only)",
     "proximal_readout": "HiBiT, immunoblot, SILAC AURKA abundance", "terminal_readout": "cell cycle (qualitative), RNA-seq GSEA (qualitative), viability JB170 only",
     "controls": ["alisertib / thalidomide / MG132 / MLN4924 competition for degradation"], "replicate_structure": "mixed; cell cycle replicate count not extracted; apoptosis performed once",
     "lineage": "not reported", "source_locator_and_hash": "S1 Fig 2, 3, 5a,b, 6a,c", "publication_exposure_status": "published; read by the designer; KNOWN_CASE_LOGIC_ONLY",
     "costs_and_turnaround": "not reported"},
    {"unit_id": "U3_MV411_AURKA_CCT400028_JB170", "target": "AURKA", "target_family": "Aurora kinase (serine/threonine kinase)",
     "cell_background": "MV4-11 (HiBiT, viability); Kelly neuroblastoma (proteomics, Western, rescue); KNS-42 glioma (Western)", "genotype": "HiBiT-AURKA reporter for HiBiT; others unmodified",
     "intervention_method": "chemical", "concrete_compounds": ["CCT400028", "JB170", "compound 50", "compound 57 (control)"],
     "modality": ["CRBN-recruiting degradation", "CRBN-null matched control (57)"], "nominal_dose_uM": "series (HiBiT, GI50); 1 (Kelly proteomics); up to 10 (57)",
     "exposure_time_h": "6 (HiBiT), 4 and 24 (Kelly), 72 (viability)", "proximal_readout": "HiBiT DC50/Dmax with n; Kelly proteomics AURKA channels (numeric, 3 experiments, shared DMSO)",
     "terminal_readout": "alamarBlue GI50 (JB170, CCT400028, 50; no SEM in text)", "controls": ["57 for degradation only", "MG132, MLN4924, CC220, alisertib competition"],
     "replicate_structure": "HiBiT n=3-5 biological; GI50 3 biological, curves n=3 technical; proteomics n=3 independent", "lineage": "cell sources and authentication reported; stock, passage, plate not reported",
     "source_locator_and_hash": "S2 Tables 1, 3, 5, Fig 8, Fig S7, S10, SI Table S1, si_002.xlsx", "publication_exposure_status": "published; read by the designer; KNOWN_CASE_LOGIC_ONLY",
     "costs_and_turnaround": "not reported"},
    {"unit_id": "C4_KELLY_PROTEOMICS_CCT400028_JB170_50", "target": "AURKA", "target_family": "Aurora kinase (serine/threonine kinase)",
     "cell_background": "Kelly neuroblastoma", "genotype": "unmodified", "intervention_method": "chemical", "concrete_compounds": ["CCT400028", "JB170", "compound 50"],
     "modality": ["CRBN-recruiting degradation"], "nominal_dose_uM": "1", "exposure_time_h": "4", "proximal_readout": "proteomics AURKA, 3 experiments, shared DMSO",
     "terminal_readout": "none", "controls": ["DMSO shared across the three compounds"], "replicate_structure": "3 independent experiments",
     "lineage": "not reported", "source_locator_and_hash": "S2 SI xlsx", "publication_exposure_status": "published; read by the designer; KNOWN_CASE_LOGIC_ONLY",
     "costs_and_turnaround": "not reported", "note": "proximal only; no terminal endpoint, so it is not a task unit"},
]

# JB211 premise status: variables kept separate. `status` uses the audit vocabulary.
JB211_STATUS = {
    "wording": None,  # filled from audit_logic.JB211_WORDING
    "variables": {
        "crbn_recruitment": {"status": "reported_qualitatively", "evidence": "by design (N-methylated glutarimide) and authors' statement; co-IP with JB211 exists in ED5c, result not read from the blot image",
                             "direct_measurement": "not_read"},
        "aurka_occupancy_or_binding": {"status": "reported_qualitatively", "evidence": "Results text says JB211 'binds AURORA-A but does not mediate its degradation'; no JB211 binding value found; BRET values are in Supp Table 1 (not_read); docking is a model",
                                       "direct_measurement": "not_reported (read material); Supp Table 1 not_read"},
        "intracellular_exposure": {"status": "not_reported", "evidence": "no exposure, permeability or cellular concentration measurement", "direct_measurement": "not_reported"},
        "catalytic_activity": {"status": "not_reported", "evidence": "no pT288, substrate phosphorylation or kinase assay for JB211 in text or SI PDF", "direct_measurement": "not_reported"},
        "protein_abundance": {"status": "numeric_with_uncertainty",
                              "evidence": "IMR5, 1 uM, 6 h TMT: AURKA log2 reporter JB211 18.88 +- 0.03 (n=3) vs JB170 17.74 (n=3) vs alisertib 19.31 (n=4), one batch, no vehicle channel; MV4-11 immunoblot: JB211 and alisertib raise AURKA (qualitative)",
                              "direct_measurement": "SI Supp Data Set 3"},
        "terminal_phenotype": {"status": "reported_qualitatively",
                               "evidence": "IMR5, 72 h, 0.5 and 1 uM: no significant apoptosis (Fig 6d) and no significant viability reduction (ED7d), n=3, two-tailed t-test; no equivalence margin, interval or detection limit",
                               "direct_measurement": "not_reported (numeric)"},
    },
    "premise_P_catalytic_inhibition_by_JB211": "UNRESOLVED",
    "forbidden_inferences": [
        "catalytic inhibition from structural analogy to the alisertib warhead",
        "catalytic inhibition from the rise in AURKA abundance",
        "catalytic inhibition from a binary 'engaged' observation or from occupancy alone",
        "absence of terminal effect from 'no significant' without an equivalence margin or detection limit",
        "JB211 as a fully inactive or pharmacologically inert control",
    ],
    "pT288_note": "pT288 is a context-dependent activity proxy (cell-cycle dependent), not universal target engagement; occupancy, pT288, validated kinase activity, abundance and exposure are separate variables",
    "t217d_note": "T217D rescue is limited on-target evidence: wild-type overexpression also rescues, JB170 binding to T217D and HA-protein localisation are not reported, so it does not exclude degradation-specific effects, off-target effects or expression confounding",
}

CCT57_STATUS = {
    "compound": "57 (N-methylated CRBN warhead matched control of CCT400028)",
    "role": "CRBN-null matched control for AURKA degradation",
    "degradation_result": {"status": "reported_qualitatively", "evidence": "SI Fig S10: no AURKA reduction up to 10 uM at 4 and 24 h in Kelly, representative of 2 independent experiments (blot image, not interpreted)"},
    "terminal_functional_result": {"status": "not_reported",
                                   "evidence": "no viability, apoptosis, cell-cycle or other terminal readout for 57 in the text, SI PDF or proteomics workbook; 57 is not in Fig S7 or in the proteomics sheets"},
    "terminal_inactivity_claim_allowed": False,
    "why": "absence of AURKA depletion does not establish terminal inactivity: 57 may still bind AURKA and inhibit it, or have CRBN-independent effects",
    "other_controls_for_CCT400028": "MG132, MLN4924, CC220 and alisertib competition (degradation dependence only)",
}
