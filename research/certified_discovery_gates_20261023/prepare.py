"""First response conversion of the study; runs only after FREEZE.json.

Jaaks: validation-screen SYNERGY_DELTA_EMAX per plate (evidence reads), original-screen means (primary read) and the
inactivity flags; raw original-screen NC-1 and lowest-dose library-alone INTENSITY values for Gate 1b.
AZ: Bliss_excess, lib1_yhat and lib2_yhat of GDSC_007 rows of the 320 exposed MASTER cells only. Rows of any other MASTER_CELL_ID are discarded
right after CSV tokenisation, before any other field is read. No other archive member is opened.
"""
from collections import Counter, defaultdict
import csv
import io
import json
import math
import re
import zipfile

import numpy as np
import pandas as pd

from common import (AZ_DESIGN, AZ_MEMBER, AZ_ZIP, AZ_ZIP_SHA, INACTIVE_LEVEL, JAAKS_ORIGINAL, JAAKS_RAW,
                    JAAKS_VALIDATION, DATA, OUT, require_freeze, sha, write_json)

ID_COLS = ["BARCODE", "SIDM", "ANCHOR_ID", "ANCHOR_CONC", "LIBRARY_ID"]
VALUE_COLS = ["SYNERGY_DELTA_EMAX", "ANCHOR_VIABILITY", "LIBRARY_EMAX"]


def _float(text):
    try:
        value = float(text)
    except ValueError:
        return math.nan
    return value if math.isfinite(value) else math.nan


def load_fitted(path):
    d = pd.read_csv(path, usecols=ID_COLS + VALUE_COLS, dtype={c: str for c in ID_COLS})
    for c in ID_COLS:
        d[c] = d[c].str.strip()
    d["unit"] = (d.SIDM + "|" + d.ANCHOR_ID + "|" + d.ANCHOR_CONC.map(lambda s: repr(float(s))) + "|" + d.LIBRARY_ID)
    for c in VALUE_COLS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def jaaks():
    original = load_fitted(JAAKS_ORIGINAL)
    validation = load_fitted(JAAKS_VALIDATION)
    vplate = (validation.groupby(["unit", "BARCODE"])
              .agg(read=("SYNERGY_DELTA_EMAX", "mean"), rows=("SYNERGY_DELTA_EMAX", "size")).reset_index())
    duplicate_unit_plates = int((vplate.rows > 1).sum())
    vplate = vplate[np.isfinite(vplate.read)]
    finite_plates = vplate.groupby("unit").size()
    original_units = set(original.unit)
    pool = sorted(u for u, n in finite_plates.items() if n >= 2 and u in original_units)
    oplate = original.groupby(["unit", "BARCODE"]).SYNERGY_DELTA_EMAX.mean().reset_index()
    oplate = oplate[np.isfinite(oplate.SYNERGY_DELTA_EMAX)]
    primary = oplate.groupby("unit").SYNERGY_DELTA_EMAX.agg(["mean", "size"])
    activity = original.groupby("unit")[["ANCHOR_VIABILITY", "LIBRARY_EMAX"]].mean()

    width = int(finite_plates.loc[pool].max())
    K = len(pool)
    X = np.full((K, width), np.nan)
    barcodes = np.full((K, width), "", dtype=object)
    by_unit = {u: g.sort_values("BARCODE") for u, g in vplate[vplate.unit.isin(set(pool))].groupby("unit")}
    for i, u in enumerate(pool):
        g = by_unit[u]
        X[i, :len(g)] = g.read.to_numpy()
        barcodes[i, :len(g)] = g.BARCODE.to_numpy()
    p = primary["mean"].reindex(pool).to_numpy(dtype=float)
    n_o = primary["size"].reindex(pool).fillna(0).to_numpy(dtype=int)
    av = activity.ANCHOR_VIABILITY.reindex(pool).to_numpy(dtype=float)
    le = activity.LIBRARY_EMAX.reindex(pool).to_numpy(dtype=float)
    inactive = np.isfinite(av) & np.isfinite(le) & (av >= INACTIVE_LEVEL) & (le >= INACTIVE_LEVEL)
    np.savez_compressed(DATA / "DATA_JAAKS.npz", unit=np.array(pool, dtype=str), X=X,
                        barcodes=barcodes.astype(str), p=p, n_o=n_o, inactive=inactive)
    shared = set(original.BARCODE) & set(validation.BARCODE)
    return original, {
        "pool_units": K, "max_validation_reads": width,
        "validation_reads_per_unit": {str(k): int(v) for k, v in Counter((~np.isnan(X)).sum(1)).items()},
        "units_with_nan_primary": int(np.isnan(p).sum()),
        "inactive_units": int(inactive.sum()),
        "unit_plates_with_duplicate_rows_averaged": duplicate_unit_plates,
        "original_validation_shared_barcodes": len(shared),
        "validation_rows": int(len(validation)), "original_rows": int(len(original)),
    }


