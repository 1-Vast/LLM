"""Curated evidence records for the AURORA-A known-case sources (G0).

Every record is a hand extraction from the full text of two open-access papers (Europe PMC
full-text XML, retrieved 2026-10-19; digests below). Values that the text states are copied;
values that live only in figures or in supplementary files that were not read are marked
`numeric_extracted: False`. Nothing here is interpolated, normalised or borrowed across
conditions. `locator` names the figure, legend, table or Methods passage the record rests on.
"""

# Evidence types are kept apart on purpose (verification test F).
OBSERVED = "OBSERVED_EXPERIMENTAL_RESULT"
ANNOTATION = "BIOLOGICAL_ANNOTATION"
MECH_REF = "MECHANISTIC_REFERENCE"
PREDICTION = "MODEL_PREDICTION"
CONFIRMATION = "INDEPENDENT_CONFIRMATION"
EVIDENCE_TYPES = (OBSERVED, ANNOTATION, MECH_REF, PREDICTION, CONFIRMATION)

SOURCES = {
    "S1": {
        "title": "Adhikari, Bozilovic et al. 2020, Nat Chem Biol: AURORA-A degrader (JB170, JB211, alisertib)",
        "pmcid": "PMC7610535",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7610535/",
        "retrieved_from": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7610535/fullTextXML",
        "retrieved_on": "2026-10-19",
        "xml_sha256": "b73d60d507b006af73fae8a31ff6106834731e78f20a76ad299d215ec1c4f57b",
        "data_deposits": {"GEO": "GSE141911", "PRIDE": ["PXD017342", "PXD019585", "PXD019684"]},
        "source_data_for_terminal_endpoints": "none listed for Extended Data Figs 7-8; Source Data exist for Fig 1, 2, 4, 5 and ED 1-6",
        "status": "KNOWN_CASE_LOGIC_ONLY",
        "read_by_designer": True,
    },
    "S2": {
        "title": "O'Hanlon et al. 2026, J Med Chem: JB170 to CCT400028, Aurora A degrader probe",
        "pmcid": "PMC12833858",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12833858/",
        "retrieved_from": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12833858/fullTextXML",
        "retrieved_on": "2026-10-19",
        "xml_sha256": "811eec00c6498a37dc086977a01b0333454d57774d65ff82cb7e4af03e6de815",
        "data_deposits": {"supporting_information": ["jm5c03024_si_001.pdf", "jm5c03024_si_002.xlsx", "jm5c03024_si_003.csv"]},
        "source_data_for_terminal_endpoints": "viability curves are in Figure S7 of the SI PDF, which was not read; only GI50 values from the main text are recorded",
        "status": "KNOWN_CASE_LOGIC_ONLY",
        "read_by_designer": True,
        "doi_note": "DOI differs across aggregators (10.1021/acs.jmedchem.5c03024 per PMC and the Chemical Probes Portal); the journal page returned HTTP 403 and was not read",
    },
}

# Intervention method / pharmacological implementation (levels 1 and 2 of the four-level model).
COMPOUNDS = {
    "alisertib": {"method": "chemical", "mode": "atp_competitive_kinase_inhibition", "note": "warhead of the degraders; raises AURKA protein level (S1 Fig 2c text)"},
    "JB170": {"method": "chemical", "mode": "crbn_recruiting_degrader", "note": "alisertib-thalidomide conjugate (S1 cmpd 5); also an AURKA binder"},
    "JB158": {"method": "chemical", "mode": "crbn_recruiting_degrader", "note": "S1 cmpd 4; three ethylene glycol units"},
    "JB211": {"method": "chemical", "mode": "crbn_null_aurka_binder_control",
              "note": "S1 cmpd 6; methylated glutarimide, cannot bind CRBN; text says it binds AURKA but does not mediate degradation; AURKA binding/inhibition by JB211 is asserted, no assay extracted; NOT a pharmacologically inactive control"},
    "JB160": {"method": "chemical", "mode": "vhl_recruiting_degrader_inactive", "note": "S1 cmpd 2; did not reduce AURKA (Fig 1b)"},
    "JB161": {"method": "chemical", "mode": "vhl_recruiting_degrader_inactive", "note": "S1 cmpd 3; did not reduce AURKA (Fig 1b)"},
    "CCT400028": {"method": "chemical", "mode": "crbn_recruiting_degrader", "note": "S2; phenyl dihydrouracil CRBN warhead, hook effect reduced"},
    "cmpd50": {"method": "chemical", "mode": "crbn_recruiting_degrader", "note": "S2 piperazine-linker analogue"},
    "cmpd57": {"method": "chemical", "mode": "crbn_null_matched_control", "note": "S2; N-methylated CRBN warhead matched control of CCT400028; tested for AURKA depletion only"},
    "AURKA_siRNA": {"method": "siRNA", "mode": "genetic_knockdown", "note": "S1 ED6f-h; cell line and knockdown efficiency not extracted"},
    "AURKA_T217D": {"method": "engineered_resistance_mutant", "mode": "rescue_construct", "note": "S1; lowers alisertib-type binding; not depleted by JB170; used as on-target rescue"},
}


