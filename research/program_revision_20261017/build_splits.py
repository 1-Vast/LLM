"""Build the frozen drug/line partitions from metadata only (no response file is opened).

File summary
- Path: research/program_revision_20261017/build_splits.py
- Purpose: fix which drugs and lines are source history, which are held-out future projects, and
  how development projects split into support and query halves, before any response is read.
- Rules (seed 20261017, salted SHA-256 hashing; all deterministic):
  - Drugs: the HTS002 2.5 uM cores of `common.load_treatments`. Structure groups are connected
    components of (same InChIKey connectivity block) OR (Butina cluster on Morgan radius-2,
    2048-bit fingerprints at Tanimoto distance cutoff 0.5). Groups are hashed and taken in hash
    order into NOVEL until NOVEL holds >= 25% of drugs; the rest are SOURCE drugs.
  - Lines: `common.load_lines`. Lineage = primary_tissue. Future lineages: among lineages with
    8-45 eligible lines, the 7 with the smallest salted hash. Within every other lineage, lines
    with hash < 0.2 are held-out "seen-lineage" future lines. The remainder are SOURCE lines.
  - Development projects: each source lineage with >= 8 source lines is one project; smaller
    source lineages form one pooled project "other". Within a project, lines with hash < 0.5
    are support lines, the rest query lines.
- Outputs: drugs.csv, lines.csv, SPLITS.json (counts, rules, input digests, overlap census).
- Interfaces: ``python -B build_splits.py`` (refuses SPLITS_EXIST if SPLITS.json exists).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import (CELLS, EXPR, HERE, MUT, POOLS, SEED, TREAT, hash_unit, load_lines,
                    load_treatments, sha256, write_json)


def fingerprints(smiles):
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    from rdkit.Chem.inchi import MolToInchiKey

    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps, keys = [], []
    for s in smiles:
        mol = Chem.MolFromSmiles(str(s).split(",")[0].strip())
        if mol is None:
            fps.append(None)
            keys.append(None)
            continue
        fps.append(gen.GetFingerprint(mol))
        keys.append(MolToInchiKey(mol).split("-")[0])
    return fps, keys, DataStructs


def structure_groups(fps, keys, DataStructs, cutoff: float = 0.5):
    from rdkit.ML.Cluster import Butina

    n = len(fps)
    dists = []
    for i in range(1, n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
        dists.extend(1.0 - np.array(sims))
    clusters = Butina.ClusterData(dists, n, cutoff, isDistData=True)
    parent = list(range(n))

    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def join(a, b):
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for cl in clusters:
        for j in cl[1:]:
            join(cl[0], j)
    by_key = {}
    for i, k in enumerate(keys):
        by_key.setdefault(k, []).append(i)
    for members in by_key.values():
        for j in members[1:]:
            join(members[0], j)
    return np.array([root(i) for i in range(n)])


def tokens(v):
    if not isinstance(v, str):
        return []
    return sorted({t.strip() for t in v.split(",") if t.strip()})


def main() -> None:
    if (HERE / "SPLITS.json").exists():
        raise SystemExit("SPLITS_EXIST: partitions are already fixed")
    treat = load_treatments()
    fps, keys, DataStructs = fingerprints(treat.smiles)
    ok = np.array([f is not None for f in fps])
    treat = treat[ok].reset_index(drop=True)
    fps = [f for f in fps if f is not None]
    keys = [k for k in keys if k is not None]
    root = structure_groups(fps, keys, DataStructs)
    treat["connectivity"] = keys
    treat["structure_group"] = [f"SG{r:04d}" for r in root]
    groups = sorted(set(treat.structure_group))
    order = np.argsort(hash_unit(groups, f"{SEED}:novel-structure-group"))
    sizes = treat.structure_group.value_counts()
    novel, count = set(), 0
    for i in order:
        if count >= 0.25 * len(treat):
            break
        novel.add(groups[i])
        count += sizes[groups[i]]
    treat["drug_split"] = np.where(treat.structure_group.isin(novel), "novel", "source")
    src_idx = np.flatnonzero(treat.drug_split == "source")
    max_tc = np.zeros(len(treat))
    for i in range(len(treat)):
        sims = np.array(DataStructs.BulkTanimotoSimilarity(fps[i], [fps[j] for j in src_idx]))
        if treat.drug_split[i] == "source":
            sims = sims[src_idx != i]
        max_tc[i] = sims.max()
    treat["max_tanimoto_to_source"] = np.round(max_tc, 4)
    src_moa = {t for v in treat.moa[treat.drug_split == "source"] for t in tokens(v)}
    src_tgt = {t for v in treat.target[treat.drug_split == "source"] for t in tokens(v)}
    treat["moa_seen_in_source"] = [bool(set(tokens(v)) & src_moa) for v in treat.moa]
    treat["target_seen_in_source"] = [bool(set(tokens(v)) & src_tgt) for v in treat.target]

    lines = load_lines()
    counts = lines.primary_tissue.value_counts()
    cand = sorted(t for t, n in counts.items() if 8 <= n <= 45)
    h = hash_unit(cand, f"{SEED}:future-lineage")
    future_lin = {cand[i] for i in np.argsort(h)[:7]}
    hl = hash_unit(lines.depmap_id, f"{SEED}:held-out-line")
    split = np.where(lines.primary_tissue.isin(future_lin), "future_lineage",
                     np.where(hl < 0.2, "future_line", "source"))
    lines["line_split"] = split
    src = lines.line_split == "source"
    src_counts = lines[src].primary_tissue.value_counts()
    proj = [t if src_counts.get(t, 0) >= 8 else "other" for t in lines.primary_tissue]
    lines["project"] = np.where(src, proj, "")
    hs = hash_unit(lines.depmap_id, f"{SEED}:support-query")
    lines["role"] = np.where(src, np.where(hs < 0.5, "support", "query"), "")

    treat.to_csv(HERE / "drugs.csv", index=False, lineterminator="\n")
    lines.to_csv(HERE / "lines.csv", index=False, lineterminator="\n")
    nov = treat.drug_split == "novel"
    write_json(HERE / "SPLITS.json", {
        "seed": SEED,
        "responses_opened": False,
        "inputs_sha256": {p.name: sha256(p) for p in (TREAT, CELLS, POOLS, EXPR, MUT)},
        "drugs": {"total": int(len(treat)), "unparsable_smiles_dropped": int((~ok).sum()),
                  "source": int((~nov).sum()), "novel": int(nov.sum()),
                  "structure_groups": int(len(groups)), "novel_groups": len(novel),
                  "novel_max_tanimoto_to_source_quantiles": np.quantile(max_tc[nov], [0.1, 0.5, 0.9]).round(3),
                  "novel_with_near_analogue_tc_ge_0.6": int((max_tc[nov] >= 0.6).sum()),
                  "novel_moa_seen_in_source": int(treat.moa_seen_in_source[nov].sum()),
                  "novel_target_seen_in_source": int(treat.target_seen_in_source[nov].sum())},
        "lines": {"total": int(len(lines)), "future_lineages": sorted(future_lin),
                  "by_split": lines.line_split.value_counts().to_dict(),
                  "projects": lines[src].project.value_counts().to_dict(),
                  "roles": lines[src].role.value_counts().to_dict()},
    })
    print(open(HERE / "SPLITS.json", encoding="utf-8").read())


if __name__ == "__main__":
    main()
