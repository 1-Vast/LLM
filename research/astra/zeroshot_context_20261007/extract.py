"""Stage 2: byte-budgeted extraction of native X_hvg rows from pinned Tahoe files.

The sampling plan (which rows, which roles) is computed from obs metadata alone
and written, with its SHA-256, before any expression byte is requested.

Held-out (documented zero-shot test) contexts keep the raw sampled rows, so
every downstream statistic can be recomputed. Training contexts keep per-group
summaries (count, mean, variance) and their raw DMSO rows, which are STATE's
basal input. Roles are fixed by a row hash, never by expression:
  DMSO rows -> 'basal' (model input) or 'reference' (outcome denominator);
  every row -> half 'A' or 'B' (split-half reliability).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from remote import CACHE, REVISION, RangeClient  # noqa: E402

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
ROW_BYTES = 2000 * 4
LOCAL = {"c39.h5ad": Path(__file__).resolve().parents[3] / "data/external/arc_state/tahoe_metadata_source/c39.h5ad"}
PROFILES = {  # rows per group, contiguous windows per group
    "heldout": {"treated": 384, "treated_windows": 6, "dmso": 2048, "dmso_windows": 16},
    "train": {"treated": 32, "treated_windows": 1, "dmso": 512, "dmso_windows": 4},
}


def unit_hash(file: str, rows: np.ndarray, salt: str) -> np.ndarray:
    return np.array([int(hashlib.sha256(f"{salt}:{file}:{int(r)}".encode()).hexdigest()[:12], 16) / 16 ** 12 for r in rows])


def choose(rows: np.ndarray, k: int, windows: int) -> np.ndarray:
    """Evenly spaced contiguous windows over the group's sorted rows (metadata only)."""
    n = len(rows)
    if n <= k:
        return rows
    width = int(np.ceil(k / windows))
    if windows == 1:
        starts = [(n - width) // 2]
    else:
        starts = [int(round(i * (n - width) / (windows - 1))) for i in range(windows)]
    positions = np.unique(np.concatenate([np.arange(s, s + width) for s in starts]))
    return rows[positions[:k] if len(positions) > k else positions]


def spans(rows: np.ndarray) -> list[tuple[int, int]]:
    breaks = np.flatnonzero(np.diff(rows) != 1)
    starts = np.concatenate([[0], breaks + 1])
    ends = np.concatenate([breaks, [len(rows) - 1]])
    return [(int(rows[a]), int(rows[b])) for a, b in zip(starts, ends)]


def plan(file: str, role: str) -> dict:
    census = json.loads((HERE / "census" / f"{file}.json").read_text(encoding="utf-8"))
    with np.load(CACHE / "census" / f"{file}.npz") as codes:
        drug, plate, passed = codes["drugname_drugconc"].astype(np.int64), codes["plate"].astype(np.int64), codes["pass_filter"]
    labels, plates = census["categories"]["drugname_drugconc"], census["categories"]["plate"]
    full_code = census["categories"]["pass_filter"].index("full")
    profile = PROFILES[role]
    key = drug * 64 + plate
    order = np.argsort(key, kind="stable")
    keys, first = np.unique(key[order], return_index=True)
    bounds = list(first) + [len(order)]
    groups = []
    for i, k in enumerate(keys):
        rows = np.sort(order[bounds[i]:bounds[i + 1]])
        label, plate_name = labels[int(k // 64)], plates[int(k % 64)]
        is_control = label == CONTROL
        chosen = choose(rows, profile["dmso" if is_control else "treated"],
                        profile["dmso_windows" if is_control else "treated_windows"])
        groups.append({"group": len(groups), "label": label, "plate": plate_name, "control": is_control,
                       "available_rows": int(len(rows)), "available_full_rows": int((passed[rows] == full_code).sum()),
                       "rows": chosen.tolist(), "full": (passed[chosen] == full_code).tolist()})
    for g in groups:
        rows = np.asarray(g["rows"])
        g["half"] = np.where(unit_hash(file, rows, "half") < 0.5, "A", "B").tolist()
        if g["control"]:
            g["control_role"] = np.where(unit_hash(file, rows, "control-role") < 0.5, "basal", "reference").tolist()
    layout = census["layouts"]["obsm/X_hvg"]
    return {"file": file, "cell_name": census["cell_names"][0], "revision": REVISION, "role": role,
            "profile": profile, "x_hvg_offset": layout["offset"], "x_hvg_shape": layout["shape"],
            "groups": groups, "planned_rows": int(sum(len(g["rows"]) for g in groups)),
            "planned_bytes": int(sum(len(g["rows"]) for g in groups) * ROW_BYTES),
            "selection": "metadata-only evenly spaced contiguous windows per (drugname_drugconc, plate) group; roles by row hash",
            "census_sha256": hashlib.sha256((HERE / "census" / f"{file}.json").read_bytes()).hexdigest()}


def chunked_sha256(array: np.ndarray, rows: int = 65536) -> str:
    h = hashlib.sha256()
    for i in range(0, len(array), rows):
        h.update(np.ascontiguousarray(array[i:i + rows]).tobytes())
    return h.hexdigest()


def extract(file: str, role: str, threads: int = 16) -> dict:
    out = CACHE / "extract" / file
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = HERE / "extract" / f"{file}.receipt.json"
    if receipt_path.exists():
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    p = plan(file, role)
    plan_path = CACHE / "extract" / "plans" / f"{file}.plan.json"  # large; hash kept in the receipt
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(p), encoding="utf-8")
    plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    started = time.perf_counter()
    groups = p["groups"]
    # Fixed output slots per group: control rows always raw; treated rows raw only for held-out contexts.
    slot, cursor = {}, 0
    for g in groups:
        if g["control"] or role == "heldout":
            slot[g["group"]] = cursor
            cursor += len(g["rows"])
    raw = np.lib.format.open_memmap(out / "rows.npy", mode="w+", dtype=np.float32, shape=(cursor, 2000)) if cursor else None
    summary = {g["group"]: {"n": 0, "s": np.zeros(2000), "ss": np.zeros(2000)} for g in groups if not (g["control"] or role == "heldout")}
    jobs = []
    for g in groups:
        rows = np.asarray(g["rows"])
        position = {int(r): i for i, r in enumerate(rows)}
        for a, b in spans(rows):
            jobs.append((g["group"], a, b, position[a]))
    local = LOCAL.get(file)
    client = RangeClient(HERE / "extract" / "ledgers" / f"{file}.jsonl")

    def fetch(job):
        group, a, b, pos = job
        start = p["x_hvg_offset"] + a * ROW_BYTES
        end = p["x_hvg_offset"] + (b + 1) * ROW_BYTES - 1
        if local is not None:
            with open(local, "rb") as handle:
                handle.seek(start)
                data = handle.read(end - start + 1)
        else:
            data = client.fetch(file, start, end, f"x_hvg_rows:group{group}")
        return job, np.frombuffer(data, dtype="<f4").reshape(b - a + 1, 2000)

    full = {g["group"]: np.asarray(g["full"], dtype=bool) for g in groups}
    with ThreadPoolExecutor(threads) as pool:
        futures = [pool.submit(fetch, job) for job in jobs]
        for future in as_completed(futures):
            (group, a, b, pos), block = future.result()
            if not np.isfinite(block).all():
                raise ValueError(f"non-finite X_hvg rows in {file} group {group}")
            if group in slot:
                raw[slot[group] + pos: slot[group] + pos + len(block)] = block
            else:
                keep = full[group][pos:pos + len(block)]
                values = block[keep].astype(np.float64)
                summary[group]["n"] += len(values)
                summary[group]["s"] += values.sum(0)
                summary[group]["ss"] += (values ** 2).sum(0)
    if raw is not None:
        raw.flush()
    ids = np.array(sorted(summary)) if summary else np.zeros(0, dtype=int)
    if len(ids):
        n = np.array([summary[i]["n"] for i in ids], dtype=np.int64)
        mean = np.array([summary[i]["s"] / max(summary[i]["n"], 1) for i in ids])
        var = np.array([(summary[i]["ss"] - summary[i]["n"] * (summary[i]["s"] / max(summary[i]["n"], 1)) ** 2) / max(summary[i]["n"] - 1, 1) for i in ids])
        np.savez(out / "treated_summaries.npz", group=ids, n=n, mean=mean.astype(np.float32), var=np.maximum(var, 0).astype(np.float32))
    np.savez(out / "slots.npz", group=np.array(sorted(slot)), start=np.array([slot[g] for g in sorted(slot)]))
    receipt = {"file": file, "cell_name": p["cell_name"], "role": role, "plan_sha256": plan_sha,
               "planned_rows": p["planned_rows"], "raw_rows_stored": int(cursor),
               "remote_requests": client.requests, "remote_bytes": client.bytes,
               "local_read": local is not None, "seconds": round(time.perf_counter() - started, 2),
               "rows_sha256": chunked_sha256(raw) if raw is not None else None,
               "outputs": sorted(x.name for x in out.iterdir()),
               "expression_inspected_by_operator": False}
    receipt_path.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--role", choices=sorted(PROFILES), required=True)
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args()
    (HERE / "extract").mkdir(exist_ok=True)
    for file in args.files:
        r = extract(file, args.role, args.threads)
        print(json.dumps({k: r[k] for k in ("file", "cell_name", "role", "planned_rows", "remote_bytes", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