def R(rid, src, loc, role, evtype, compound, cell, genotype, dose_uM, time_h, readout, result, n, n_kind,
      numeric, uncertainty, lineage, note=""):
    return {
        "id": rid, "source": src, "locator": loc, "level": role, "evidence_type": evtype,
        "compound": compound, "cell": cell, "genotype": genotype, "dose_uM": dose_uM, "time_h": time_h,
        "readout": readout, "result": result, "n": n, "n_kind": n_kind,
        "numeric_extracted": numeric, "uncertainty_reported": uncertainty, "lineage": lineage, "note": note,
    }


NR = "not_reported"
L_S1_TMT = {"cell_stock": NR, "batch": "S1 IMR5 TMT11plex batch 1 (JB170 x4 [rep4 excluded], JB211 x3, alisertib x4)", "plate": NR}
L_NONE = {"cell_stock": NR, "batch": NR, "plate": NR}

RECORDS = [
    # ---- S1 proximal ----
    R("S1-R01", "S1", "Fig 2a text", "proximal", OBSERVED, "JB170", "MV4-11", "HiBiT-AURKA", "series", 6, "HiBiT AURKA level (DC50, DCmax)",
      {"DC50_nM": 28, "DC50_sd_nM": 4, "DCmax_uM": 0.3, "hook_effect_from_uM": 10}, 3, "unspecified", True, True, L_NONE),
    R("S1-R02", "S1", "Fig 2c (legend + text)", "proximal", OBSERVED, "JB170", "MV4-11", "WT", "series_not_extracted", 6, "AURKA immunoblot",
      {"direction": "decrease"}, None, "not_extracted", False, False, L_NONE, "same blot as R03 and R04: JB170 vs JB211 vs alisertib"),
    R("S1-R03", "S1", "Fig 2c (legend + text)", "proximal", OBSERVED, "JB211", "MV4-11", "WT", "series_not_extracted", 6, "AURKA immunoblot",
      {"direction": "increase_vs_vehicle"}, None, "not_extracted", False, False, L_NONE),
    R("S1-R04", "S1", "Fig 2c text ('similar to that observed for alisertib')", "proximal", OBSERVED, "alisertib", "MV4-11", "WT", "series_not_extracted", 6, "AURKA immunoblot",
      {"direction": "increase_vs_vehicle"}, None, "not_extracted", False, False, L_NONE),
    R("S1-R05", "S1", "Fig 3b; ED3a; Supp Table 1", "proximal", OBSERVED, "JB170", "HEK293T", "WT", "series", 2, "NanoBRET AURKA target engagement",
      {"EC50_nM": 193}, 2, "biological", True, False, L_NONE, "JB211 value not in the text read"),
    R("S1-R06", "S1", "Fig 3b; ED3a; Supp Table 1", "proximal", OBSERVED, "alisertib", "HEK293T", "WT", "series", 2, "NanoBRET AURKA target engagement",
      {"EC50_nM": 18}, 2, "biological", True, False, L_NONE),
    R("S1-R07", "S1", "Fig 3a text; Dataset 1", "proximal", OBSERVED, "alisertib", "lysate (kinobeads)", "WT", "series", None, "kinobeads AURKA Kd app",
      {"Kd_app_nM": 7}, None, "not_extracted", True, False, L_NONE),
    R("S1-R08", "S1", "Fig 3a text; Dataset 1", "proximal", OBSERVED, "JB170", "lysate (kinobeads)", "WT", "series", None, "kinobeads AURKA Kd app",
      {"Kd_app_nM": 99}, None, "not_extracted", True, False, L_NONE),
    R("S1-R09", "S1", "ED3f-h; Methods (TMT)", "proximal", OBSERVED, "JB170", "IMR5", "WT", 1.0, 6, "TMT proteome (6485 proteins)",
      {"direction": "AURKA specifically depleted vs JB211 and vs alisertib"}, 3, "technical_batch_channels", False, True, L_S1_TMT, "4 channels, replicate 4 excluded as technical outlier"),
    R("S1-R10", "S1", "ED3f-h; Methods (TMT)", "proximal", OBSERVED, "JB211", "IMR5", "WT", 1.0, 6, "TMT proteome (6485 proteins)",
      {"direction": "AURKA not depleted"}, 3, "technical_batch_channels", False, True, L_S1_TMT),
    R("S1-R11", "S1", "ED3f-h; Methods (TMT)", "proximal", OBSERVED, "alisertib", "IMR5", "WT", 1.0, 6, "TMT proteome (6485 proteins)",
      {"direction": "AURKA not depleted"}, 4, "technical_batch_channels", False, True, L_S1_TMT),
    R("S1-R12", "S1", "Fig 3c text; Dataset 2", "proximal", OBSERVED, "JB170", "MV4-11", "WT", 0.1, 6, "SILAC proteome",
      {"AURKA_change_vs_alisertib_pct": -73, "AURKA_change_vs_untreated_pct": -57}, 3, "biological", True, True, L_NONE, "alisertib concentration in this comparison not extracted"),
    R("S1-R13", "S1", "Fig 3d, ED3e", "proximal", OBSERVED, "JB170", "MV4-11", "WT", 0.1, 6, "CRBN neosubstrate abundance (GSPT1, CSNK1A1, ZFP91, IKZF1/3)",
      {"direction": "not destabilised"}, 3, "biological", False, True, L_NONE, "absence of known neosubstrate loss does not exclude unknown CRBN off-targets"),
    R("S1-R14", "S1", "ED2g,h,j,k,l", "control", OBSERVED, "JB170", "MV4-11", "WT", 0.1, 6, "AURKA depletion with competitor / MG132 / MLN4924",
      {"direction": "depletion abolished by alisertib, thalidomide, MG132 or MLN4924"}, None, "not_extracted", False, False, L_NONE),
    # ---- S1 terminal ----
    R("S1-R20", "S1", "Fig 5a", "terminal", OBSERVED, "alisertib", "MV4-11", "WT", 1.0, 12, "cell cycle (BrdU-PI)",
      {"direction": "G2/M arrest"}, None, "not_extracted", False, False, L_NONE),
    R("S1-R21", "S1", "Fig 5a", "terminal", OBSERVED, "JB170", "MV4-11", "WT", 0.5, 12, "cell cycle (BrdU-PI)",
      {"direction": "S-phase arrest, BrdU-negative cells"}, None, "not_extracted", False, False, L_NONE, "0.5 uM vs 1 uM alisertib: dose-mismatched"),
    R("S1-R22", "S1", "Fig 5b; GEO GSE141911", "terminal", OBSERVED, "alisertib", "MV4-11", "WT", 1.0, 18, "RNA-seq GSEA Fischer G2/M",
      {"direction": "G2/M gene set induced"}, None, "not_extracted", False, True, L_NONE),
    R("S1-R23", "S1", "Fig 5b; GEO GSE141911", "terminal", OBSERVED, "JB170", "MV4-11", "WT", 0.1, 18, "RNA-seq GSEA Fischer G2/M",
      {"direction": "G2/M gene set not induced"}, None, "not_extracted", False, True, L_NONE, "0.1 uM vs 1 uM alisertib: dose-mismatched"),
    R("S1-R24", "S1", "Fig 5d,e", "terminal", OBSERVED, "alisertib", "IMR5", "AURKA_T217D_Dox", 1.0, 18, "cell cycle (BrdU-PI)",
      {"direction": "phenotype reported in T217D vs EtOH panel; direction not extracted"}, None, "not_extracted", False, False, L_NONE),
    R("S1-R25", "S1", "Fig 5e", "terminal", OBSERVED, "JB170", "IMR5", "AURKA_T217D_Dox", 1.0, 18, "cell cycle (BrdU-PI)",
      {"direction": "S-phase arrest reverted by T217D"}, None, "not_extracted", False, False, L_NONE),
    R("S1-R26", "S1", "ED6f-h", "genetic", OBSERVED, "AURKA_siRNA", "not_extracted", "WT", None, None, "cell cycle (BrdU-PI)",
      {"direction": "S-phase accumulation of BrdU-negative cells, similar to JB170"}, None, "not_extracted", False, False, L_NONE,
      "cell cycle only; no genetic viability or apoptosis reference was found"),
    R("S1-R27", "S1", "Fig 6a", "terminal", OBSERVED, "JB170", "MV4-11", "WT", 1.0, 72, "alamarBlue viability",
      {"viable_pct_of_control": 32}, 3, "replicate_experiments", True, True, L_NONE, "no alisertib or JB211 arm in this panel"),
    R("S1-R28", "S1", "Fig 6c", "terminal", OBSERVED, "JB170", "MV4-11", "WT", 0.5, 72, "annexin/PI apoptosis",
      {"annexin_pos_pct": 56}, 1, "performed_once", True, False, L_NONE),
    R("S1-R29", "S1", "Fig 6d; ED7a,b", "terminal", OBSERVED, "JB170", "IMR5", "AURKA_T217D_Dox_vs_EtOH", "0.5;1.0", 72, "annexin/PI apoptosis",
      {"direction": "apoptosis induced in EtOH cells, reverted by T217D"}, 3, "biological", False, True, L_NONE, "values are bars in the figure; no source data for ED7"),
    R("S1-R30", "S1", "Fig 6d; ED7a,b", "terminal", OBSERVED, "JB211", "IMR5", "AURKA_T217D_Dox_vs_EtOH", "0.5;1.0", 72, "annexin/PI apoptosis",
      {"direction": "no significant apoptosis"}, 3, "biological", False, True, L_NONE, "absence of significance with n=3; effect size not extracted"),
    R("S1-R31", "S1", "ED7d", "terminal", OBSERVED, "JB211", "IMR5", "AURKA_T217D_Dox_vs_EtOH", "0.5;1.0", 72, "alamarBlue viability",
      {"direction": "no significant reduction"}, 3, "replicate_experiments", False, True, L_NONE, "two-tailed unpaired t-test; effect size not extracted"),
    R("S1-R32", "S1", "ED7d (design); text states JB170 apoptosis/viability phenotype", "terminal", OBSERVED, "JB170", "IMR5", "AURKA_T217D_Dox_vs_EtOH", "0.5;1.0", 72, "alamarBlue viability",
      {"direction": "plotted in the same panel; direction not stated in the text read"}, 3, "replicate_experiments", False, True, L_NONE),
    # ---- S2 ----
    R("S2-R01", "S2", "Table 5; Table 1", "proximal", OBSERVED, "CCT400028", "MV4-11", "HiBiT-AURKA", "series", 6, "HiBiT AURKA level",
      {"DC50_nM": 29, "Dmax_pct": 85, "hook_effect": False}, 3, "biological", True, False, L_NONE),
    R("S2-R02", "S2", "Table 1; Results and Introduction", "proximal", OBSERVED, "JB170", "MV4-11", "HiBiT-AURKA", "series", 6, "HiBiT AURKA level",
      {"DC50_nM": 39, "DC50_nM_alt_intro": 28, "Dmax_pct": 69, "hook_effect": True}, 3, "biological", True, False, L_NONE, "internal inconsistency 39 vs 28 nM within the paper"),
    R("S2-R03", "S2", "Fig 8", "proximal", OBSERVED, "CCT400028", "Kelly", "WT", 1.0, 4, "proteomics AURKA, N-Myc, AURKB, CDK9, GSPT1",
      {"direction": "AURKA depleted more than by JB170; N-Myc, AURKB, CDK9, GSPT1 not depleted"}, 3, "independent_experiments", False, True, L_NONE),
    R("S2-R04", "S2", "Fig 8", "proximal", OBSERVED, "JB170", "Kelly", "WT", 1.0, 4, "proteomics AURKA, N-Myc, AURKB, CDK9, GSPT1",
      {"direction": "AURKA depleted; others not depleted"}, 3, "independent_experiments", False, True, L_NONE),
    R("S2-R05", "S2", "Fig S10", "control", OBSERVED, "cmpd57", "Kelly", "WT", "up_to_10", None, "AURKA immunoblot",
      {"direction": "no AURKA reduction up to 10 uM"}, None, "not_extracted", False, False, L_NONE, "no viability readout for 57 in the text read"),
    R("S2-R06", "S2", "Fig 10", "control", OBSERVED, "CCT400028", "Kelly", "WT", 1.0, 4, "AURKA depletion with MG132 / MLN4924 / CC220 / alisertib",
      {"direction": "depletion blocked by all four"}, 3, "biological", False, True, L_NONE),
    R("S2-R07", "S2", "Fig 9A,B", "proximal", OBSERVED, "CCT400028", "kinome panel", "WT", 1.0, None, "97-kinase binding; AURKB Kd",
      {"direction": "AURKA only kinase <35% control", "AURKB_Kd_nM": 2100}, 2, "biological", True, False, L_NONE),
    R("S2-R08", "S2", "Fig S7A,B; main text", "terminal", OBSERVED, "JB170", "MV4-11", "WT", "series", 72, "alamarBlue viability GI50",
      {"GI50_nM": 1100}, None, "not_extracted", True, False, L_NONE, "curve and uncertainty in SI Fig S7 (not read)"),
    R("S2-R09", "S2", "Fig S7A,B; main text", "terminal", OBSERVED, "CCT400028", "MV4-11", "WT", "series", 72, "alamarBlue viability GI50",
      {"GI50_nM": 310}, None, "not_extracted", True, False, L_NONE),
    R("S2-R10", "S2", "Fig S7A,B; main text", "terminal", OBSERVED, "cmpd50", "MV4-11", "WT", "series", 72, "alamarBlue viability GI50",
      {"GI50_nM": 130}, None, "not_extracted", True, False, L_NONE),
    # ---- annotation-only items ----
    {"id": "S1-A01", "source": "S1", "locator": "Fig 1b", "level": "annotation", "evidence_type": ANNOTATION, "compound": "JB158", "note": "second CRBN degrader, 62% reduction at a single dose; no terminal data"},
    {"id": "S1-A02", "source": "S1", "locator": "Fig 1b", "level": "annotation", "evidence_type": ANNOTATION, "compound": "JB160", "note": "VHL-based, inactive in degradation"},
    {"id": "S1-A03", "source": "S1", "locator": "Fig 1b", "level": "annotation", "evidence_type": ANNOTATION, "compound": "JB161", "note": "VHL-based, inactive in degradation"},
    {"id": "S2-A01", "source": "S2", "locator": "Table 1, 3, 5", "level": "annotation", "evidence_type": ANNOTATION, "compound": "S2 analogues 42-56", "note": "linker and warhead variants; HiBiT and CRBN FP only"},
    {"id": "S1-M01", "source": "S1", "locator": "Fig 4a,b; ED2m,n", "level": "mechanism_reference", "evidence_type": MECH_REF, "compound": "AURKA mutants",
     "note": "CRBN-interface mutants abolish JB170 depletion; kinase-dead D274N/K162R are depleted as WT: depletion does not need catalytic activity"},
]