def jaaks_raw(original):
    """NC-1 intensities per plate and lowest-dose (D7) library-alone wells with leave-plate-out inactivity."""
    nc = defaultdict(list)
    lib = defaultdict(list)
    plate_model = {}
    lib_tag = re.compile(r"^L\d+-D(\d+)-S$")
    with zipfile.ZipFile(JAAKS_RAW) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = next(reader)
            ix = {name: i for i, name in enumerate(header)}
            b_i, p_i, t_i, d_i, c_i, y_i, s_i = (ix[k] for k in ("BARCODE", "POSITION", "TAG", "DRUG_ID", "CONC",
                                                                 "INTENSITY", "SANGER_MODEL_ID"))
            for row in reader:
                tag = row[t_i]
                barcode = row[b_i]
                if barcode not in plate_model:
                    plate_model[barcode] = row[s_i].strip()
                if tag == "NC-1":
                    nc[barcode].append(_float(row[y_i]))
                    continue
                match = lib_tag.match(tag)
                if match:
                    lib[(barcode, row[p_i])].append((int(match.group(1)), row[d_i].strip(), _float(row[c_i]),
                                                     _float(row[y_i])))
    plates = sorted(nc)
    plate_index = {b: i for i, b in enumerate(plates)}
    width = max(len(v) for v in nc.values())
    NC = np.full((len(plates), width), np.nan)
    for b, values in nc.items():
        NC[plate_index[b], :len(values)] = values

    per_plate = (original.groupby(["SIDM", "LIBRARY_ID", "BARCODE"]).LIBRARY_EMAX.mean().dropna().reset_index())
    totals = per_plate.groupby(["SIDM", "LIBRARY_ID"]).LIBRARY_EMAX.agg(["sum", "size"])
    own = {(r.SIDM, r.LIBRARY_ID, r.BARCODE): r.LIBRARY_EMAX for r in per_plate.itertuples(index=False)}
    conc_check = defaultdict(dict)
    wells = []
    skipped = Counter()
    for (barcode, position), tags in lib.items():
        for dose, drug, conc, _ in tags:
            conc_check[(barcode, drug)][dose] = conc
        if len(tags) != 1:
            skipped["more_than_one_library_tag"] += 1
            continue
        dose, drug, conc, intensity = tags[0]
        if dose != 7:
            continue
        if barcode not in plate_index or not math.isfinite(intensity):
            skipped["no_plate_or_nan_intensity"] += 1
            continue
        model = plate_model[barcode]
        key = (model, drug)
        if key not in totals.index:
            skipped["library_not_in_fitted_line"] += 1
            continue
        total, count = totals.loc[key]
        mine = own.get((model, drug, barcode))
        if mine is not None:
            total, count = total - mine, count - 1
        if count < 1:
            skipped["no_other_plate"] += 1
            continue
        wells.append((plate_index[barcode], intensity, drug, total / count))
    lowest_is_d7 = [c[7] < c[1] for c in conc_check.values() if 7 in c and 1 in c
                    and math.isfinite(c[7]) and math.isfinite(c[1])]
    W = np.array(wells, dtype=object)
    np.savez_compressed(DATA / "DATA_JAAKS_RAW.npz", plates=np.array(plates, dtype=str), NC=NC,
                        well_plate=W[:, 0].astype(int), well_intensity=W[:, 1].astype(float),
                        well_drug=W[:, 2].astype(str), well_loo_emax=W[:, 3].astype(float))
    loo = W[:, 3].astype(float)
    return {"plates": len(plates), "nc1_per_plate": {str(k): int(v) for k, v in
                                                     Counter((~np.isnan(NC)).sum(1)).items()},
            "d7_library_wells": len(wells), "d7_wells_inactive_loo": int((loo >= INACTIVE_LEVEL).sum()),
            "skipped": dict(skipped), "plates_with_d7_concentration_below_d1": float(np.mean(lowest_is_d7)),
            "dose_pairs_checked": len(lowest_is_d7)}


