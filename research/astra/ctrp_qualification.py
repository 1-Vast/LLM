"""Verify CTRPv2 raw menu coverage; read dose metadata, not response columns."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

import numpy as np
import pandas as pd

from research.astra.gdsc_transport import digest, save


def normalized_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def run(archive, out):
    out.mkdir(parents=True, exist_ok=False)
    save(out / "protocol.json", dict(archive_sha256=digest(archive), version="CTRPv2.0_2015_ctd2_ExpandedDataset",
         code_sha256=digest(__file__), metadata_only=True, no_fitted_dose_interpolation=True,
         dose_tolerance_uM=1e-12, outcome_columns_read=[], provider_license="unknown",
         assay_platform_evidence="native cells_per_well definition: 1536-well CellTiter-Glo",
         duration="unknown from inspected native metadata; full protocol access failed"))
    with zipfile.ZipFile(archive) as z:
        members = []
        declared = {line.split(" *",1)[1]:line.split(" *",1)[0] for line in z.read("MANIFEST.txt").decode().splitlines() if " *" in line}
        for info in z.infolist():
            sha, md5 = hashlib.sha256(), hashlib.md5()
            with z.open(info) as stream:
                while chunk := stream.read(1 << 20):
                    sha.update(chunk)
                    md5.update(chunk)
            if info.filename in declared and md5.hexdigest() != declared[info.filename]:
                raise ValueError("native archive manifest mismatch: " + info.filename)
            members.append(dict(file=info.filename, bytes=info.file_size, sha256=sha.hexdigest(),
                                native_md5=md5.hexdigest(), native_md5_matched=info.filename in declared))
        save(out / "archive_members.json", members)
        for name in ["v20._README.txt", "v20._COLUMNS.txt", "MANIFEST.txt", "v20.meta.per_compound.txt",
                     "v20.meta.per_cell_line.txt", "v20.meta.per_experiment.txt"]:
            (out / name).write_bytes(z.read(name))
        compounds = pd.read_csv(z.open("v20.meta.per_compound.txt"), sep="\t")
        compounds["canonical_name"] = compounds.cpd_name.map(normalized_name)
        requested = [("Afatinib",2.),("PLX-4720",10.),("PD0325901",.25)]
        selected = compounds.loc[compounds.canonical_name.isin([normalized_name(n) for n,_ in requested])].copy()
        selected.to_csv(out / "requested_compounds.csv", index=False)
        pieces, raw_rows = [], 0
        with z.open("v20.data.per_cpd_well.txt") as stream:
            for chunk in pd.read_csv(stream, sep="\t", usecols=["experiment_id","assay_plate_barcode","master_cpd_id","cpd_conc_umol"],chunksize=250000):
                raw_rows += len(chunk)
                part = chunk.loc[chunk.master_cpd_id.isin(selected.master_cpd_id)].copy()
                part.insert(0,"source_record",part.index)
                pieces.append(part)
        observed = pd.concat(pieces, ignore_index=True)
        observed.to_csv(out / "requested_dose_metadata.csv", index=False)
        coverage = []
        for name,dose in requested:
            ids = selected.loc[selected.canonical_name == normalized_name(name), "master_cpd_id"]
            rows = observed.loc[observed.master_cpd_id.isin(ids)]
            doses = sorted(map(float,rows.cpd_conc_umol.dropna().unique()))
            exact = np.isclose(rows.cpd_conc_umol,dose,rtol=0,atol=1e-12)
            coverage.append(dict(name=name, requested_dose_uM=dose, compound_ids=list(map(int,ids)),
                actual_doses_uM=doses, actual_well_records=len(rows), exact_well_records=int(exact.sum()),
                closest_actual_dose_uM=min(doses,key=lambda x:abs(x-dose)) if doses else None))
        save(out / "summary.json", dict(raw_well_records=raw_rows, compound_records=len(compounds), coverage=coverage,
            exact_original_menu_qualified=all(r["exact_well_records"]>0 for r in coverage),
            status="metadata qualification only; no policy value evaluated",
            missing_evidence=["well positions", "prospective input availability", "complete failures/costs",
                              "duration protocol certification"],
            source_record_definition="zero-based parsed nonblank data-record ordinal, not a physical well ID or text line",
            response_values_inspected=False, outcome_model_fits=0, STATE_forwards=0))
    save(out / "manifest.json", {p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"})
    print((out / "summary.json").read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    run(args.archive,args.out)
