"""Independent identity/design/storage-mask audit; never casts an assay value."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "log/20261022/biological_decision_scout"
OUT = ROOT / "log/20261022/contrast_independent_review"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workbook(number):
    path = SRC / f"sources/complete_members/41467_2024_52694_MOESM{number}_ESM.xlsx"
    with zipfile.ZipFile(path) as z:
        strings = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        rels = {r.get("Id"): r.get("Target").lstrip("/") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        result = {}
        for s in ET.fromstring(z.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS):
            target = rels[s.get(REL)]
            target = target if target.startswith("xl/") else "xl/" + target
            result[s.get("name")] = (strings, ET.fromstring(z.read(target)).findall("m:sheetData/m:row", NS))
        return result


def cells(row):
    return {re.sub(r"\d", "", c.get("r")): c for c in row.findall("m:c", NS)}


def text(cell, strings, design_token=False):
    if cell is None:
        return None
    if cell.get("t") == "s":
        # Integer conversion is a shared-string index, never an assay scalar.
        return strings[int(cell.findtext("m:v", namespaces=NS))]
    if cell.get("t") == "inlineStr":
        return "".join(cell.find("m:is", NS).itertext())
    if design_token:
        return cell.findtext("m:v", namespaces=NS)
    raise AssertionError("Non-string data outside whitelisted design metadata")


def project(sheet, columns, numeric_design=False):
    strings, rows = sheet
    return [{name: text(cells(row).get(col), strings, numeric_design) for name, col in columns.items()}
            for row in rows[1:] if any(cells(row).get(col) is not None for col in columns.values())]


def run():
    initial_seal = load(SRC / "INDEPENDENT_SEAL.json")
    assert sha(ROOT / initial_seal["path"]) == initial_seal["sha256"]
    for name, expected in initial_seal["evidence_hashes"].items():
        assert sha(SRC / name) == expected, name
    sources = SRC / "sources"
    archive = sources / "mse_europepmc_supplements_complete_attempt.body"
    assert archive.stat().st_size == 98664660
    assert sha(archive) == "c774c7780eef81ddd22d5f716a481df2930064eaba3f7f7c5dcd384784072c2e"
    manifest = load(sources / "mse_complete_zip_manifest.json")
    core_hashes = {}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.infolist()) == len(manifest) == 32
        assert [{"name": m.filename, "size": m.file_size, "compressed": m.compress_size} for m in z.infolist()] == manifest
        for n in range(4, 9):
            name = f"41467_2024_52694_MOESM{n}_ESM.xlsx"
            p = sources / "complete_members" / name
            core_hashes[name] = sha(p)
            assert p.read_bytes() == z.read(name), name
    assert sha(sources / "mse_primary.body") == "b9241d6bb66eb57ae8fed6c463c1e771f5838e77f4854bc3ec22c6b243289c7d"
    clinical = project(workbook(4)["Clinical data"], {"sample": "A", "patient": "B", "sample_type": "E", "tumor_type": "F"})
    experiments = project(workbook(5)["Experiment details"], {"experiment": "A", "sample": "B", "plate": "C", "storage": "E", "protocol": "F"}, True)
    controls = project(workbook(6)["Cell_type_abundance_raw"], {"sample": "A"})
    prior = load(sources / "MSE_KEY_AUDIT.json")
    assert clinical == prior["clinical_identity"] and experiments == prior["experiment_identity"]
    assert len({r["sample"] for r in clinical}) == len(clinical) == 150
    assert len({r["experiment"] for r in experiments}) == len({r["plate"] for r in experiments}) == 150
    masks, slot_counts, storage_types, formulas = {}, {}, Counter(), 0
    for name, (strings, rows) in workbook(8).items():
        if not rows:
            continue
        headers = {col: text(c, strings) for col, c in cells(rows[0]).items()}
        drugs = {col: name for col, name in headers.items() if col != "A"}
        entries, counts = [], Counter()
        for row in rows[1:]:
            cs = cells(row)
            sample = text(cs["A"], strings)
            available, other = [], []
            for col, drug in drugs.items():
                c = cs.get(col)
                numeric = c is not None and c.get("t") in (None, "n") and c.find("m:v", NS) is not None
                counts["numeric_slot" if numeric else "nonnumeric_missing_or_annotation"] += 1
                (available if numeric else other).append(drug)
                storage_types[str(None if c is None else c.get("t"))] += 1
                formulas += int(c is not None and c.find("m:f", NS) is not None)
                # No outcome cell <v> text is read, printed or converted.
            entries.append({"sample": sample, "numeric_slot_drugs": available, "other_drugs": other})
        assert entries == prior["response_masks"][name]["rows"]
        assert list(drugs.values()) == prior["response_masks"][name]["drugs"]
        assert dict(counts) == prior["summary"]["per_sheet_slot_types"][name]
        masks[name], slot_counts[name] = entries, dict(counts)
    assert set(masks) == {"RCN raw", "RCN scaled", "RCF raw", "RCF scaled"}
    assert all(rows == masks["RCN raw"] for rows in masks.values())
    ids = {r["sample"] for r in masks["RCN raw"]}
    pid = {r["sample"]: r["patient"] for r in clinical}
    counts = Counter(pid[s] for s in ids)
    assert len(ids) == len({r["sample"] for r in controls}) == 149
    assert ids == {r["sample"] for r in controls}
    assert set(pid) - ids == {"FB209"}
    assert len(counts) == 105 and Counter(counts.values()) == Counter({1: 80, 2: 12, 3: 9, 4: 2, 5: 2})
    common = set.intersection(*(set(r["numeric_slot_drugs"]) for r in masks["RCN raw"]))
    assert len(common) == 65 and sorted(common) == prior["summary"]["all_sample_numeric_slot_drugs"]
    ex = {r["sample"]: r for r in experiments}
    late = {s for s in ids if re.match(r"^[2-7]STP", ex[s]["plate"])}
    early = ids - late
    assert all(ex[s]["plate"].startswith("STP") for s in early)
    assert len(late) == 135 and len({pid[s] for s in late}) == 95 and len(early) == 14
    design_audit = load(sources / "MSE_COMMON_ACTION_DESIGN.json")
    assert sorted(early) == design_audit["excluded_early_multidose_samples"]
    design_headers = {}
    for name, sheet in workbook(7).items():
        if name not in {"STP", "2STP", "3STP", "4STP", "5STP", "6STP", "7STP"}:
            continue
        strings, rows = sheet
        headers = [text(c, strings) for c in cells(rows[0]).values()]
        design_headers[name] = headers
        expected_unit = "Concentration [uM]" if name in {"STP", "2STP"} else "Concentration [uM for small compounds, mg/ml for antibodies]"
        assert headers == ["Compound", expected_unit, "No. replicate wells"]
        design = project(sheet, {"drug": "A", "concentration_token": "B", "replicate_wells_token": "C"}, True)
        selected = [r for r in design if r["drug"] in common]
        assert selected == design_audit["designs"][name]
        if name != "STP":
            assert Counter(r["drug"] for r in selected) == Counter({d: 1 for d in common})
            assert all(r["concentration_token"] == "10" and r["replicate_wells_token"] == "4" for r in selected)
    method = load(sources / "MSE_METHOD_CONTRACT.json")
    primary = ET.fromstring((sources / "mse_primary.body").read_bytes())
    method_checks = {}
    for title, excerpt in method.items():
        found = [sec for sec in primary.iter("sec") if sec.find("title") is not None and "".join(sec.find("title").itertext()) == title]
        assert len(found) == 1, title
        original = "".join(found[0].itertext())
        method_checks[title] = re.sub(r"\s+", "", original) == re.sub(r"\s+", "", excerpt)
        assert method_checks[title], title
    report = {"status": "PASS", "audit_code_sha256": sha(Path(__file__)), "initial_seal_and_core_artifacts": "PASS",
        "archive_bytes": archive.stat().st_size, "archive_members": 32, "all_archive_CRCs": "PASS", "core_member_hashes": core_hashes,
        "independently_reconstructed": {"clinical_samples": 150, "full_functional_samples": 149, "full_functional_patients": 105,
        "patients_with_repeats": 25, "sample_count_distribution": dict(Counter(counts.values())), "late_samples": 135, "late_patients": 95,
        "excluded_early_samples": sorted(early), "common_drugs": sorted(common), "late_designs": 6, "common_dose_uM_token": "10", "planned_technical_wells_token": "4"},
        "storage_masks_equal_across_four_sheets": True, "slot_counts": slot_counts, "storage_type_counts": dict(storage_types),
        "design_headers": design_headers, "method_contract_matches_original_primary_sections": method_checks,
        "unit_scope": "Named common65 occur in2STP under uM header; later designs mix small-compound uM and antibody mg/ml labels. Primary methods state antibody ug/ml. Do not extend10uM to all later-panel entries or silently reconcile antibody units.",
        "outcome_formula_cell_count": formulas, "assay_endpoint_value_casts": 0, "outcome_cell_v_text_accesses": 0,
        "predictive_fits": 0, "reserve_access": 0,
        "limits": "Storage coverage is not finite-value/biological/QC eligibility. Dose/well counts are design metadata, not effective retained replicates. No numerical control compositions or RCN/RCF responses were decoded."}
    with (OUT / "MSE_METADATA_RECONSTRUCTION.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({"status": "PASS", "samples": 149, "patients": 105, "late_samples": 135, "late_patients": 95, "common_drugs": 65, "assay_value_casts": 0}))


if __name__ == "__main__":
    run()