def az():
    assert sha(AZ_ZIP) == AZ_ZIP_SHA, "pinned AZ archive hash mismatch"
    roles = json.loads(AZ_DESIGN.read_text(encoding="utf-8"))["role_cells"]
    exposed = set(roles["train"]) | set(roles["validation"]) | set(roles["test"])
    reserve = set(roles["reserve"])
    assert len(exposed) == 320 and len(reserve) == 413 and not exposed & reserve
    skipped = Counter()
    matrices = {}
    with zipfile.ZipFile(AZ_ZIP) as archive, archive.open(AZ_MEMBER) as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
        header = next(reader)
        ix = {name: i for i, name in enumerate(header)}
        m_i = ix["MASTER_CELL_ID"]
        b_i, c_i, d1_i, d2_i, y_i, h1_i, h2_i = (ix[k] for k in ("BARCODE", "cmatrix", "lib1_drug_id",
                                                                 "lib2_drug_id", "Bliss_excess", "lib1_yhat",
                                                                 "lib2_yhat"))
        for row in reader:
            master = row[m_i]
            if master not in exposed:
                skipped["reserve" if master in reserve else "unassigned"] += 1
                continue
            key = (row[b_i], row[c_i])
            m = matrices.get(key)
            if m is None:
                m = matrices[key] = {"master": master, "pairs": set(), "values": [], "yhat": []}
            m["pairs"].add((row[d1_i].strip(), row[d2_i].strip()))
            m["values"].append(_float(row[y_i]))
            m["yhat"].append((_float(row[h1_i]), _float(row[h2_i])))
    units = defaultdict(list)
    mono = defaultdict(list)
    dropped = Counter()
    for (barcode, cmatrix), m in matrices.items():
        if len(m["pairs"]) != 1:
            dropped["more_than_one_pair"] += 1
            continue
        values = np.array(m["values"])
        finite = np.isfinite(values)
        if finite.mean() < 0.8:
            dropped["under_80pct_finite"] += 1
            continue
        a, b = sorted(next(iter(m["pairs"])))
        units[f"{m['master']}|{a}|{b}"].append((barcode, float(values[finite].mean()), len(values)))
        mono[f"{m['master']}|{a}|{b}"].extend(m["yhat"])
    names = sorted(units)
    width = max(len(v) for v in units.values())
    K = len(names)
    X = np.full((K, width), np.nan)
    wells = np.full((K, width), np.nan)
    barcodes = np.full((K, width), "", dtype=object)
    for i, name in enumerate(names):
        reads = sorted(units[name])
        assert len({r[0] for r in reads}) == len(reads), "two reads of one unit on one plate"
        X[i, :len(reads)] = [r[1] for r in reads]
        wells[i, :len(reads)] = [r[2] for r in reads]
        barcodes[i, :len(reads)] = [r[0] for r in reads]
    n = (~np.isnan(X)).sum(1)
    group = np.where(n >= 4, 3, np.where(n >= 2, 2, 1))
    top = np.array([np.max(np.array(mono[name]), axis=0) for name in names])
    inactive = np.all(np.isfinite(top), axis=1) & np.all(top <= 1.0 - INACTIVE_LEVEL, axis=1)
    np.savez_compressed(DATA / "DATA_AZ.npz", unit=np.array(names, dtype=str), X=X, wells=wells,
                        barcodes=barcodes.astype(str), group=group, inactive=inactive)
    return {"rows_skipped_before_any_other_field": dict(skipped), "matrices_seen": len(matrices),
            "matrices_dropped": dict(dropped), "units": K,
            "units_by_group": {f"G{g}": int((group == g).sum()) for g in (1, 2, 3)},
            "reads_per_unit": {str(k): int(v) for k, v in sorted(Counter(n).items())},
            "inactive_units": int(inactive.sum()),
            "response_fields_converted": "Bliss_excess, lib1_yhat, lib2_yhat (exposed MASTER rows only)"}


def main():
    record, changed = require_freeze()
    DATA.mkdir(parents=True, exist_ok=True)
    receipt = {"freeze_sha256_of_protocol": record["files"]["log/20261023/certified_discovery_gates/PROTOCOL.md"],
               "frozen_files_changed_with_logged_deviation": changed}
    original, receipt["jaaks"] = jaaks()
    receipt["jaaks_raw"] = jaaks_raw(original)
    receipt["az"] = az()
    for name in ("DATA_JAAKS.npz", "DATA_JAAKS_RAW.npz", "DATA_AZ.npz"):
        receipt[f"{name}_sha256"] = sha(DATA / name)
    write_json(OUT / "PREPARE_RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    main()