# Condition mismatches and unsupported linkages that the reconstruction found (G0 deliverable B).
MISMATCHES = [
    {"id": "M01", "what": "S1 alisertib vs JB170 cell-cycle comparison uses 1 uM vs 0.5 uM (Fig 5a) and RNA-seq 1 uM vs 0.1 uM (Fig 5b)", "effect": "descriptive only; no dose-matched phenotype contrast"},
    {"id": "M02", "what": "S1 has no alisertib arm for viability or apoptosis; Fig 6a is JB170 alone and ED7d is JB170 vs JB211 in IMR5", "effect": "no matched terminal endpoint for inhibition vs degradation in any single cell context"},
    {"id": "M03", "what": "S1 JB211 has no MV4-11 terminal arm and no cell-cycle arm; JB211 AURKA binding/inhibition is asserted in text, no JB211 NanoBRET or kinase-activity value was found", "effect": "JB211 cannot be treated as inactive; whether it inhibits catalytic activity at assay doses is an open premise"},
    {"id": "M04", "what": "S1 and S2 share only JB170 and MV4-11; S1 viability is one dose over a time course (1 uM), S2 is a 72 h GI50 series", "effect": "terminal readouts are not poolable across papers"},
    {"id": "M05", "what": "S2 JB170 HiBiT DC50 is 39 nM in Results and 28 nM in the Introduction; S1 reports 28 nM", "effect": "cross-paper proximal anchor is internally inconsistent"},
    {"id": "M06", "what": "S2 contains no JB211 and no alisertib comparator arm; alisertib appears only as a rescue competitor (Fig 10)", "effect": "S2 cannot supply an inhibition arm"},
    {"id": "M07", "what": "S2 control 57 is tested for AURKA depletion only (Kelly); no viability value for 57", "effect": "CCT400028 terminal effect has no non-degrading matched control"},
    {"id": "M08", "what": "S2 proximal work is in Kelly (4 h) and HiBiT MV4-11 (6 h); terminal work is MV4-11 (72 h)", "effect": "no cell context carries both proximal and terminal readouts for CCT400028 except MV4-11 HiBiT + GI50"},
    {"id": "M09", "what": "S1 genetic reference is siRNA cell-cycle only (ED6f-h); no knockdown viability, apoptosis, CRISPR or kinase-dead replacement phenotype", "effect": "genetic reference does not cover the terminal endpoint"},
    {"id": "M10", "what": "S1 ED7 has no Source Data file; terminal bars are not machine-extractable from the text", "effect": "numeric values for the JB170/JB211 pair are missing"},
    {"id": "M11", "what": "S1 TMT proteomics puts JB170, JB211 and alisertib in one TMT11 batch", "effect": "contrasts share batch and controls; they are not independent replicates of each other"},
    {"id": "M12", "what": "Fig 6c apoptosis, ED1g, ED2q,r and ED7c were performed once", "effect": "no replicate structure for these records"},
]

