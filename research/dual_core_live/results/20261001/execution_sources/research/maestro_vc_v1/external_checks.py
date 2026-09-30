"""Cross-checks against public authorities: licences, compound identifiers and target annotations.

File summary
- Path: research/maestro_vc_v1/external_checks.py
- Purpose: verify against independent public sources what the local records assert. Three checks, each a
  small metadata query and each recorded with its URL, retrieval time and checksum:
  (1) the licence of the three Figshare releases the corpus rests on, read from the Figshare API;
  (2) the connectivity block of the InChIKey of a seeded sample of compounds, from PubChem by name,
      against the block recomputed from the stored structure;
  (3) the mechanism annotation ChEMBL gives for the compounds of the genetic-pharmacological cases,
      against the annotation string the PRISM release carries in each case.
- Core points:
  - Only metadata is fetched (a few kilobytes per query); no data file is downloaded. Requests are
    rate-limited and failures are recorded, not retried into success.
  - A mismatch is a finding, not an error: a name can resolve to a salt or another stereoisomer, so the
    result reports agreement, disagreement and not-found separately, with examples.
  - Nothing found here changes a case: annotations and identifiers stay as the releases state them, and
    the report says how far an external authority agrees.
  - The sample is seeded (`SEED`) and its size fixed (`SAMPLE`) so the check can be repeated.
- Run: python -m research.maestro_vc_v1.external_checks
- Interfaces: `figshare_licences`, `pubchem_inchikey_check`, `chembl_mechanism_check`, `main`
- Depends on: urllib (standard library), pandas, rdkit, family2.py
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/external/public_checks_20260929"
SEED = 20260929
SAMPLE = 60
DELAY = 0.3
FIGSHARE = {"DepMap 24Q2 Public": 25880521, "PRISM Repurposing 19Q4": 9393293, "SciPlex3 (Srivatsan 2020)": 24681285}


def _get(url: str, timeout: float = 25.0) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "maestro-vc-v1-metadata-check/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, b""
    except Exception as error:  # network problems are recorded, not hidden
        return 0, str(error).encode()


def figshare_licences() -> list[dict]:
    out = []
    for name, article in FIGSHARE.items():
        url = f"https://api.figshare.com/v2/articles/{article}"
        status, body = _get(url)
        entry = {"release": name, "url": url, "status": status, "retrieved": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "bytes": len(body)}
        if status == 200:
            data = json.loads(body)
            entry.update({"licence": data.get("license", {}).get("name"), "licence_url": data.get("license", {}).get("url"),
                          "doi": data.get("doi"), "title": data.get("title"), "published": data.get("published_date")})
        out.append(entry)
        time.sleep(DELAY)
    return out


def _block(smiles) -> str | None:
    from research.maestro_vc_v1.preprocess import inchikey_of

    key = inchikey_of(smiles)
    return key[:14] if key else None


def pubchem_inchikey_check() -> dict:
    sp = pd.read_csv(ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv")
    from research.maestro_vc_v1 import preprocess as P

    smiles = P._l1000_smiles()
    l1 = pd.read_csv(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv")
    l1["smiles"] = [smiles.get(c) for c in l1["compound"]]
    rng = np.random.default_rng(SEED)
    rows = []
    for dataset, frame, name_col in (("sciplex3", sp, "compound"), ("l1000", l1, "name")):
        f = frame.dropna(subset=["smiles"])
        f = f[f["smiles"].astype(str).str.strip() != ""]
        pick = f.iloc[rng.choice(len(f), size=min(SAMPLE, len(f)), replace=False)]
        for r in pick.itertuples():
            name = str(getattr(r, name_col))
            url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + urllib.parse.quote(name, safe="") +
                   "/property/InChIKey/JSON")
            status, body = _get(url)
            local = _block(r.smiles)
            remote = None
            if status == 200:
                props = json.loads(body).get("PropertyTable", {}).get("Properties", [])
                keys = {p["InChIKey"][:14] for p in props if p.get("InChIKey")}
                remote = sorted(keys)
            rows.append({"dataset": dataset, "name": name, "status": status, "local_block": local, "pubchem_blocks": remote,
                         "agree": bool(remote and local in remote)})
            time.sleep(DELAY)
    df = pd.DataFrame(rows)
    found = df[df.status == 200]
    summary = {"queried": int(len(df)), "found": int(len(found)), "not_found_or_error": int((df.status != 200).sum()),
               "agree": int(found.agree.sum()), "disagree": int((~found.agree).sum()),
               "agreement_among_found": float(found.agree.mean()) if len(found) else None}
    for d, g in df.groupby("dataset"):
        f = g[g.status == 200]
        summary[d] = {"queried": int(len(g)), "found": int(len(f)), "agree": int(f.agree.sum())}
    return {"summary": summary, "rows": rows, "disagreements": [r for r in rows if r["status"] == 200 and not r["agree"]][:20]}


def chembl_mechanism_check() -> dict:
    from research.maestro_vc_v1 import family2 as F2

    seen = {}
    for row in F2.load_rows():
        if row["family"] != "genetic_pharmacological":
            continue
        for e in row["public"]["initial_evidence"]:
            m = re.search(r"annotated target ([^,]+), mechanism '([^']+)'", e.get("statement", ""))
            comp = e.get("conditions", {}).get("compound")
            if m and comp and comp not in seen:
                seen[comp] = {"prism_target": m.group(1).strip(), "prism_mechanism": m.group(2).strip()}
    rows = []
    for comp, ann in sorted(seen.items()):
        url = "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?limit=1&q=" + urllib.parse.quote(comp)
        status, body = _get(url)
        entry = {"compound": comp, **ann, "molecule_status": status, "chembl_id": None, "chembl_mechanisms": []}
        if status == 200:
            mols = json.loads(body).get("molecules", [])
            if mols:
                cid = mols[0]["molecule_chembl_id"]
                entry["chembl_id"] = cid
                entry["chembl_name"] = mols[0].get("pref_name")
                time.sleep(DELAY)
                s2, b2 = _get(f"https://www.ebi.ac.uk/chembl/api/data/mechanism.json?molecule_chembl_id={cid}&limit=20")
                entry["mechanism_status"] = s2
                if s2 == 200:
                    entry["chembl_mechanisms"] = sorted({m["mechanism_of_action"] for m in json.loads(b2).get("mechanisms", [])
                                                         if m.get("mechanism_of_action")})
        entry["exact_agreement"] = bool(ann["prism_mechanism"] in entry["chembl_mechanisms"])
        entry["target_word_agreement"] = bool(any(ann["prism_target"].split("|")[0].lower() in m.lower() for m in entry["chembl_mechanisms"]))
        rows.append(entry)
        time.sleep(DELAY)
    df = pd.DataFrame(rows)
    found = df[df.chembl_id.notna() & (df.chembl_mechanisms.map(len) > 0)]
    return {"summary": {"compounds": int(len(df)), "with_chembl_mechanism": int(len(found)),
                        "exact_string_agreement": int(found.exact_agreement.sum()),
                        "target_named_in_chembl_mechanism": int(found.target_word_agreement.sum()),
                        "no_chembl_mechanism": int(len(df) - len(found))},
            "rows": rows}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    result = {"started": started, "figshare_licences": figshare_licences(), "pubchem_inchikey": pubchem_inchikey_check(),
              "chembl_mechanism": chembl_mechanism_check(), "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "endpoints": ["https://api.figshare.com/v2/articles/<id>", "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/<name>/property/InChIKey/JSON",
                            "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json", "https://www.ebi.ac.uk/chembl/api/data/mechanism.json"],
              "note": "metadata queries only; no data file downloaded; results are external agreement checks, not corrections"}
    path = OUT / "public_checks.json"
    path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    provenance = {"file": path.name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "retrieved": started, "sources": result["endpoints"], "seed": SEED, "sample_per_dataset": SAMPLE,
                  "licence_note": "each service's own terms apply; only small metadata responses are stored (summaries and identifiers)"}
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=1), encoding="utf-8")
    print(json.dumps({"figshare": [(r["release"], r.get("licence")) for r in result["figshare_licences"]],
                      "pubchem": result["pubchem_inchikey"]["summary"], "chembl": result["chembl_mechanism"]["summary"]}, indent=1))


if __name__ == "__main__":
    main()
