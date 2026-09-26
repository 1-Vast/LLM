"""Build the digest-bound signature library that tools/signature_retrieval reads.

File summary
- Path: research/biological_depth/build_library.py
- Purpose: package the prepared, marker-verified SciPlex3 shifts as a reference library, with
  the procedure's held-out agreement recorded inside it so the claim travels with the data.
- Core points:
  - Profiles are measured, uncentered shifts against matched vehicle; the library's shared mean
    per line and dose is stored beside them for centering.
  - The arrays are hashed and the hash is written into library.json; the reader refuses a
    library whose arrays no longer match.
- Run: python research/biological_depth/build_library.py --prepared <dir> --probe <summary.json>
       [--audit <audit.json>] --output data/virtual_cell/sciplex3_signature_library
- Depends on: common.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import common

LINES = ("A549", "K562", "MCF7")
DOSES = (10.0, 100.0, 1000.0, 10000.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    conditions = pd.read_csv(args.prepared / "conditions.csv", index_col="condition_id")
    compounds = pd.read_csv(args.prepared / "compounds.csv")
    genes = pd.read_csv(args.prepared / "genes.csv").symbol.tolist()
    shift = np.load(args.prepared / "shifts.npz")["shift"]
    manifest = json.loads((args.prepared / "prepare_manifest.json").read_text(encoding="utf-8"))
    index = {c: i for i, c in enumerate(compounds.compound)}
    entry_compound = conditions.compound.map(index).to_numpy()
    entry_line = conditions.cell_line.map({l: i for i, l in enumerate(LINES)}).to_numpy()
    entry_dose = conditions.dose.map({d: i for i, d in enumerate(DOSES)}).to_numpy()
    systematic = np.zeros((len(LINES), len(DOSES), len(genes)), dtype=np.float32)
    for li in range(len(LINES)):
        for di in range(len(DOSES)):
            systematic[li, di] = shift[(entry_line == li) & (entry_dose == di)].mean(0)
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez(args.output / "library.npz", profiles=shift.astype(np.float32), entry_compound=entry_compound,
             entry_line=entry_line, entry_dose=entry_dose, systematic=systematic)
    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    validation = {
        "procedure": "leave-skeleton-out retrieval: query = the compound's measured 10 uM shifts in all three lines "
                     "centered on the other skeletons' mean; references = every other skeleton; answer = class of "
                     "the most similar reference (cosine), restricted to the probe's class list",
        "top1_agreement_with_vendor_annotation": probe["accuracy"]["tool"],
        "compounds": probe["items"], "classes": len(probe["options"]), "chance": probe["chance"],
        "frequency_prior": probe["accuracy"]["prior"],
        "record": "log/20260926/README.md",
    }
    if args.audit:
        b3 = json.loads(args.audit.read_text(encoding="utf-8"))["B3"]
        validation["fold_based_retrieval_ceiling"] = {"top1_agreement": b3["observed_ceiling"],
                                                      "compounds": b3["scored_compounds"],
                                                      "chance": b3["chance"]}
    meta = {
        "schema": "maestro.virtual_cell.signature_library.v1",
        "created": datetime.now().isoformat(timespec="seconds"),
        "source": {"dataset": "SciPlex3 (Srivatsan et al., Science 2020), Figshare file 43381398, CC BY 4.0",
                   "sha256": manifest["source_sha256"], "time_hours": 24,
                   "feature_label_offset": manifest["audit"]["feature_label_check"]["chosen_offset"],
                   "shift": "mean over cells of log1p(counts per 10,000) minus the matched vehicle mean of the same "
                            "line and replicate, averaged over replicates"},
        "genes": genes, "lines": list(LINES), "doses": list(DOSES),
        "compounds": [{"name": r.compound, "skeleton": r.skeleton, "class": r.pathway_level_2,
                       "class_level_1": r.pathway_level_1, "smiles": r.smiles} for r in compounds.itertuples()],
        "validation": validation,
        "arrays_sha256": hashlib.sha256((args.output / "library.npz").read_bytes()).hexdigest(),
    }
    (args.output / "library.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"entries": int(len(shift)), "genes": len(genes), "compounds": len(compounds),
                      "arrays_sha256": meta["arrays_sha256"], "validation": validation}, indent=1))


if __name__ == "__main__":
    main()
