"""Build the independent L1000 mechanism-decision data and its feasibility audit (Phase 4).

File summary
- Path: research/sequence_audit/lincs_prepare.py
- Purpose: from the local GSE92742 metadata and the derived `subset48` condition cache, assemble
  the conditions, detection flags, mechanism labels, identity and scaffold groups and folds the
  frozen protocol (`protocol.json`, section `l1000`) calls for, and measure every feasibility gate
  before any validator reading or policy decision is computed.
- Core points:
  - Conditions: A549, MCF7, PC3 and VCAP at 10 uM, 6 h and 24 h. The profile is the cache's
    condition mean over 978 measured landmark genes.
  - Detection comes from Broad's own replicate statistic (`distil_cc_q75` in the signature
    metrics), against a vehicle null of DMSO signatures at the same line and time, with the
    SciPlex3 validator's rule: max(0.10, the null's 0.99 quantile).
  - QC: at least two wells on two plates in the cache, finite values, and a matched official
    signature with at least two replicates.
  - Labels: exact Repurposing Hub joins (Broad compound ID, else full InChIKey), single-mechanism
    records only. They are external annotations, not measured engagement.
  - Folds: connected components of compounds sharing an InChIKey connectivity block or a
    Bemis-Murcko scaffold, dealt round-robin in hash order within class strata.
  - The prepared data are laid out as `common.Data`, so the SciPlex3 validator code reads them
    unchanged; `qc_passed` sees the L1000 QC rule through the replicate fields (checked here).
- Run: python research/sequence_audit/lincs_prepare.py
- Depends on: data/external/lincs_l1000_phase1, data/raw/sciplex3 Repurposing Hub tables, rdkit
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "acquisition_followup"))

import policies as P  # noqa: E402
import lincs_flow as L  # noqa: E402

C = P.C
DATA = L.DATA
OUT = P.ROOT / "outputs" / "sequence_audit_20260926" / "l1000" / "prepared"
LINES = ("A549", "MCF7", "PC3", "VCAP")
TIMES = (6.0, 24.0)
DOSE_NM = 10000.0
TIERS = {"LT": {"keys": tuple((line, t, DOSE_NM) for line in LINES for t in TIMES),
                "fixed": (("A549", 6.0, DOSE_NM), ("A549", 24.0, DOSE_NM))},
         "T": {"keys": tuple(("A549", t, DOSE_NM) for t in TIMES),
               "fixed": (("A549", 6.0, DOSE_NM), ("A549", 24.0, DOSE_NM))}}
POOL_MIN_IDENTITIES = 6
POOL_MIN_DETECTED_IDENTITIES = 2
FOLDS = 5


def days(key) -> float:
    """Exposure in days plus the five assay days SciPlex3 charged."""
    return key[1] / 24.0 + 5.0


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scaffold(smiles: str) -> str | None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles) if smiles and smiles != "-666" else None
    if mol is None:
        return None
    text = Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol))
    return text or None


def signatures() -> pd.DataFrame:
    info = pd.read_csv(DATA / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", dtype=str)
    metrics = pd.read_csv(DATA / "GSE92742_Broad_LINCS_sig_metrics.txt.gz", sep="\t", dtype=str)
    sig = info.merge(metrics[["sig_id", "distil_cc_q75", "distil_nsample", "distil_ss", "tas"]], on="sig_id")
    sig["cc"] = sig.distil_cc_q75.astype(float)
    sig["n"] = sig.distil_nsample.astype(int)
    sig["ss"] = sig.distil_ss.astype(float)
    sig["batch"] = sig.sig_id.str.split("_").str[0]
    sig["time"] = sig.pert_itime.str.split().str[0].astype(float)
    return sig[sig.cell_id.isin(LINES)]


def vehicle_null(sig: pd.DataFrame) -> dict:
    out = {}
    for line in LINES:
        for t in TIMES:
            v = sig[(sig.cell_id == line) & (sig.time == t) & (sig.pert_type == "ctl_vehicle") & (sig.n >= 2) & (sig.cc > -600)]
            q = float(v.cc.quantile(0.99)) if len(v) else float("nan")
            out[f"{line}|{t:g}"] = {"signatures": int(len(v)), "q99": q, "median": float(v.cc.median()) if len(v) else None,
                                    "threshold": max(0.10, q) if len(v) else None}
    return out


def assign_folds(units: pd.DataFrame) -> dict:
    """Round-robin in SHA256 order within class strata, like the SciPlex3 fold assignment."""
    assignment, offset = {}, 0
    for _, stratum in units.groupby("stratum", sort=True):
        ordered = sorted(stratum.component.unique(), key=lambda s: hashlib.sha256(f"maestro-l1000-v1|{s}".encode()).hexdigest())
        for i, component in enumerate(ordered):
            assignment[component] = (i + offset) % FOLDS
        offset += len(ordered)
    return assignment


def components(frame: pd.DataFrame) -> dict:
    """Union compounds sharing an identity block or a ring scaffold."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for row in frame.itertuples():
        union(f"c:{row.compound}", f"i:{row.identity}")
        if row.scaffold:
            union(f"c:{row.compound}", f"s:{row.scaffold}")
    return {row.compound: find(f"c:{row.compound}") for row in frame.itertuples()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conditions = pd.DataFrame(json.loads((DATA / "subset48/conditions.json").read_text()))
    conditions["row"] = np.arange(len(conditions))
    conditions["time"] = conditions.time_h.astype(float)
    menu = conditions[conditions.cell_id.isin(LINES) & (conditions.dose_um == 10.0) & conditions.time.isin(TIMES)].copy()
    sig = signatures()
    null = vehicle_null(sig)
    treated = sig[(sig.pert_type == "trt_cp") & (sig.pert_idose == "10 µM")]
    by_key = defaultdict(list)
    for r in treated.itertuples():
        by_key[(r.pert_id, r.cell_id, r.time, r.batch)].append((r.cc, r.n, r.ss))
    ccs, sss, nsig = [], [], []
    for r in menu.itertuples():
        matched = [x for b in r.batches for x in by_key.get((r.pert_id, r.cell_id, r.time, b), [])]
        usable = [x for x in matched if x[1] >= 2 and x[0] > -600]
        nsig.append(len(usable))
        ccs.append(float(np.median([x[0] for x in usable])) if usable else float("nan"))
        sss.append(float(np.median([x[2] for x in usable])) if usable else float("nan"))
    menu["cc"], menu["ss"], menu["signatures"] = ccs, sss, nsig
    arrays = np.load(DATA / "subset48/conditions.npz", allow_pickle=False)
    means = arrays["mean"][menu.row.to_numpy()].astype(np.float32)
    variances = arrays["var"][menu.row.to_numpy()]
    finite = np.isfinite(means).all(axis=1) & np.isfinite(variances).all(axis=1) & (variances >= 0).all(axis=1)
    menu["qc"] = (menu.n_wells >= 2) & (menu.n_plates >= 2) & (menu.signatures >= 1) & finite
    menu["threshold"] = [null[f"{l}|{t:g}"]["threshold"] for l, t in zip(menu.cell_id, menu.time)]
    menu["detected"] = menu.qc & (menu.cc >= menu.threshold)

    pert = pd.read_csv(DATA / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str).fillna("")
    annotations = L.annotation_map(pert[pert.pert_id.isin(set(menu.pert_id))])
    info = pert.set_index("pert_id")
    compounds = []
    for pid in sorted(set(menu.pert_id)):
        # Perturbagens absent from pert_info (combinations, CMAP controls) have no identity to join.
        annotation = annotations.get(pid, {"moa": [], "annotation_route": None})
        moa = annotation["moa"]
        klass = moa[0] if len(moa) == 1 and "|" not in moa[0] else None
        inchi = info.inchi_key.get(pid, "")
        compounds.append({"compound": pid, "name": info.pert_iname.get(pid, ""), "klass": klass,
                          "multi_moa": bool(moa) and klass is None,
                          "route": annotation["annotation_route"],
                          "identity": inchi.split("-")[0] if inchi and inchi != "-666" else pid,
                          "scaffold": scaffold(info.canonical_smiles.get(pid, ""))})
    compounds = pd.DataFrame(compounds)
    qc_menu = menu[menu.qc]
    measured = qc_menu.groupby("pert_id").apply(lambda g: set(zip(g.cell_id, g.time, [DOSE_NM] * len(g))), include_groups=False)
    detected_at = qc_menu[qc_menu.detected].groupby("pert_id").apply(
        lambda g: set(zip(g.cell_id, g.time, [DOSE_NM] * len(g))), include_groups=False)

    pools, eligible = {}, {}
    labelled = compounds[compounds.klass.notna()].set_index("compound")
    for tier, spec in TIERS.items():
        keys = set(spec["keys"])
        complete = [c for c in labelled.index if keys <= measured.get(c, set())]
        frame = labelled.loc[complete]
        stats = {}
        for klass, group in frame.groupby("klass"):
            det = group[[bool(keys & detected_at.get(c, set())) for c in group.index]]
            stats[klass] = {"identities": int(group.identity.nunique()), "scaffolds": int(group.scaffold.nunique()),
                            "detected_identities": int(det.identity.nunique())}
        pool = sorted(k for k, s in stats.items()
                      if s["identities"] >= POOL_MIN_IDENTITIES and s["detected_identities"] >= POOL_MIN_DETECTED_IDENTITIES)
        pools[tier] = {"pool": pool, "class_stats": {k: stats[k] for k in pool},
                       "classes_considered": len(stats), "complete_labelled_compounds": len(complete)}
        eligible[tier] = sorted(c for c in complete if labelled.klass[c] in pool)

    in_pool = set().union(*(set(p["pool"]) for p in pools.values()))
    members = compounds[compounds.klass.isin(in_pool)].copy()
    comp_of = components(members)
    members["component"] = members.compound.map(comp_of)
    strata = members.groupby("component").klass.min()
    folds = assign_folds(pd.DataFrame({"component": strata.index, "stratum": strata.values}))
    members["fold"] = members.component.map(folds).astype(int)
    members["skeleton"] = members.identity

    keep = menu[menu.pert_id.isin(set(members.compound))].copy()
    shift = means[[menu.index.get_loc(i) for i in keep.index]]
    table = pd.DataFrame({"cell_line": keep.cell_id.values, "time": keep.time.values, "dose": DOSE_NM,
                          "compound": keep.pert_id.values,
                          # the SciPlex3 QC fields, set so that common.qc_passed reproduces the L1000 QC rule
                          "replicates": np.where(keep.qc.values, 2, 0), "n_cells_rep1": 20, "n_cells_rep2": 20,
                          "n_wells": keep.n_wells.values, "n_plates": keep.n_plates.values,
                          "batch": [b[0] if len(b) == 1 else "|".join(sorted(b)) for b in keep.batches],
                          "plates": ["|".join(p) for p in keep.plates], "cc_q75": keep.cc.values,
                          "signature_strength": keep.ss.values, "signatures": keep.signatures.values,
                          "qc": keep.qc.values, "detected": keep.detected.values})
    table.to_csv(OUT / "conditions.csv", index=False)
    np.savez_compressed(OUT / "shifts.npz", shift=shift, gene_id=arrays["gene_id"])
    members.to_csv(OUT / "compounds.csv", index=False)
    (OUT / "tiers.json").write_bytes(json.dumps({t: {"keys": [list(k) for k in TIERS[t]["keys"]],
                                                     "fixed": [list(k) for k in TIERS[t]["fixed"]],
                                                     "pool": pools[t]["pool"], "compounds": eligible[t]}
                                                 for t in TIERS}, indent=1).encode("utf-8"))

    data = load()
    assert all(C.qc_passed(data, i) == bool(q) for i, q in enumerate(data.conditions.qc)), "QC encoding"
    # Provenance: does the cache track Broad's own signature strength for the same conditions?
    norms = np.linalg.norm(means, axis=1)
    ok = menu.qc.to_numpy() & np.isfinite(menu.ss.to_numpy())
    concordance = float(pd.Series(norms[ok]).corr(pd.Series(menu.ss.to_numpy()[ok]), method="spearman"))
    batch_share = {}
    for tier in TIERS:
        sub = members[members.compound.isin(eligible[tier])]
        first_batch = {c: table[(table.compound == c) & (table.cell_line == "A549") & (table.time == 6.0)].batch.iloc[0]
                       for c in sub.compound}
        sub = sub.assign(batch=sub.compound.map(first_batch))
        batch_share[tier] = {k: round(float(g.batch.value_counts(normalize=True).iloc[0]), 3)
                             for k, g in sub.groupby("klass")}
    feasibility = {
        "sources": {str(p.relative_to(P.ROOT)).replace("\\", "/"): digest(p) for p in (
            DATA / "subset48/conditions.json", DATA / "subset48/conditions.npz", DATA / "subset48/scale_receipt.json",
            DATA / "GSE92742_Broad_LINCS_sig_info.txt.gz", DATA / "GSE92742_Broad_LINCS_sig_metrics.txt.gz",
            DATA / "GSE92742_Broad_LINCS_pert_info.txt.gz", P.ROOT / "data/raw/sciplex3/repurposing_samples_20200324.txt",
            P.ROOT / "data/raw/sciplex3/repurposing_drugs_20200324.txt")},
        "vehicle_null": null,
        "menu_conditions": int(len(menu)), "qc_passed": int(menu.qc.sum()), "detected": int(menu.detected.sum()),
        "detected_by_line_time": {f"{l}|{t:g}": [int(g.detected.sum()), int(g.qc.sum())]
                                  for (l, t), g in menu.groupby(["cell_id", "time"])},
        "compounds": int(len(compounds)), "single_moa_labelled": int(compounds.klass.notna().sum()),
        "multi_moa": int(compounds.multi_moa.sum()), "unlabelled": int(compounds.route.isna().sum()),
        "pools": pools, "eligible_episode_compounds": {t: len(v) for t, v in eligible.items()},
        "episodes": {t: len(eligible[t]) * (len(pools[t]["pool"]) - 1) for t in TIERS},
        "fold_members": members.groupby("fold").compound.size().to_dict(),
        "components": int(members.component.nunique()), "pool_compounds": int(len(members)),
        "cache_vs_official_signature_strength_spearman": concordance,
        "largest_single_batch_share_per_class": batch_share,
        "multi_batch_conditions": int((keep.batches.map(len) > 1).sum()),
    }
    (OUT.parent / "feasibility.json").write_bytes(json.dumps(feasibility, indent=1, default=str).encode("utf-8"))
    print(json.dumps({k: v for k, v in feasibility.items() if k not in ("sources",)}, indent=1, default=str))


def load() -> C.Data:
    """The prepared L1000 decision data as `common.Data`."""
    conditions = pd.read_csv(OUT / "conditions.csv")
    compounds = pd.read_csv(OUT / "compounds.csv")
    arrays = np.load(OUT / "shifts.npz")
    data = C.Data(conditions, arrays["shift"], np.zeros(0), np.zeros(0), compounds, pd.DataFrame(), {},
                  pd.DataFrame(), np.zeros(0))
    data.agreement = conditions.cc_q75.to_numpy()
    for row, r in conditions.iterrows():
        data.index.setdefault((r.cell_line, float(r.time), float(r.dose)), {})[r.compound] = row
    return data


def tiers() -> dict:
    spec = json.loads((OUT / "tiers.json").read_text(encoding="utf-8"))
    return {name: C.Tier(name, tuple(tuple(k) for k in s["keys"]), tuple(s["pool"]), tuple(s["compounds"]))
            for name, s in spec.items()}


def setting(tier) -> P.Setting:
    return P.Setting("l1000", tuple(tier.keys), TIERS[tier.name]["fixed"], days, 12.0)


if __name__ == "__main__":
    main()
