"""Bind a manually reviewed chemical-drug whitelist to source roster/catalogues."""
import hashlib
import json
from pathlib import Path
import audit_mse_metadata as audit

# Explicit identity review, rather than inferring drug class from a dose header.
WHITELIST = set("""5-fluorouracil
Abemaciclib
Afatinib
Axitinib
Belinostat
Binimetinib
Bortezomib
Cabazitaxel
Cabozantinib
Carboplatin
Carfilzomib
Ceritinib
Cisplatin
Cobimetinib
Crizotinib
Cyclophosphamid
Dabrafenib
Dacarbazine
Dasatinib
Decitabine
Dexamethasone
Docetaxel
Elesclomol
Epacadostat
Erlotinib
Everolimus
Fotemustine
Gefitinib
Gemcitabine
Idelalisib
Ifosfamide
Imatinib
Ixazomib
Lenvatinib
Lorlatinib
Methotrexate
Midostaurin
Mln2480
Niraparib
Olaparib
Osimertinib
Oxaliplatin
Paclitaxel
Palbociclib
Panobinostat
Pazopanib
Pemetrexed
Ponatinib
Regorafenib
Ribociclib
Rucaparib
Sonidegib
Sorafenib
Temozolomide
Temsirolimus
Topotecan
Trametinib
Trifluridine
Ulixertinib
Vemurafenib
Vinblastine
Vincristine
Vindesine
Vinorelbine
Vismodegib""".splitlines())


if __name__ == "__main__":
    prior = audit.load(audit.OUT / "MSE_METADATA_RECONSTRUCTION.json")
    assert len(WHITELIST) == 65 and WHITELIST == set(prior["independently_reconstructed"]["common_drugs"])
    roster = audit.project(audit.workbook(7)["All compounds"],
                           {"drug": "A", "category": "B", "targets": "C", "vendor_catalogue": "F"}, True)
    selected = [r for r in roster if r["drug"] in WHITELIST]
    assert len(selected) == 65 and all(r["vendor_catalogue"] and "|" not in r["drug"] for r in selected)
    antibodies = [r for r in roster if r["drug"] in {"Trastuzumab", "Trastuzumab emtansine"}]
    assert len(antibodies) == 2 and not ({r["drug"] for r in antibodies} & WHITELIST)
    result = {"status": "PASS_FOR_NAMED_COMMON65_ONLY", "classification_basis": "Manual review of explicit chemical-drug identities against source All compounds names, targets and vendor/catalogue references; no antibody/co-treatment in whitelist. Source roster fields are authenticated; external vendor catalogues were not fetched or independently chemically assayed.",
              "whitelist": sorted(WHITELIST), "source_roster_references": selected, "outside_menu_antibody_entries": antibodies,
              "unit_evidence": "All whitelist identities occur under2STP's uM header at token10; every retained design has same identities/dose token10/planned wells4. Later mixed headers distinguish small-compound uM from antibody mg/ml; no blanket header inference.",
              "unresolved_outside_menu": "Primary method10ug/ml antibody statement conflicts with later-design antibody mg/ml heading; excluded from this task, no unit correction or conversion applied.",
              "assay_endpoint_casts": 0, "predictive_fits": 0, "code_sha256": audit.sha(Path(__file__)),
              "roster_workbook_sha256": audit.sha(audit.SRC / "sources/complete_members/41467_2024_52694_MOESM7_ESM.xlsx")}
    with (audit.OUT / "MSE_COMMON65_UNIT_QUALIFICATION.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"status": result["status"], "whitelist_count": 65, "outside_menu_antibodies": 2, "assay_endpoint_casts": 0}))
