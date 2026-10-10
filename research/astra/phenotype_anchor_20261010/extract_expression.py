"""Stage 2: byte-accounted X_hvg extraction for the phenotype-anchor study.

The row plan is computed from obs codes alone (stage 1) and hashed before any expression byte is
requested. Per (condition, plate) group:

* treated: 24 rows in 2 evenly spaced contiguous windows -> count, mean, variance, phase counts of
  the read rows, and 4 raw rows (float16) for cell-level checks;
* DMSO: 256 rows in 4 windows -> raw float32 rows (STATE basal input; phase-classifier training).

Held-out contexts are refused before FREEZE.json exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ZS = ROOT / "research/astra/zeroshot_context_20261007"
sys.path.insert(0, str(ZS))
from remote import REVISION, RangeClient  # noqa: E402
from extract import choose, spans  # noqa: E402

CACHE = ROOT / "data/external/tahoe_phenotype_20261010"
HELDOUT = ("c12.h5ad", "c20.h5ad", "c26.h5ad", "c27.h5ad", "c31.h5ad")
DMSO = "[('DMSO_TF', 0.0, 'uM')]"
ROW_BYTES = 2000 * 4
TREATED, TREATED_WINDOWS, KEEP_RAW = 24, 2, 4
BASAL, BASAL_WINDOWS = 256, 4


def plan(name: str, basal_rows: int = BASAL) -> dict:
    receipt = json.loads((HERE / "obs" / f"{name}.json").read_text(encoding="utf-8"))
    census = json.loads((ZS / "census" / f"{name}.json").read_text(encoding="utf-8"))
    layout = census["layouts"]["obsm/X_hvg"]
    if layout["chunks"] is not None or layout["compression"] is not None or layout["shape"][1] != 2000:
        raise ValueError(f"{name}: X_hvg is not contiguous float32 x 2000")
    z = np.load(CACHE / "obs" / f"{name}.npz")
    labels = np.asarray(receipt["categories"]["drugname_drugconc"])
    plates = np.asarray(receipt["categories"]["plate"])
    key = z["drugname_drugconc"].astype(np.int64) * 64 + z["plate"].astype(np.int64)
    order = np.argsort(key, kind="stable")
    uniq, start = np.unique(key[order], return_index=True)
    bounds = list(start) + [len(order)]
    groups = []
    for i, k in enumerate(uniq):
        rows = np.sort(order[bounds[i]:bounds[i + 1]])
        label, plate = str(labels[k // 64]), str(plates[k % 64])
        basal = label == DMSO
        chosen = choose(rows, basal_rows if basal else TREATED, BASAL_WINDOWS if basal else TREATED_WINDOWS)
        groups.append({"label": label, "plate": plate, "n_group": int(len(rows)), "rows": chosen.tolist(), "basal": basal})
    body = {"file": name, "revision": REVISION, "x_hvg_offset": layout["offset"], "n_cells": layout["shape"][0], "groups": groups}
    body["plan_sha256"] = hashlib.sha256(json.dumps(groups, sort_keys=True).encode()).hexdigest()
    return body


def extract(name: str, threads: int = 12, basal_rows: int = BASAL) -> dict:
    out_dir = CACHE / "expression" / name
    receipt_path = HERE / "expression" / f"{name}.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    started = time.perf_counter()
    p = plan(name, basal_rows)
    (HERE / "expression" / "plans").mkdir(parents=True, exist_ok=True)
    (HERE / "expression" / "plans" / f"{name}.json").write_text(json.dumps(p), encoding="utf-8")
    client = RangeClient(HERE / "expression" / "ledgers" / f"{name}.jsonl", user_agent="MAESTRO-phenotype-anchor/1")
    phase = np.load(CACHE / "obs" / f"{name}.npz")["phase"]
    jobs = []
    for gi, g in enumerate(p["groups"]):
        for a, b in spans(np.asarray(g["rows"], dtype=np.int64)):
            jobs.append((gi, a, b))

    def fetch(job):
        gi, a, b = job
        start = p["x_hvg_offset"] + a * ROW_BYTES
        data = client.fetch(name, start, start + (b - a + 1) * ROW_BYTES - 1, f"x_hvg_rows:{gi}")
        return gi, a, np.frombuffer(data, dtype="<f4").reshape(b - a + 1, 2000)

    blocks: dict[int, list] = {}
    with ThreadPoolExecutor(threads) as pool:
        for gi, a, arr in pool.map(fetch, jobs):
            blocks.setdefault(gi, []).append((a, arr))
    labels, plates, counts, n_group, means, variances, phase_counts = [], [], [], [], [], [], []
    raw_treated, raw_treated_key, basal_blocks, basal_plate, basal_phase = [], [], [], [], []
    for gi, g in enumerate(p["groups"]):
        parts = sorted(blocks[gi], key=lambda t: t[0])
        x = np.concatenate([arr for _, arr in parts]).astype(np.float32)
        rows = np.concatenate([np.arange(a, a + len(arr)) for a, arr in parts])
        if not np.array_equal(rows, np.asarray(g["rows"])):
            raise ValueError(f"{name}: group {gi} row mismatch")
        if g["basal"]:
            basal_blocks.append(x)
            basal_plate.extend([g["plate"]] * len(x))
            basal_phase.append(phase[rows])
        else:
            labels.append(g["label"])
            plates.append(g["plate"])
            counts.append(len(x))
            n_group.append(g["n_group"])
            means.append(x.mean(0))
            variances.append(x.var(0))
            phase_counts.append(np.bincount(phase[rows], minlength=3))
            raw_treated.append(x[:KEEP_RAW].astype(np.float16))
            raw_treated_key.extend([len(labels) - 1] * min(KEEP_RAW, len(x)))
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(out_dir / "treated.npz", label=np.asarray(labels), plate=np.asarray(plates), count=np.asarray(counts),
             n_group=np.asarray(n_group), mean=np.asarray(means), var=np.asarray(variances),
             phase_counts=np.asarray(phase_counts), raw=np.concatenate(raw_treated), raw_group=np.asarray(raw_treated_key))
    basal = np.concatenate(basal_blocks)
    np.savez(out_dir / "basal.npz", x=basal, plate=np.asarray(basal_plate), phase=np.concatenate(basal_phase))
    out = {"file": name, "plan_sha256": p["plan_sha256"], "treated_groups": len(labels), "basal_rows": int(len(basal)),
           "remote_requests": client.requests, "remote_bytes": client.bytes, "seconds": round(time.perf_counter() - started, 1),
           "treated_mean_sha256": hashlib.sha256(np.ascontiguousarray(np.asarray(means)).tobytes()).hexdigest(),
           "basal_sha256": hashlib.sha256(np.ascontiguousarray(basal).tobytes()).hexdigest()}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="*", default=[f"c{i}.h5ad" for i in range(50)])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--allow-heldout", action="store_true")
    parser.add_argument("--basal-rows", type=int, default=BASAL, help="DMSO rows read per plate (512 for held-out STATE input)")
    args = parser.parse_args()
    files = list(args.files)
    if not args.allow_heldout:
        files = [f for f in files if f not in HELDOUT]
    elif not (HERE / "FREEZE.json").exists():
        raise SystemExit("held-out expression may be read only after FREEZE.json exists")
    with Pool(args.workers) as pool:
        for row in pool.starmap(extract, [(f, 12, args.basal_rows) for f in files]):
            print(json.dumps({k: row[k] for k in ("file", "treated_groups", "basal_rows", "remote_bytes", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
