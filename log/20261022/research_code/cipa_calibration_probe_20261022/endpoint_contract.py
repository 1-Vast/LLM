"""Strict source/dev OOXML census; no later outcome decoding and no fitting."""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "log/20261022/next_asset/sources"
OUT = ROOT / "log/20261022/cipa_calibration_probe"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SPLITS = {**{str(i): "source" for i in range(1, 6)}, "6": "dev", "7": "dev", "8": "later", "9": "later", "10": "excluded_sequential"}
HEADER = ["Drug_Name", "Cell_type", "risk", "Platform", "Type_of_EADs", "conc", "EAD", "ddFPDc", "site"]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)


def raw_cell(cell, shared):
    if cell is None:
        return {"type": None, "raw": None, "text": None, "formula": None}
    value = cell.find("s:v", NS)
    raw = value.text if value is not None else None
    kind = cell.get("t")
    if kind == "s" and raw is not None:
        text = shared[int(raw)]
    elif kind == "inlineStr":
        text = "".join(cell.find("s:is", NS).itertext()) if cell.find("s:is", NS) is not None else ""
    else:
        text = raw
    formula = cell.find("s:f", NS)
    return {"type": kind, "raw": raw, "text": text, "formula": ET.tostring(formula, encoding="unicode") if formula is not None else None}


def outcome(cell, shared, binary):
    raw = raw_cell(cell, shared)
    if raw["formula"] is not None:
        return raw, "illegal_formula", None
    if raw["text"] in (None, ""):
        return raw, "missing", None
    if raw["type"] not in (None, "n"):
        return raw, "illegal_type", None
    try:
        value = Decimal(raw["text"])
    except InvalidOperation:
        return raw, "illegal_decimal", None
    if not value.is_finite():
        return raw, "illegal_nonfinite", None
    if binary and value not in (Decimal(0), Decimal(1)):
        return raw, "illegal_nonbinary", None
    if not math.isfinite(float(value)):
        return raw, "illegal_float_overflow", None
    return raw, "valid", value


