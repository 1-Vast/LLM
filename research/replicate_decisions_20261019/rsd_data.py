"""Replicate-split decisions (RSD) arena: PRISM 19Q4 secondary HTS002, 2.5 uM, replicate detection plates X1-X3.

File summary
- Units: one Broad core (first 13 characters of broad_id) = one compound; one column triple (X1, X2, X3) per core, the
  lexicographically first (broad_id, compound_plate, well) that has all three replicate plates (same rule as
  program_revision_20261017 and anchor_purchase_20261016).
- Lines: secondary-screen lines that passed STR profiling and have an HTS002 pool assignment.
- Identity audit: every comma-separated SMILES is parsed; the parent (largest organic fragment) is canonicalised with and
  without stereochemistry. Cores whose parents differ beyond stereochemistry are refused (AMBIGUOUS_STRUCTURE); cores with
  no parseable SMILES are refused (NO_STRUCTURE).
- Families: union of (any shared MoA label from secondary or primary metadata), (shared lower-case name), (ECFP4 Tanimoto
  >= 0.5 between non-isomeric parents). Using all labels joins 509 of 1,283 compounds (most oncology classes) into one
  component (the "giant" component; identified by size alone, before any outcome was read).
- Roles: clusters (a non-giant family, or the giant-component compounds sharing a first MoA label; core id if unlabelled)
  are taken in salted-hash order and each is given to the role with the largest deficit against target compound shares
  reference 2/6, search 1/6, selection 1/6, evaluation 2/6. For each query block, every reference
  compound with a direct edge (shared label, shared name, Tanimoto >= 0.5) to any query of that block is purged from that
  block's references. Non-giant queries are therefore component-isolated ("strict" tier); giant queries are edge-purged
  ("purged" tier). Queries of one block are never references of another block.
- Replicate roles: per core, a salted hash permutes (X1, X2, X3) into (A = purchased screening read, B = optional
  escalation read, T = truth read used only by the evaluator).
No outcome is used to build families, folds or roles.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "data" / "external" / "prism_19q4" / "raw"
TREAT = RAW / "secondary-screen-replicate-treatment-info.csv"
LFC = RAW / "secondary-screen-logfold-change.csv"
CELLS = RAW / "secondary-screen-cell-line-info.csv"
POOLS = RAW / "secondary-screen-pooling-info.csv"
PRIM_TREAT = RAW / "primary-screen-replicate-collapsed-treatment-info.csv"
PRIM_LFC = RAW / "primary-screen-replicate-collapsed-logfold-change.csv"
CACHE = HERE / "cache"
SCREEN, DOSE = "HTS002", 2.5
SALT_FOLD, SALT_ROLE = "rsd20261019|family", "rsd20261019|replicate"
TARGET = {"reference": 2 / 6, "search": 1 / 6, "selection": 1 / 6, "evaluation": 2 / 6}
GIANT_SHARE = 0.2
TANI = 0.5


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_text(path: Path) -> str:
    """Line-ending-normalised hash for frozen text/code files (CRLF and LF checkouts hash equal)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def hash_int(salt: str, key: str) -> int:
    return int(hashlib.sha256((salt + "|" + key).encode()).hexdigest()[:12], 16)


def load_treatments() -> pd.DataFrame:
    info = pd.read_csv(TREAT, low_memory=False)
    e = info[(info.perturbation_type == "experimental_treatment") & (info.screen_id == SCREEN)
             & np.isclose(info.dose, DOSE, atol=0.01)].copy()
    e["core"] = e.broad_id.str[:13]
    e["rep"] = e.detection_plate.str.extract(r"_(X\d)")[0]
    rows = []
    for core, g in e.groupby("core"):
        g = g.sort_values(["broad_id", "compound_plate", "well", "rep"])
        for (bid, plate, well), h in g.groupby(["broad_id", "compound_plate", "well"], sort=True):
            reps = dict(zip(h.rep, h.column_name))
            if {"X1", "X2", "X3"} <= set(reps):
                f = h.iloc[0]
                rows.append(dict(core=core, broad_id=bid, compound_plate=plate, well=well, name=str(f["name"]).strip().lower(),
                                 moa=f.moa, target=f.target, smiles=f.smiles, x1=reps["X1"], x2=reps["X2"], x3=reps["X3"]))
                break
    return pd.DataFrame(rows).sort_values("core").reset_index(drop=True)


