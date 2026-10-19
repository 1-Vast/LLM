"""Fetch Klaeger et al. 2017 (Science 358:eaan4368) kinobeads apparent Kd records from ChEMBL (document CHEMBL3991601).

Download authorised by the user on 2026-10-19 (ChEMBL REST API, CC BY-SA 3.0). Writes, once:
  data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv   one row per activity record
  data/external/klaeger2017_chembl/molecules.json                     pref name + synonyms per molecule (for mapping)
  data/external/klaeger2017_chembl/MANIFEST.json                      counts, sha256, retrieval date
Usage: python fetch_klaeger.py
"""
import csv
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/external/klaeger2017_chembl"
API = "https://www.ebi.ac.uk/chembl/api/data"
DOC = "CHEMBL3991601"
FIELDS = ["activity_id", "molecule_chembl_id", "molecule_pref_name", "target_chembl_id", "target_pref_name",
          "target_organism", "assay_chembl_id", "standard_type", "standard_relation", "standard_value", "standard_units",
          "pchembl_value", "data_validity_comment"]


def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # transient API errors: back off and retry
            if attempt == 4:
                raise
            print("retry", attempt, e, flush=True)
            time.sleep(5 * (attempt + 1))


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    csv_path = OUT / "klaeger2017_CHEMBL3991601_kd.csv"
    if csv_path.exists():
        raise SystemExit(f"{csv_path} exists (write-once)")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, offset, total = [], 0, None
    while total is None or offset < total:
        d = get(f"{API}/activity.json?document_chembl_id={DOC}&limit=1000&offset={offset}&only={','.join(FIELDS)}")
        total = d["page_meta"]["total_count"]
        rows += [{k: a.get(k) for k in FIELDS} for a in d["activities"]]
        offset += 1000
        print(f"{len(rows)}/{total}", flush=True)
    assert len(rows) == total, (len(rows), total)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    mids = sorted({r["molecule_chembl_id"] for r in rows})
    aids = sorted({r["assay_chembl_id"] for r in rows})
    mols = {}
    for i in range(0, len(mids), 50):
        d = get(f"{API}/molecule.json?molecule_chembl_id__in={','.join(mids[i:i + 50])}&limit=1000"
                f"&only=molecule_chembl_id,pref_name,molecule_synonyms")
        for m in d["molecules"]:
            mols[m["molecule_chembl_id"]] = dict(pref_name=m.get("pref_name"),
                                                 synonyms=sorted({s["molecule_synonym"] for s in m.get("molecule_synonyms") or []}))
    assays = {}
    for i in range(0, len(aids), 50):
        d = get(f"{API}/assay.json?assay_chembl_id__in={','.join(aids[i:i + 50])}&limit=1000&only=assay_chembl_id,description")
        for a in d["assays"]:
            assays[a["assay_chembl_id"]] = a["description"]
    (OUT / "molecules.json").write_text(json.dumps(dict(molecules=mols, assays=assays), indent=1), encoding="utf-8", newline="\n")
    manifest = dict(source=f"ChEMBL REST API, document {DOC} (Klaeger et al. 2017, Science 358:eaan4368, PMID 29191878)",
                    licence="CC BY-SA 3.0 (ChEMBL)", retrieved=time.strftime("%Y-%m-%d"), n_activities=len(rows),
                    n_molecules=len(mids), n_molecules_resolved=len(mols), n_assays=len(aids),
                    sha256={p.name: sha256(p) for p in (csv_path, OUT / "molecules.json")})
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
