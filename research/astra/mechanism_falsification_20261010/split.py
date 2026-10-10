"""Metadata-only universe and role split for block M (writes SPLIT.json once).

Reads only design metadata: GSE92742 sig_info (which signatures exist), pert_info (InChIKeys) and
the Drug Repurposing Hub 2020-03-24 drug and sample tables (mechanism annotations). No expression
value, signature metric or activity score is read, so the split cannot depend on an outcome.

Unit: one drug, keyed by its Repurposing Hub name, so salt forms and re-synthesised batches of one
drug share a role. A LINCS compound maps to a drug by its 13-character Broad ID, else by its
14-character InChIKey block.

Design menu: the nine L1000 core lines x {6 h, 24 h} at 10 uM (18 options). A drug enters the
universe when at least 8 options exist and at least 3 lines have both times.

Truth: the drug's single Repurposing Hub mechanism (``moa``). Drugs with several mechanisms are
excluded from the universe; their mechanism is not single-valued.

Roles (seed 20261010), per mechanism class after a seeded shuffle:
* n >= 2: ceil(n/2) reference, the rest alternate confirmation, development (confirmation first);
* n == 1: query only (development or confirmation by alternation over the sorted singleton list),
  so the class has no data reference and can be represented only by knowledge.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "data/external/lincs_l1000_gse92742"
SEED = 20261010
CORE = ("A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP")
TIMES = ("6 h", "24 h")
DOSE = "10 µM"
MIN_OPTIONS = 8
MIN_BOTH_TIME_LINES = 3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sig = pd.read_csv(SRC / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", low_memory=False)
    pert = pd.read_csv(SRC / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", low_memory=False)
    drugs = pd.read_csv(SRC / "repurposing_drugs_20200324.txt", sep="\t", comment="!")
    samples = pd.read_csv(SRC / "repurposing_samples_20200324.txt", sep="\t", comment="!")
    return sig, pert, drugs, samples


def drug_map(pert: pd.DataFrame, samples: pd.DataFrame) -> dict[str, str]:
    """LINCS pert_id -> Repurposing Hub drug name (Broad ID first, then InChIKey block)."""
    by_brd = samples.assign(b=samples.broad_id.str[:13]).drop_duplicates("b").set_index("b").pert_iname.to_dict()
    ik = samples.dropna(subset=["InChIKey"]).assign(k=lambda d: d.InChIKey.str[:14])
    by_ik = ik.drop_duplicates("k").set_index("k").pert_iname.to_dict()
    out: dict[str, str] = {}
    for pid, key in zip(pert.pert_id.astype(str), pert.inchi_key.astype(str)):
        if pid[:13] in by_brd:
            out[pid] = by_brd[pid[:13]]
        elif key not in ("-666", "nan") and key[:14] in by_ik:
            out[pid] = by_ik[key[:14]]
    return out


def main() -> dict:
    out_path = HERE / "SPLIT.json"
    if out_path.exists():
        raise SystemExit("SPLIT.json exists; the split is written once")
    sig, pert, drugs, samples = load()
    pmap = drug_map(pert[pert.pert_type == "trt_cp"], samples)
    moa = drugs.set_index("pert_iname").moa.to_dict()
    cp = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(CORE) & sig.pert_itime.isin(TIMES) & (sig.pert_idose == DOSE)].copy()
    cp["drug"] = cp.pert_id.astype(str).map(pmap)
    cp = cp.dropna(subset=["drug"])
    cp["moa"] = cp.drug.map(moa)
    cp = cp[cp.moa.notna() & ~cp.moa.astype(str).str.contains("|", regex=False)]
    avail = cp.groupby("drug").apply(lambda d: sorted({f"{c}|{t}" for c, t in zip(d.cell_id, d.pert_itime)}), include_groups=False)
    both = cp.groupby(["drug", "cell_id"]).pert_itime.nunique().reset_index()
    nboth = both[both.pert_itime == 2].groupby("drug").size()
    universe = sorted(d for d, opts in avail.items() if len(opts) >= MIN_OPTIONS and nboth.get(d, 0) >= MIN_BOTH_TIME_LINES)
    cls = {d: moa[d] for d in universe}
    rng = np.random.default_rng(SEED)
    roles: dict[str, str] = {}
    singletons = []
    for c in sorted(set(cls.values())):
        members = sorted(d for d in universe if cls[d] == c)
        if len(members) == 1:
            singletons.append(members[0])
            continue
        perm = [members[i] for i in rng.permutation(len(members))]
        k = math.ceil(len(members) / 2)
        for d in perm[:k]:
            roles[d] = "reference"
        for j, d in enumerate(perm[k:]):
            roles[d] = "confirmation" if j % 2 == 0 else "development"
    for j, d in enumerate(sorted(singletons)):
        roles[d] = "confirmation" if j % 2 == 0 else "development"
    sigs = {d: sorted(cp[cp.drug == d].sig_id) for d in universe}
    res = {
        "seed": SEED, "core_lines": list(CORE), "times": list(TIMES), "dose": DOSE,
        "min_options": MIN_OPTIONS, "min_both_time_lines": MIN_BOTH_TIME_LINES,
        "sources": {p.name: sha256(p) for p in sorted(SRC.glob("*")) if p.is_file() and p.suffix in (".gz", ".txt") and "Level5" not in p.name},
        "n_universe": len(universe),
        "role_counts": pd.Series(roles).value_counts().to_dict(),
        "n_classes": len(set(cls.values())),
        "drugs": {d: {"moa": cls[d], "role": roles[d], "options": avail[d], "sig_ids": sigs[d]} for d in universe},
    }
    out_path.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print(r["n_universe"], r["role_counts"], "classes", r["n_classes"])