def load_lines() -> pd.DataFrame:
    cells = pd.read_csv(CELLS)
    pools = pd.read_csv(POOLS)
    pools = pools[pools.screen_id == SCREEN][["row_name", "pool_id"]].drop_duplicates("row_name")
    c = cells[cells.passed_str_profiling.astype(str).str.upper() == "TRUE"].merge(pools, on="row_name")
    c = c.drop_duplicates("row_name").sort_values("row_name").reset_index(drop=True)
    return c[["row_name", "depmap_id", "ccle_name", "primary_tissue", "pool_id"]]


def parents(smiles):
    """Canonical parent SMILES (largest fragment), isomeric and non-isomeric, for every comma-separated entry."""
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    iso, flat = set(), set()
    if not isinstance(smiles, str):
        return iso, flat
    for s in smiles.split(", "):
        m = Chem.MolFromSmiles(s.strip())
        if m is None or m.GetNumHeavyAtoms() == 0:
            continue
        frags = Chem.GetMolFrags(m, asMols=True)
        p = max(frags, key=lambda x: x.GetNumHeavyAtoms())
        iso.add(Chem.MolToSmiles(p, isomericSmiles=True))
        flat.add(Chem.MolToSmiles(p, isomericSmiles=False))
    return iso, flat


def labels(moa) -> set:
    if not isinstance(moa, str) or moa.strip() in ("", "NA"):
        return set()
    return {x.strip().lower() for x in moa.split(",") if x.strip() and x.strip() != "NA"}


def build_arena():
    """Identity audit, families, folds and replicate roles. Reads metadata only (no response values)."""
    from rdkit import Chem, DataStructs
    from rdkit.Chem import AllChem
    t = load_treatments()
    lines = load_lines()
    prim = pd.read_csv(PRIM_TREAT)
    prim["core"] = prim.broad_id.str[:13]
    prim_moa = prim.groupby("core").moa.apply(lambda s: set().union(*[labels(x) for x in s]))
    refusals, keep, fps = {}, [], []
    stereo_only = 0
    for r in t.itertuples():
        iso, flat = parents(r.smiles)
        if not flat:
            refusals[r.core] = "NO_STRUCTURE"
            continue
        if len(flat) > 1:
            refusals[r.core] = "AMBIGUOUS_STRUCTURE"
            continue
        stereo_only += len(iso) > 1
        m = Chem.MolFromSmiles(next(iter(flat)))
        fps.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048))
        keep.append(r.Index)
    t = t.loc[keep].reset_index(drop=True)
    n = len(t)
    T = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        T[i] = DataStructs.BulkTanimotoSimilarity(fps[i], fps)
    lab = [labels(m) | prim_moa.get(c, set()) for m, c in zip(t.moa, t.core)]
    par = list(range(n))

    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    def u(a, b):
        ra, rb = f(a), f(b)
        if ra != rb:
            par[max(ra, rb)] = min(ra, rb)
    first = {}
    for i in range(n):
        for key in [("moa", x) for x in lab[i]] + [("name", t.name[i])]:
            if key in first:
                u(i, first[key])
            else:
                first[key] = i
        for j in np.where(T[i] >= TANI)[0]:
            u(i, int(j))
    root = np.array([f(i) for i in range(n)])
    fam_key = {rt: t.core[np.where(root == rt)[0]].min() for rt in set(root)}
    t["family"] = [fam_key[rt] for rt in root]
    sizes = t.family.value_counts()
    giant = set(sizes.index[sizes > GIANT_SHARE * n])
    first_lab = [(str(m).split(",")[0].strip().lower() if isinstance(m, str) and m.strip() not in ("", "NA") else "") for m in t.moa]
    t["giant"] = t.family.isin(giant)
    t["cluster"] = [("G:" + (fl or c)) if g else f for fl, c, g, f in zip(first_lab, t.core, t.giant, t.family)]
    # Balanced deterministic assignment: clusters in salted-hash order, each to the role with the largest remaining
    # deficit against TARGET compound shares (ties: fixed role order). Metadata only.
    size = t.cluster.value_counts()
    order = sorted(size.index, key=lambda c: hash_int(SALT_FOLD, c))
    filled = {r: 0 for r in TARGET}
    role_of = {}
    for c in order:
        r = max(TARGET, key=lambda k: (TARGET[k] * n - filled[k], -list(TARGET).index(k)))
        role_of[c] = r
        filled[r] += int(size[c])
    t["role"] = t.cluster.map(role_of)
    t["moa_labels"] = ["|".join(sorted(x)) for x in lab]
    # direct edges (metadata only) for per-block reference purging
    E = T >= TANI
    groups = {}
    for i in range(n):
        for key in [("moa", x) for x in lab[i]] + [("name", t.name[i])]:
            groups.setdefault(key, []).append(i)
    for v in groups.values():
        v = np.array(v)
        E[np.ix_(v, v)] = True
    np.fill_diagonal(E, False)
    ref = (t.role == "reference").to_numpy()
    purged = {}
    for blk in ("search", "selection", "evaluation"):
        q = (t.role == blk).to_numpy()
        purged[blk] = sorted(t.core[ref & E[:, q].any(1)])
    t.attrs["purged"] = purged
    perms = [("x1", "x2", "x3"), ("x1", "x3", "x2"), ("x2", "x1", "x3"), ("x2", "x3", "x1"), ("x3", "x1", "x2"), ("x3", "x2", "x1")]
    p = [perms[hash_int(SALT_ROLE, c) % 6] for c in t.core]
    t["colA"] = [getattr(t.loc[i], p[i][0]) for i in range(n)]
    t["colB"] = [getattr(t.loc[i], p[i][1]) for i in range(n)]
    t["colT"] = [getattr(t.loc[i], p[i][2]) for i in range(n)]
    audit = dict(n_cores_with_triple=int(n + len(refusals)), refusals={k: v for k, v in sorted(refusals.items())},
                 refusal_counts=pd.Series(list(refusals.values())).value_counts().to_dict() if refusals else {},
                 stereo_only_variants_kept=int(stereo_only), n_compounds=int(n), n_families=int(t.family.nunique()),
                 largest_family=int(t.family.value_counts().iloc[0]), n_lines=int(len(lines)), n_pools=int(lines.pool_id.nunique()),
                 role_counts={k: int(v) for k, v in t.role.value_counts().items()},
                 giant_by_role={k: int(v) for k, v in t[t.giant].role.value_counts().items()},
                 purged_reference_counts={k: len(v) for k, v in purged.items()})
    return t, lines, T, audit, E