# Units (task-level). The primary endpoint is declared before eligibility is computed.
UNITS = [
    {
        "unit_id": "U1_IMR5_AURKA_JB170_JB211_alisertib",
        "task": "AURKA dependency in IMR5 neuroblastoma cells: which implementation (CRBN degrader, inhibitor, or neither) explains and should carry apoptosis/viability loss",
        "target": "AURKA", "context": {"cell": "IMR5", "genotype_axis": "AURKA_T217D_Dox vs EtOH"},
        "implementations": ["alisertib", "JB170", "JB211"],
        "primary_terminal_endpoint": {"readout": "alamarBlue viability / annexin-PI apoptosis", "time_h": 72},
        "proximal_readout": "TMT proteome (AURKA abundance)",
        "genetic_reference_records": ["S1-R26"],
        "discriminating_control_records": ["S1-R25", "S1-R29", "S1-R30", "S1-R31"],
        "record_ids": ["S1-R09", "S1-R10", "S1-R11", "S1-R24", "S1-R25", "S1-R26", "S1-R29", "S1-R30", "S1-R31", "S1-R32"],
        "mechanism_contrasts": ["degradation_vs_inhibition", "on_target_vs_off_target"],
    },
    {
        "unit_id": "U2_MV411_AURKA_JB170_alisertib",
        "task": "AURKA phenotype comparison in MV4-11: inhibition (G2/M) vs degradation (S phase), descriptive",
        "target": "AURKA", "context": {"cell": "MV4-11", "genotype_axis": "WT"},
        "implementations": ["alisertib", "JB170"],
        "primary_terminal_endpoint": {"readout": "cell cycle (BrdU-PI)", "time_h": 12},
        "proximal_readout": "HiBiT / immunoblot / SILAC AURKA abundance",
        "genetic_reference_records": ["S1-R26"],
        "discriminating_control_records": ["S1-R14"],
        "record_ids": ["S1-R01", "S1-R02", "S1-R04", "S1-R12", "S1-R20", "S1-R21", "S1-R22", "S1-R23", "S1-R27", "S1-R28"],
        "mechanism_contrasts": ["degradation_vs_inhibition"],
    },
    {
        "unit_id": "U3_MV411_AURKA_CCT400028_JB170",
        "task": "Optimised degrader vs original degrader on AURKA depletion and viability in MV4-11, with a CRBN-null matched control for depletion",
        "target": "AURKA", "context": {"cell": "MV4-11", "genotype_axis": "WT"},
        "implementations": ["CCT400028", "JB170", "cmpd50"],
        "primary_terminal_endpoint": {"readout": "alamarBlue viability GI50", "time_h": 72},
        "proximal_readout": "HiBiT AURKA level",
        "genetic_reference_records": [],
        "discriminating_control_records": ["S2-R05", "S2-R06"],
        "record_ids": ["S2-R01", "S2-R02", "S2-R03", "S2-R04", "S2-R05", "S2-R06", "S2-R07", "S2-R08", "S2-R09", "S2-R10"],
        "mechanism_contrasts": ["degradation_dependence"],
    },
]

