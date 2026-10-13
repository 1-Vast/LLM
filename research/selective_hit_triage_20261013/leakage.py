"""Metadata-only leakage audit of the development/test split (no outcome is read).

File summary
- Path: research/selective_hit_triage_20261013/leakage.py
- Purpose: find the routes by which development information could reach a test compound, and fix
  the sensitivity subset before the freeze.
- Checks:
  - Identity: no connectivity block or CTRP compound id in both splits.
  - Structure: the nearest development neighbour of each test compound, by Tanimoto similarity of
    Morgan radius-2 2048-bit fingerprints. Test compounds at or above 0.7 are CLOSE_ANALOGUE;
    those at or above 0.4 (about the top 5%) are dropped in the S12 sensitivity analysis.
  - Mechanism: the split is by MoA family, so no MoA string is shared. Test compounds sharing an
    annotated target gene with development are listed and dropped in the other S12 analysis.
  - Context: every cell line appears in both splits by design, because the task is to triage new
    compounds on a known panel. Line-level information therefore crosses the split; this is the
    route the memory arms use deliberately.
- Output: LEAKAGE.json.
"""
from __future__ import annotations

import json

from census import HERE

CLOSE, SIMILAR = 0.7, 0.4


def main() -> None:
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    census = {r["core"]: r for r in json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))["compounds"]}
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def fp(core):
        smiles = max(str(census[core]["smiles"]).split(","), key=len)
        mol = Chem.MolFromSmiles(smiles)
        return gen.GetFingerprint(mol) if mol is not None else None

    dev, test = split["development"], split["test"]
    fdev = {c: fp(c) for c in dev}
    nearest = {}
    for c in test:
        f = fp(c)
        if f is None:
            nearest[c] = {"similarity": None, "neighbour": None}
            continue
        sims = {d: DataStructs.TanimotoSimilarity(f, g) for d, g in fdev.items() if g is not None}
        d = max(sims, key=lambda k: (sims[k], k))
        nearest[c] = {"similarity": round(sims[d], 4), "neighbour": d, "neighbour_name": census[d]["name"], "name": census[c]["name"]}
    dev_targets = {g for c in dev for g in census[c]["targets"]}
    dev_moas = {m for c in dev for m in census[c]["moas"]}
    out = {
        "label": "metadata only; no CTRP response value read",
        "shared_connectivity": sorted({census[c]["connectivity"] for c in dev} & {census[c]["connectivity"] for c in test} - {None}),
        "shared_ctrp_compound_ids": sorted({census[c]["ctrp_master_cpd_id"] for c in dev} & {census[c]["ctrp_master_cpd_id"] for c in test}),
        "shared_moa_strings": sorted(dev_moas & {m for c in test for m in census[c]["moas"]}),
        "test_compounds_sharing_a_target_gene_with_development": sorted(c for c in test if set(census[c]["targets"]) & dev_targets),
        "similar_threshold": SIMILAR,
        "similar_to_development": sorted(c for c, v in nearest.items() if v["similarity"] is not None and v["similarity"] >= SIMILAR),
        "close_analogue_threshold": CLOSE,
        "close_analogues": sorted(c for c, v in nearest.items() if v["similarity"] is not None and v["similarity"] >= CLOSE),
        "no_fingerprint": sorted(c for c, v in nearest.items() if v["similarity"] is None),
        "nearest_similarity_quantiles": None, "nearest": nearest}
    vals = sorted(v["similarity"] for v in nearest.values() if v["similarity"] is not None)
    out["nearest_similarity_quantiles"] = {q: vals[min(len(vals) - 1, int(q * len(vals)))] for q in (0.5, 0.9, 0.95)}
    (HERE / "LEAKAGE.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in out.items() if k != "nearest"}, indent=1))
    for c in out["close_analogues"]:
        print(c, nearest[c])


if __name__ == "__main__":
    main()
