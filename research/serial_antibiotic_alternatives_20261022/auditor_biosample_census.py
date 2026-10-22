"""Identity-only census from approved BioSample projection; no source payload parse."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "log/20261022/serial_antibiotic_alternatives"
OUT = BASE / "biosample_identity_followup"


def main():
    target = OUT / "IDENTITY_CENSUS.json"
    if target.exists():
        raise RuntimeError("BioSample census exists")
    source = OUT / "IDENTITY_METADATA.json"
    samples = json.loads(source.read_text(encoding="utf-8"))["samples"]
    expected = json.loads((BASE / "manifest_followup/amendment2_sources/RELATION_SUMMARY.json").read_text(encoding="utf-8"))["unique_linked_BioSample_Entrez_ids"]
    mappings, attributes, prefixes, title_withheld = [], Counter(), Counter(), 0
    for sample in samples:
        names = [r["value"] for r in sample["sample_name_ids"] if not r["withheld"]]
        identity = {r["attribute_name"]: r["value"] for r in sample["strain_isolate_sample_identity"] if not r["withheld"]}
        mappings.append({"entrez_id": sample["entrez_id"], "accession": sample["accession"],
                         "sample_name_ids": names, "strain_isolate_identity": identity,
                         "title_withheld": sample["title"]["withheld"]})
        for name in names:
            prefixes["-".join(name.split("-")[:2])] += 1
        attributes.update(r["attribute_name"] for r in sample["attribute_names"])
        title_withheld += sample["title"]["withheld"]
    actual = [s["entrez_id"] for s in samples]
    result = {"returned_records": len(samples), "unique_entrez_ids": len(set(actual)),
              "unique_accessions": len({s["accession"] for s in samples}),
              "missing_requested_entrez_ids": sorted(set(expected) - set(actual)),
              "unexpected_entrez_ids": sorted(set(actual) - set(expected)),
              "attribute_name_record_counts": dict(attributes),
              "literal_first_two_hyphen_token_counts": dict(prefixes),
              "prefix_abbreviations_semantically_decoded": False,
              "titles_withheld_by_predeclared_phenotype_guard": title_withheld,
              "taxonomy_counts": dict(Counter(str(s["taxonomy"]) for s in samples)),
              "owner_name_counts": dict(Counter(s["owner"]["name"] if s["owner"] else None for s in samples)),
              "collection_date_counts": dict(Counter(d["value"] for s in samples for d in s["collection_dates"])),
              "sample_identity_mapping": mappings,
              "explicit_loop_stage_figure_row_or_first_retry_attribute_names": [n for n in attributes if any(token in n.casefold() for token in ["loop", "stage", "figure", "row", "retry", "attempt", "lineage", "parent", "ancestor", "passage", "generation"])],
              "sample_names_alone_certify_figure_S1_strain_row_and_stage_join": False,
              "21_records_are_21_founders_backgrounds_or_tasks": False,
              "input_projection_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
