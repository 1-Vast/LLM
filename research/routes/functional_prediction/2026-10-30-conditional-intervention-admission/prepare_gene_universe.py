"""Resolve gene identities and the pre-label artifact mask from public metadata."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / "cgi_source/gene_identity.tsv"
    receipt = json.loads((ROOT / "cgi_source/candidate_7p_metadata_receipt.json").read_text())
    annotation = Path(receipt["source"])
    assert sha(annotation) == receipt["source_sha256"]
    genes = pd.read_csv(source, sep="\t", dtype=str).fillna("")
    hgnc = pd.read_csv(annotation, sep="\t", dtype=str).fillna("")
    hgnc = hgnc[hgnc.status == "Approved"]
    exact = {r["symbol"]: r for r in hgnc.to_dict("records")}
    previous, aliases = {}, {}
    for row in exact.values():
        for field, mapping in [("prev_symbol", previous), ("alias_symbol", aliases)]:
            for symbol in row[field].split("|"):
                if symbol:
                    mapping.setdefault(symbol, set()).add(row["symbol"])
    rows = []
    for raw in genes.to_dict("records"):
        old = raw["HGNC(2020)_Gene_Symbol"]
        candidates = {old} if old in exact else previous.get(old, aliases.get(old, set()))
        canonical = next(iter(candidates)) if len(candidates) == 1 else ""
        location = exact[canonical]["location"] if canonical else ""
        reason = "unmapped_or_ambiguous_identity" if not canonical else ""
        if canonical and not location:
            reason = "unknown_chromosome_location"
        if any(loc.startswith(("7p", "21q")) for loc in location.split("|")):
            reason = "predeclared_7p_or_21q_artifact_arm"
        rows.append({**raw, "canonical_gene": canonical, "location": location,
                     "reason": reason})
    frame = pd.DataFrame(rows)
    duplicate = frame.canonical_gene.duplicated(keep=False) & frame.canonical_gene.ne("")
    frame.loc[duplicate & frame.reason.eq(""), "reason"] = "multiple_source_rows_per_canonical_gene"
    frame["included"] = frame.reason.eq("")
    frame.to_csv(ROOT / "gene_universe.tsv", sep="\t", index=False, lineterminator="\n")
    included = frame.loc[frame.included, "canonical_gene"].sort_values().tolist()
    assert len(included) == len(set(included))
    record = {"scope": "identity/annotation only; no calls or response scores read",
              "source_gene_rows": len(frame), "included_gene_count": len(included),
              "excluded_reasons": frame.loc[~frame.included, "reason"].value_counts().to_dict(),
              "source_identity_sha256": sha(source), "annotation_source": str(annotation),
              "annotation_sha256": sha(annotation),
              "script_sha256": sha(Path(__file__)),
              "gene_universe_sha256": sha(ROOT / "gene_universe.tsv"),
              "included_gene_ids_sha256": hashlib.sha256("\n".join(included).encode()).hexdigest(),
              "annotation_currency": "existing public HGNC snapshot; not refreshed",
              "boundary": "Uses HGNC2020 text identity, not date-corrupted EKO fields; excludes duplicate canonical rows and known artifact arms without claiming correction completeness"}
    (ROOT / "gene_universe_freeze.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