def main():
    contract = OUT / "ENDPOINT_CONTRACT.md"
    inputs = {"workbook": SOURCE / "cipa_blinova_workbook.body", "dose_mapping": SOURCE / "CIPA_PHYSICAL_DOSE_MAPPING.json", "author_xml": SOURCE / "cipa_multisite_primary_fulltext.body", "contract": contract, "code": Path(__file__)}
    write("ENDPOINT_INPUT_SEAL.json", {name: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)} for name, path in inputs.items()})
    mapping_rows = json.loads(inputs["dose_mapping"].read_text(encoding="utf-8"))["rows"]
    mapping = {row["drug"]: row for row in mapping_rows}
    assert len(mapping) == len(mapping_rows) == 28
    assert all(set(row["dose_code_to_uM_string"]) == {"1", "2", "3", "4"} for row in mapping_rows)
    with zipfile.ZipFile(inputs["workbook"]) as archive:
        shared = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    xml_rows = sheet.findall("s:sheetData/s:row", NS)
    header = {"".join(c for c in cell.get("r") if c.isalpha()): raw_cell(cell, shared)["text"] for cell in xml_rows[0].findall("s:c", NS)}
    assert [header.get(chr(65 + i)) for i in range(9)] == HEADER
    bundles = defaultdict(list)
    all_identities = Counter()
    identity_rows = Counter()
    records, anomalies, aliases = [], [], []
    contact_counts = Counter()
    source_quotes = []
    author = ET.fromstring(inputs["author_xml"].read_bytes())
    for p in author.iter("p"):
        text = " ".join("".join(p.itertext()).split())
        if any(x in text for x in ("Arrhythmia was a binary outcome", "Single concentrations of each drug", "Drug-induced arrhythmia-like eventswere counted")):
            source_quotes.append(text)
    for row in xml_rows[1:]:
        cells = {"".join(c for c in cell.get("r") if c.isalpha()): cell for cell in row.findall("s:c", NS)}
        identity = {col: raw_cell(cells.get(col), shared)["text"] for col in ("A", "B", "D", "F", "I")}
        if not identity["A"]:
            continue
        original_name = identity["A"]
        drug = "D,l Sotalol" if original_name == "D,l,Sotalol" else original_name
        if original_name != drug:
            aliases.append({"row": row.get("r"), "original": original_name, "canonical": drug})
        site, cell, platform, code = identity["I"], identity["B"], identity["D"], identity["F"]
        assert site in SPLITS and code in {"1", "2", "3", "4"}
        assert drug in mapping and code in mapping[drug]["dose_code_to_uM_string"]
        key = (site, cell, platform, drug, code)
        split = SPLITS[site]
        all_identities[key] += 1
        identity_rows[split] += 1
        if split not in ("source", "dev"):
            continue  # Do not access G/H/E here: reserved and sequential rows are identities only.
        record = {"row": row.get("r"), "site": site, "cell": cell, "platform": platform, "drug": drug, "dose_code": code, "split": split, "ead": None, "ddfpdc": None}
        for column, field, binary in (("G", "ead", True), ("H", "ddfpdc", False)):
            contact_counts[split] += 1
            raw, status, value = outcome(cells.get(column), shared, binary)
            record[field + "_raw"] = raw
            record[field + "_status"] = status
            record[field] = float(value) if value is not None else None
            if status != "valid":
                anomalies.append({"row": row.get("r"), "key": list(key), "split": split, "field": field, "status": status, "raw": raw})
        records.append(record)
        bundles[key].append(record)
    assert len(all_identities) == 1679 and sum(all_identities.values()) == 8859
    menus = defaultdict(set)
    for key in all_identities:
        menus[key[:-1]].add(key[-1])
    missing = [{"key": list(k), "available_codes": sorted(v)} for k, v in menus.items() if v != {"1", "2", "3", "4"}]
    assert missing == [{"key": ["3", "CDI", "MCS", "Ibutilide"], "available_codes": ["2", "3", "4"]}]
    aggregate = []
    for key, rows in sorted(bundles.items()):
        site, cell, platform, drug, code = key
        ead = [Decimal(r["ead_raw"]["text"]) for r in rows if r["ead_status"] == "valid"]
        duration = [Decimal(r["ddfpdc_raw"]["text"]) for r in rows if r["ddfpdc_status"] == "valid"]
        aggregate.append({"bundle_id": "|".join(key), "site": site, "cell": cell, "platform": platform, "drug": drug, "dose_code": code, "split": SPLITS[site], "nominal_uM_string": mapping[drug]["dose_code_to_uM_string"][code], "cmax_uM_string": mapping[drug]["cmax_uM_string"], "row_ids": [r["row"] for r in rows], "n_rows": len(rows), "n_ead_valid": len(ead), "n_ddfpdc_valid": len(duration), "ead_mean": float(sum(ead) / len(ead)) if ead else None, "ddfpdc_mean": float(sum(duration) / len(duration)) if duration else None, "ead_available_fraction": len(ead) / len(rows), "ddfpdc_available_fraction": len(duration) / len(rows)})
    statuses = {field: dict(Counter(r[field + "_status"] for r in records)) for field in ("ead", "ddfpdc")}
    illegal = [row for row in anomalies if row["status"] != "missing"]
    audit = {"status": "PASS" if not illegal else "STOP_ILLEGAL_OUTCOMES", "zero_fits": True, "header": header, "source_quotes": source_quotes, "identity_rows_by_split": dict(identity_rows), "identity_bundles_by_split": dict(Counter(SPLITS[k[0]] for k in all_identities)), "source_dev_outcome_contacts_by_split": dict(contact_counts), "later_outcome_contacts": 0, "excluded_outcome_contacts": 0, "later_outcome_numeric_casts": 0, "excluded_outcome_numeric_casts": 0, "all_rows": sum(all_identities.values()), "all_canonical_bundles": len(all_identities), "aliases": aliases, "nonfour_menus": missing, "statuses": statuses, "illegal_count": len(illegal), "source_dev_bundles": len(aggregate), "source_dev_rows": len(records), "targets": ["ead_mean", "ddfpdc_mean", "ddfpdc_available_fraction"], "raw_workbook_and_published_supplement_designer_exposed": True, "notes": "Counts of released rows are not independent biological replicates. Availability means exported finite numeric H, not authenticated physiological cause. Later and sequential outcomes skipped before raw cell decoding."}
    write("SOURCE_DEV_ROWS.json", {"rows": records})
    write("SOURCE_DEV_BUNDLES.json", {"bundles": aggregate})
    write("ENDPOINT_ANOMALIES.json", {"records": anomalies})
    write("ENDPOINT_SCHEMA_AUDIT.json", audit)
    write("ENDPOINT_ARTIFACT_SEAL.json", {name: digest(OUT / name) for name in ("SOURCE_DEV_ROWS.json", "SOURCE_DEV_BUNDLES.json", "ENDPOINT_ANOMALIES.json", "ENDPOINT_SCHEMA_AUDIT.json", "ENDPOINT_INPUT_SEAL.json")})
    print(json.dumps({k: v for k, v in audit.items() if k not in ("source_quotes", "header")}, indent=2))
    if illegal:
        raise SystemExit("Illegal source/dev outcomes retained; stop before fitting.")


if __name__ == "__main__":
    main()
