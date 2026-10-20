"""Store actual fits and replay observed campaigns without fitting or hidden truth."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import r1_core as C
from r1_gates import Gate


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_fits(path, fits):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    arrays, metadata = {}, []
    for index, fitted in enumerate(fits):
        pre = str(index)
        meta = {"program": vars(fitted.program), "version": fitted.version,
                "cells": list(fitted.cells), "probe_classes": list(fitted.probe_classes),
                "gate_ids": list(fitted.gate_ids), "definition_key": fitted.definition_key,
                "arrays": [], "gates": {}}
        for name in ("sigma", "states", "logprior", "mu", "V", "ref_basis"):
            value = getattr(fitted, name)
            if value is not None:
                arrays[f"{pre}/{name}"] = value
                meta["arrays"].append(name)
        for gid, gate in (fitted.gates or {}).items():
            gm = {k: v for k, v in vars(gate).items() if k not in ("b", "beta")}
            for name in ("b", "beta"):
                if getattr(gate, name) is not None:
                    arrays[f"{pre}/gates/{gid}/{name}"] = getattr(gate, name)
            meta["gates"][gid] = gm
        metadata.append(meta)
    arrays["metadata"] = np.array(json.dumps(metadata, sort_keys=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    return file_hash(path)


def load_fits(path):
    fits = []
    with np.load(path, allow_pickle=False) as stored:
        for index, meta in enumerate(json.loads(str(stored["metadata"]))):
            pre = str(index)
            pm = meta["program"]
            for name in ("gates", "parents"):
                pm[name] = tuple(pm[name])
            pm["conj"] = tuple(tuple(edge) for edge in pm["conj"])
            values = {name: stored[f"{pre}/{name}"].copy() for name in meta["arrays"]}
            gates = {}
            for gid, gm in meta["gates"].items():
                for name in ("scope", "probe_order", "parents", "evidence_cells", "states"):
                    gm[name] = tuple(gm[name])
                gm["b"] = stored[f"{pre}/gates/{gid}/b"].copy()
                key = f"{pre}/gates/{gid}/beta"
                gm["beta"] = stored[key].copy() if key in stored else None
                gates[gid] = Gate(**gm)
            fits.append(C.Fitted(C.Program(**pm), **values, version=meta["version"],
                                 cells=tuple(meta["cells"]), probe_classes=tuple(meta["probe_classes"]),
                                 gate_ids=tuple(meta["gate_ids"]), gates=gates or None,
                                 definition_key=meta["definition_key"]))
    return fits


def gate_programs(fits):
    return [{"pid": f.program.pid, "key": f.program.key(f.gates)}
            for f in fits if f.program.kind == "gate"]


def replay(fits, row):
    base = np.asarray(row["base"])
    pool = np.asarray(row["pool"], bool)
    belief, recorded = C.make_belief(fits, base), {}
    for pair, value in zip(row["probes"], row["values"]):
        belief.observe(pair, value - base[pair])
        if pool[pair]:
            recorded[pair] = value
    return C.top_k(C.shortlist_scores(belief, pool, recorded)).tolist()