# Legal assay bundles for the task of unit U1 (G0 deliverable F). Cost fields are null where the
# papers give no price or turnaround: they are missing, not zero. `outcome_in_records` says whether
# the evaluator vault can release a real published outcome.
ACTIONS = [
    {"action_id": "A_JB211_VIAB", "purpose": "JB211 (CRBN-null AURKA binder) viability and apoptosis in IMR5, next to JB170 positive control",
     "conditions": {"cell": "IMR5", "dose_uM": [0.5, 1.0], "time_h": 72, "genotype": "AURKA_T217D EtOH (WT AURKA expressed)"},
     "controls": ["vehicle", "JB170 positive control"], "replicates": 3, "arms": 6, "wells_min": 18, "wells_note": "arms x replicates; technical wells per arm not reported",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "separates catalytic/binder-driven loss from degradation-driven loss (conditional on A_JB211_ENGAGE premise)",
     "outcome_in_records": True, "record_ids": ["S1-R30", "S1-R31"]},
    {"action_id": "A_T217D_RESCUE", "purpose": "JB170 apoptosis/viability in IMR5 cells expressing T217D (Dox) versus control (EtOH)",
     "conditions": {"cell": "IMR5", "dose_uM": [0.5, 1.0], "time_h": 72, "genotype": "AURKA_T217D_Dox vs EtOH"},
     "controls": ["vehicle", "EtOH vs Dox arms"], "replicates": 3, "arms": 6, "wells_min": 18, "wells_note": "arms x replicates; technical wells per arm not reported",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "separates AURKA-binding-dependent loss from AURKA-independent loss; does not separate degradation from catalytic inhibition",
     "outcome_in_records": True, "record_ids": ["S1-R29"]},
    {"action_id": "A_ALI_VIAB", "purpose": "Alisertib viability and apoptosis in IMR5 at the same doses and time as the JB170/JB211 panel",
     "conditions": {"cell": "IMR5", "dose_uM": [0.5, 1.0], "time_h": 72, "genotype": "EtOH (WT AURKA)"},
     "controls": ["vehicle", "JB170 positive control"], "replicates": 3, "arms": 6, "wells_min": 18, "wells_note": "arms x replicates",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "completes the matched three-way terminal endpoint; discriminating only if viability is preserved",
     "outcome_in_records": False, "record_ids": []},
    {"action_id": "A_JB211_ENGAGE", "purpose": "JB211 AURKA target engagement and catalytic inhibition (pT288 autophosphorylation, NanoBRET) at assay doses",
     "conditions": {"cell": "IMR5", "dose_uM": [0.5, 1.0], "time_h": 2, "genotype": "WT"},
     "controls": ["vehicle", "alisertib positive control", "JB170"], "replicates": 3, "arms": 8, "wells_min": 24, "wells_note": "arms x replicates",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "resolves whether JB211 inhibits the catalytic activity; a premise for reading A_JB211_VIAB",
     "outcome_in_records": False, "record_ids": []},
    {"action_id": "A_AURKA_KD_VIAB", "purpose": "AURKA knockdown or knockout viability and apoptosis in IMR5",
     "conditions": {"cell": "IMR5", "time_h": 72, "genotype": "AURKA knockdown vs non-targeting"},
     "controls": ["non-targeting control", "second independent guide or siRNA"], "replicates": 3, "arms": 6, "wells_min": 18, "wells_note": "arms x replicates",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "genetic reference for loss of the protein; does not separate degradation from catalytic loss",
     "outcome_in_records": False, "record_ids": []},
    {"action_id": "A_KINASE_DEAD_REPLACE", "purpose": "AURKA knockdown rescued by wild-type or kinase-dead AURKA (e.g. D274N or K162R) in IMR5",
     "conditions": {"cell": "IMR5", "time_h": 72, "genotype": "knockdown plus replacement constructs"},
     "controls": ["non-targeting", "wild-type replacement", "empty vector"], "replicates": 3, "arms": 8, "wells_min": 24, "wells_note": "arms x replicates",
     "cost_currency": None, "turnaround_days": None, "expected_contrast": "separates scaffold-type (non-catalytic) loss from catalytic loss",
     "outcome_in_records": False, "record_ids": []},
]
