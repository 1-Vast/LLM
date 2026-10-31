"""Parse the two CellMiner workbooks into plain arrays (verifier cache).

Usage: python -I v02_parse_xlsx.py <zscore.xlsx> <raw.xlsx> <out_dir>
Values 'na' (or empty) become NaN. Every non-numeric cell in a line column is counted and reported.
"""
import sys
import time
from collections import Counter

import numpy as np
import openpyxl


def to_float(v, bad):
    if v is None:
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s == "" or s.lower() == "na":
        return np.nan
    try:
        return float(s)
    except ValueError:
        bad[s] += 1
        return np.nan


def parse(path, header_first_cell, n_meta_before_lines, n_after):
    t0 = time.time()
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["all"]
    header = None
    rows = []
    pre = []
    for row in ws.iter_rows(values_only=True):
        cells = list(row)
        if header is None:
            pre.append(cells)
            if cells and isinstance(cells[0], str) and cells[0].strip().startswith(header_first_cell):
                header = cells
            continue
        rows.append(cells)
    wb.close()
    print(f"{path}: header found after {len(pre)} rows; {len(rows)} data rows; {time.time() - t0:.1f}s", flush=True)
    return header, rows


def main():
    zpath, rpath, out = sys.argv[1], sys.argv[2], sys.argv[3]

    # ---- z-score workbook
    header, rows = parse(zpath, "NSC #", 6, 2)
    header = [h if h is None else str(h) for h in header]
    print("z header:", header[:6], header[-2:])
    lines = header[6:66]
    assert len(lines) == 60, len(lines)
    bad = Counter()
    nsc, name, smiles, z, tot_exp, tot_qc, skipped = [], [], [], [], [], [], []
    for r in rows:
        if r is None or len(r) == 0 or all(c is None for c in r):
            skipped.append("empty")
            continue
        r = list(r) + [None] * (68 - len(r))
        if r[0] is None:
            skipped.append(repr(r[:3]))
            continue
        nsc.append(str(r[0]).strip())
        name.append("" if r[1] is None else str(r[1]))
        smiles.append("" if r[5] is None else str(r[5]).strip())
        z.append([to_float(v, bad) for v in r[6:66]])
        tot_exp.append(to_float(r[66], Counter()))
        tot_qc.append(to_float(r[67], Counter()))
    print("z rows parsed:", len(nsc), "skipped:", len(skipped), Counter(skipped).most_common(5))
    print("z non-numeric tokens in line columns:", bad.most_common(10))
    np.savez(out + "/cache_zscore.npz", nsc=np.array(nsc), name=np.array(name), smiles=np.array(smiles),
             z=np.array(z, dtype=float), line=np.array(lines), tot_exp=np.array(tot_exp), tot_qc=np.array(tot_qc))

    # ---- raw workbook
    header, rows = parse(rpath, "NSC #", 9, 0)
    header = [h if h is None else str(h) for h in header]
    print("raw header:", header[:9])
    rlines = header[9:69]
    assert len(rlines) == 60, len(rlines)
    assert rlines == lines, "line columns differ between workbooks"
    bad = Counter()
    nsc, fail, expt, x, probes, qc, skipped = [], [], [], [], [], [], []
    fail_raw_types = Counter()
    for r in rows:
        if r is None or len(r) == 0 or all(c is None for c in r):
            skipped.append("empty")
            continue
        r = list(r) + [None] * (69 - len(r))
        if r[0] is None:
            skipped.append(repr(r[:3]))
            continue
        nsc.append(str(r[0]).strip())
        fail_raw_types[type(r[7]).__name__] += 1
        fail.append("<None>" if r[7] is None else str(r[7]))
        expt.append("" if r[8] is None else str(r[8]))
        probes.append(to_float(r[5], Counter()))
        qc.append(to_float(r[6], Counter()))
        x.append([to_float(v, bad) for v in r[9:69]])
    print("raw rows parsed:", len(nsc), "skipped:", len(skipped), Counter(skipped).most_common(5))
    print("raw failure-reason cell types:", dict(fail_raw_types))
    print("raw non-numeric tokens in line columns:", bad.most_common(10))
    fc = Counter(fail)
    print("raw distinct failure reasons:", len(fc))
    for k, v in fc.most_common(40):
        print(f"   {v:7d}  {k!r}")
    np.savez(out + "/cache_raw.npz", nsc=np.array(nsc), fail=np.array(fail), expt=np.array(expt),
             x=np.array(x, dtype=float), line=np.array(rlines), probes=np.array(probes), qc=np.array(qc))
    print("done")


if __name__ == "__main__":
    main()