def load_reads(t: pd.DataFrame, lines: pd.DataFrame):
    """A, B, T replicate log2FC arrays (compounds x lines). NaN = unknown (removed upstream), never inactive."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha256(("|".join(t.colA) + "#" + "|".join(t.colB) + "#" + "|".join(t.colT) + "#" + "|".join(lines.row_name)).encode()).hexdigest()[:16]
    path = CACHE / f"reads_{key}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=False)
        return z["A"], z["B"], z["T"]
    cols = set(t.colA) | set(t.colB) | set(t.colT)
    first = pd.read_csv(LFC, nrows=0).columns[0]
    m = pd.read_csv(LFC, usecols=lambda c: c == first or c in cols, index_col=0).reindex(lines.row_name)
    out = [m.reindex(columns=list(t[c])).to_numpy(np.float64).T for c in ("colA", "colB", "colT")]
    np.savez_compressed(path, A=out[0], B=out[1], T=out[2], lfc_sha256=np.array(sha256(LFC)))
    return out


def load_primary(t: pd.DataFrame, lines: pd.DataFrame):
    """Independent-run read: primary HTS 2.5 uM replicate-collapsed log2FC, aligned to (compounds x lines); NaN if absent."""
    pi = pd.read_csv(PRIM_TREAT)
    pi = pi[pi.screen_id == "HTS"].copy()
    pi["core"] = pi.broad_id.str[:13]
    pl = pd.read_csv(PRIM_LFC, index_col=0)
    pi = pi[pi.column_name.isin(pl.columns)].sort_values("column_name").drop_duplicates("core").set_index("core")
    P = np.full((len(t), len(lines)), np.nan)
    rows = pl.reindex(lines.row_name)
    for i, c in enumerate(t.core):
        if c in pi.index:
            P[i] = rows[pi.loc[c, "column_name"]].to_numpy(np.float64)
    return P


if __name__ == "__main__":
    t, lines, T, audit, E = build_arena()
    print(json.dumps(audit | {"refusals": len(audit["refusals"])}, indent=1))
    print(t.groupby("role").cluster.nunique().to_dict())
