"""Dataset, split and candidate manifests, written before the freeze and hashed into it.

File summary
- Path: research/external_validation/manifests.py
- Purpose: record what each study is (source digests, version, licence, compounds and structures,
  groups, contexts, plate and batch clusters), how it is partitioned, and which local studies were
  considered for external validation and why none qualifies.
- Core points:
  - Dataset manifests carry no mechanism label: labels are outcomes.
  - Split manifests hold the five grouped folds of each tier and each fold's boundary report;
    internal folds must be compound- and group-disjoint, and batch crossing is recorded, not hidden.
  - The candidate audit (`manifests/external_candidates.json`, in the repository) states the
    blocker and the exact data an external run needs.
- Run: python -m research.external_validation.manifests
- Depends on: firewall.py, locked_replay.py (loaders and units)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import firewall as F
from . import locked_replay as R

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = R.OUT / "manifests"
C, E, LP = R.C, R.E, R.LP


def file_entry(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": F.sha256_file(path), "bytes": path.stat().st_size}


def sciplex3_manifest() -> dict:
    raw = ROOT / "data/raw/sciplex3"
    provenance = json.loads((raw / "SrivatsanTrapnell2020_sciplex3.provenance.json").read_text(encoding="utf-8"))
    h5ad = raw / "SrivatsanTrapnell2020_sciplex3.h5ad"
    source = [file_entry(h5ad), file_entry(raw / "SrivatsanTrapnell2020_sciplex3.provenance.json")]
    if source[0]["sha256"] != provenance["sha256"]:
        raise F.FreezeMismatch("sciplex3 h5ad does not match its download provenance")
    for folder in (C.PREPARED, C.FROZEN):
        source += [file_entry(p) for p in sorted(folder.iterdir()) if p.is_file()]
    data = C.load()
    units = R.units("sciplex3")
    spec = C.load_protocol()
    keys = sorted({k for t in C.tiers(data, spec).values() for k in t.keys})
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    compounds = [{"compound": c, "identity": str(comp.skeleton[c]), "canonical_smiles": comp.smiles[c] if isinstance(comp.smiles[c], str) else None,
                  "group": str(comp.skeleton[c]), "scaffold": str(units.murcko_scaffold.get(c))} for c in comp.index]
    clusters = []
    for key in keys:
        for compound, row in sorted(data.index.get(key, {}).items()):
            r = data.conditions.iloc[row]
            plates = [str(p) for p in (r.plate_rep1, r.plate_rep2) if isinstance(p, str)]
            clusters.append({"action": C.action_id(key), "compound": compound, "batch": None, "plates": plates,
                             "replicates": int(r.replicates)})
    return {"manifest_version": "1", "dataset": "sciplex3", "role": "development",
            "study": {"name": "sci-Plex3 (Srivatsan et al., Science 2020), Figshare release", "accession": f"figshare:{provenance['article']}",
                      "version": "SrivatsanTrapnell2020_sciplex3.h5ad", "download_date": "2026-09-15",
                      "license": provenance.get("license"), "platform": "sci-RNA-seq3 with nuclear hashing"},
            "source": {"files": source}, "compounds": compounds,
            "contexts": [{"action": C.action_id(k), "cell_line": k[0], "time_hours": k[1], "dose_nM": k[2]} for k in keys],
            "clusters": clusters}


def l1000_manifest() -> dict:
    source = [file_entry(p) for p in sorted(LP.DATA.iterdir()) if p.is_file()]
    source += [file_entry(p) for p in sorted((LP.DATA / "subset48").iterdir()) if p.is_file()]
    source += [file_entry(p) for p in sorted(LP.OUT.iterdir()) if p.is_file()]
    data = LP.load()
    smiles = R.l1000_smiles()
    units = R.units("l1000")
    tiers = LP.tiers()
    keys = sorted({k for t in tiers.values() for k in t.keys})
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    compounds = [{"compound": c, "identity": str(comp.identity[c]), "canonical_smiles": smiles.get(c),
                  "group": str(comp.component[c]), "scaffold": None if pd.isna(comp.scaffold[c]) else str(comp.scaffold[c])}
                 for c in comp.index]
    clusters = []
    for key in keys:
        for compound, row in sorted(data.index.get(key, {}).items()):
            r = data.conditions.iloc[row]
            clusters.append({"action": C.action_id(key), "compound": compound, "batch": str(r.batch),
                             "plates": str(r.plates).split("|") if isinstance(r.plates, str) else [],
                             "replicates": int(r.n_wells)})
    return {"manifest_version": "1", "dataset": "l1000", "role": "development",
            "study": {"name": "LINCS L1000 Phase I, subset48 condition means joined to Level 5 signature metrics",
                      "accession": "GEO:GSE92742", "version": "GSE92742 Broad release metadata", "download_date": "2026-08-31",
                      "license": "GEO public release; no licence file in the local copy", "platform": "L1000 (978 landmarks)"},
            "source": {"files": source}, "compounds": compounds,
            "contexts": [{"action": C.action_id(k), "cell_line": k[0], "time_hours": k[1], "dose_nM": k[2]} for k in keys],
            "clusters": clusters}


def split_manifests(dataset: str) -> list[dict]:
    if dataset == "sciplex3":
        data = C.load()
        tiers = C.tiers(data, C.load_protocol())
    else:
        data = LP.load()
        tiers = LP.tiers()
    units = R.units(dataset)
    unit = R.UNIT[dataset]
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    out = []
    for name, tier in tiers.items():
        measured = {c for k in tier.keys for c, r in data.index.get(k, {}).items() if C.qc_passed(data, r)}
        partitions, boundaries = [], []
        for fold in range(5):
            test = sorted(c for c in tier.compounds if comp.fold[c] == fold)
            train = sorted(c for c in measured if comp.fold[c] != fold)

            def describe(members):
                return {"compounds": set(members), "groups": {units[unit].get(c) for c in members},
                        "scaffolds": {units["murcko_scaffold"].get(c) for c in members},
                        "batches": R.batches_of(data, dataset, set(members), tier.keys)}

            report = F.boundary_report(describe(train), describe(test))
            partitions.append({"name": f"fold{fold}", "role": "heldout_fold", "fold": fold, "compounds": test,
                               "groups": sorted({str(units[unit].get(c)) for c in test}),
                               "batches": sorted(R.batches_of(data, dataset, set(test), tier.keys))})
            boundaries.append({"train": f"not_fold{fold}", "test": f"fold{fold}", "kind": "internal", "report": report,
                               "problems": F.internal_boundary_problems(report)})
        out.append({"manifest_version": "1", "dataset": dataset, "tier": name, "unit": unit,
                    "partitions": partitions, "boundaries": boundaries})
    return out


def write(path: Path, value: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, indent=1, sort_keys=True, default=str).encode("utf-8"))
    return F.sha256_file(path)


def main() -> None:
    written = {}
    for builder in (sciplex3_manifest, l1000_manifest):
        manifest = builder()
        manifest["sha256"] = F.sha256_json({k: v for k, v in manifest.items() if k != "sha256"})
        F.check_manifest(manifest, "dataset_manifest")
        written[f"dataset_{manifest['dataset']}.json"] = write(OUT / f"dataset_{manifest['dataset']}.json", manifest)
    for dataset in ("sciplex3", "l1000"):
        for manifest in split_manifests(dataset):
            F.check_manifest(manifest, "split_manifest")
            problems = [p for b in manifest["boundaries"] for p in b["problems"]]
            if problems:
                raise AssertionError(f"{dataset} {manifest['tier']}: {problems}")
            name = f"split_{dataset}_{manifest['tier']}.json"
            written[name] = write(OUT / name, manifest)
    candidates = json.loads((HERE / "manifests" / "external_candidates.json").read_text(encoding="utf-8"))
    written["external_candidates.json(repository)"] = F.sha256_file(HERE / "manifests" / "external_candidates.json")
    (OUT / "index.json").write_bytes(json.dumps({"sha256": written, "external_blocker": candidates["blocker"]},
                                                indent=1).encode("utf-8"))
    print(json.dumps(written, indent=1))


if __name__ == "__main__":
    main()
