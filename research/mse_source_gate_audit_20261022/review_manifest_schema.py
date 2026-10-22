"""Metadata-only independent manifest and composition-schema reconstruction."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/mse_source_gate_audit"
SRC = ROOT / "log/20261022/biological_decision_scout/sources"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RAW_HEADERS = ["SampleID", "Lymphocyte_act", "Lymphocyte_conv", "Macrophage_round", "Macrophage_stretched",
               "Malignant_adherent", "Malignant_colony", "Malignant_single", "Malignant_spheroid", "Other", "Unassigned"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order(namespace, values):
    return sorted(values, key=lambda value: (hashlib.sha256((namespace + "\n" + value).encode("utf-8")).hexdigest(), value))


def run():
    path = ROOT / "log/20261022/mse_source_gate/PATIENT_MENU_MANIFEST.json"
    manifest = read(path)
    for name, expected in manifest["input_hashes"].items():
        assert sha(ROOT / name) == expected
    keys = read(SRC / "MSE_KEY_AUDIT.json")
    pid = {r["sample"]: r["patient"] for r in keys["clinical_identity"]}
    experiments = {r["sample"]: r for r in keys["experiment_identity"]}
    response = keys["response_masks"]["RCN raw"]["rows"]
    eligible = sorted(r["sample"] for r in response if re.match(r"^[2-7]STP", experiments[r["sample"]]["plate"]))
    patients = order(manifest["split_namespace"], {pid[s] for s in eligible})
    partition = {p: ("source" if i < 55 else "development" if i < 75 else "later") for i, p in enumerate(patients)}
    expected_rows = [{"sample": s, "patient": pid[s], "partition": partition[pid[s]], "design": experiments[s]["plate"]} for s in eligible]
    assert manifest["rows"] == expected_rows
    assert Counter(partition.values()) == Counter(source=55, development=20, later=20)
    assert Counter(r["partition"] for r in expected_rows) == Counter(source=75, development=33, later=27)
    drugs = read(ROOT / "log/20261022/contrast_independent_review/MSE_COMMON65_UNIT_QUALIFICATION.json")["whitelist"]
    assert manifest["drugs"] == drugs
    probes = order(manifest["fixed_probe_namespace"], drugs)[:8]
    assert manifest["probes"] == probes
    assert manifest["terminal_drugs"] == sorted(set(drugs) - set(probes)) and len(manifest["terminal_drugs"]) == 57
    assert manifest["clinical_covariates_allowed"] == [] and manifest["composition_available_only_at_checkpoint"] is True
    book = SRC / "complete_members/41467_2024_52694_MOESM6_ESM.xlsx"
    schemas = {}
    with zipfile.ZipFile(book) as z:
        strings = ["".join(s.itertext()) for s in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        rel = {r.get("Id"): r.get("Target").lstrip("/") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        styles = ET.fromstring(z.read("xl/styles.xml"))
        xfs = [x.get("numFmtId") for x in styles.findall("m:cellXfs/m:xf", NS)]
        custom = {x.get("numFmtId"): x.get("formatCode") for x in styles.findall("m:numFmts/m:numFmt", NS)}
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS):
            target = rel[sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")]
            target = target if target.startswith("xl/") else "xl/" + target
            rows = ET.fromstring(z.read(target)).findall("m:sheetData/m:row", NS)
            if not rows:
                continue
            headers = []
            for c in rows[0].findall("m:c", NS):
                assert c.get("t") == "s"
                headers.append(strings[int(c.findtext("m:v", namespaces=NS))])
            ids = []
            style_counts = Counter()
            for row in rows[1:]:
                for c in row.findall("m:c", NS):
                    if re.sub(r"\d", "", c.get("r")) == "A":
                        assert c.get("t") == "s"
                        ids.append(strings[int(c.findtext("m:v", namespaces=NS))])
                    else:
                        style_counts[c.get("s", "0")] += 1
                        # Composition cell values are never accessed.
            schemas[sheet.get("name")] = {"headers": headers, "samples": len(ids), "sample_ids_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
                "styles": {key: {"cells": count, "numFmtId": xfs[int(key)], "custom_format": custom.get(xfs[int(key)])} for key, count in style_counts.items()}}
    assert schemas["Cell_type_abundance_raw"]["headers"] == RAW_HEADERS
    assert len(schemas["Cell_types_normalized"]["headers"]) == 14
    report = {"status": "PASS_METADATA_WITH_CRITICAL_PREFREEZE_SCHEMA_CORRECTION", "code_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(path), "composition_workbook_sha256": sha(book), "patient_partition_counts": dict(Counter(partition.values())),
        "sample_partition_counts": dict(Counter(r["partition"] for r in expected_rows)), "probes": probes, "terminal_actions": 57,
        "composition_sheet_schemas": schemas, "raw_composition_fields": RAW_HEADERS[1:],
        "schema_correction": "Raw sheet has10 subtype/leaf fields; normalized sheet has13 parent+subtype fields. Previous13-raw claim is corrected append-only. General numFmt0 supplies no explicit percentage/fraction storage-unit marker.",
        "source_semantics": "Primary text supplies mean fractions in24h DMSO controls and describes parent normalization for morphological subclasses in MOFA. Raw sheet label and leaf headers must be distinguished from normalized13. No raw10 sum-to-one or stored percentage conversion is inferred from observed values.",
        "assay_endpoint_values_decoded": 0, "composition_values_decoded": 0, "predictive_fits": 0, "reserve_access": 0}
    with (OUT / "MANIFEST_SCHEMA_REVIEW.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({"status": report["status"], "patients": report["patient_partition_counts"], "samples": report["sample_partition_counts"], "raw_composition_fields": 10, "numeric_decodes": 0}))


if __name__ == "__main__":
    run()
