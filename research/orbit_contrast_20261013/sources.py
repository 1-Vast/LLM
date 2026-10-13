"""Load L1000 phase-1 signatures and compound knowledge into the evidence interface, then compile arrays.

File summary
- Path: research/orbit_contrast_20261013/sources.py
- Purpose: one place that reads local, previously exposed assets (PROTOCOL.md section 1), turns
  annotations into `evidence.EvidenceRecord`s, and compiles them into the index arrays the routes
  use. Outcomes (signatures) stay in arrays; evidence records carry only `value_ref` pointers.
- Knowledge parsing follows block Q (`research/knowledge_transfer_20261012/knowledge.py`), copied so
  this study stays self-contained: Hub targets with a sign from the MoA text; MAP-KG edges classed
  inhibition / activation / binding, metabolic edges dropped; binding never signs a route.
- Interfaces: `load_phase1`, `compound_store`, `compile_compounds`, `morgan`, `esm_features`,
  `fold_of`, `vehicle_thresholds`.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from evidence import Entity, EvidenceRecord, EvidenceStore, Query, Absent, transport

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PHASE1 = ROOT / "data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz"
PERT_INFO = ROOT / "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz"
HUB = ROOT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
MAPKG_EDGES = ROOT / "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
MAPKG_GENES = ROOT / "data/external/mapkg_20261009/GENE_tahoe_filtered.csv"
ESM = ROOT / "data/external/map_module_replacement_20261009/PROTEIN_FEATURES.npz"
CACHE = ROOT / "tmp/orbit_contrast_20261013"
SALT = "orbit-contrast:"
N_FOLDS = 5
HUB_DATE, MAPKG_DATE, L1000_DATE = "2020-03-24", "2026-10-08", "2017-12-01"

ACTIVATING = re.compile(r"agonist|activator|opener|inducer|potentiat|positive (allosteric )?modulator|enhances", re.I)
INHIBITING = re.compile(r"inhibit|antagonist|blocker|negative (allosteric )?modulator|degrader|suppress", re.I)
BINDING = re.compile(r"bind|radioligand|binding constant|drugmatrix|affinity|displacement", re.I)
METABOLIC = re.compile(r"substrate|reactant|metaboli", re.I)


def fold_of(key: str) -> int:
    return int(hashlib.sha256((SALT + key).encode()).hexdigest(), 16) % N_FOLDS


@lru_cache(maxsize=1)
def load_phase1() -> dict:
    z = np.load(PHASE1, allow_pickle=True)
    return {k: z[k] for k in z.files}


def vehicle_thresholds(z: dict, q: float = 0.95) -> np.ndarray:
    lines = list(z["line"])
    norms = np.linalg.norm(z["vehicle"].astype(np.float64), axis=1)
    return np.array([np.quantile(norms[z["vehicle_line"] == l], q) for l in lines])


def _relation_class(text: str) -> str | None:
    t = str(text)
    if METABOLIC.search(t):
        return None
    if ACTIVATING.search(t):
        return "activation"
    if INHIBITING.search(t):
        return "inhibition"
    return "binding"


def _hub() -> pd.DataFrame:
    hub = pd.read_csv(HUB, sep="\t", comment="!")
    hub["n"] = hub.pert_iname.astype(str).str.strip().str.lower()
    return hub.drop_duplicates("n").set_index("n")


def _mapkg() -> dict[int, dict[str, str]]:
    genes = pd.read_csv(MAPKG_GENES)
    symbol = dict(zip(genes["Gene stable ID"], genes["Gene name"].astype(str)))
    edges = pd.read_csv(MAPKG_EDGES)
    edges["kind"] = edges.relation.map(_relation_class)
    edges = edges.dropna(subset=["kind"])
    rank = {"inhibition": 0, "activation": 1, "binding": 2}
    out: dict[int, dict[str, str]] = {}
    for cid, gid, kind in zip(edges["Drug ID"], edges["Gene ID"], edges["kind"]):
        sym = symbol.get(gid)
        if not sym:
            continue
        d = out.setdefault(int(cid), {})
        if sym not in d or rank[kind] < rank[d[sym]]:
            d[sym] = kind
    return out


def compound_store(z: dict) -> tuple[EvidenceStore, list[Entity], list[str]]:
    """Evidence records for every phase-1 compound: Hub and MAP-KG target relations and Hub MoA."""
    pert = pd.read_csv(PERT_INFO, sep="\t", low_memory=False).set_index("pert_id")
    hub, mapkg = _hub(), _mapkg()
    store = EvidenceStore()
    entities, smiles = [], []
    for key, iname, pids in zip(z["compound"], z["iname"], z["pert_ids"]):
        ent = Entity("compound", "lincs_key", str(key))
        entities.append(ent)
        rows = pert.loc[[p for p in str(pids).split("|") if p in pert.index]]
        cids = pd.to_numeric(rows.pubchem_cid, errors="coerce").dropna().astype(int).unique().tolist()
        smiles.append(next((s for s in rows.canonical_smiles.astype(str) if s and s not in ("-666", "nan", "restricted")), ""))
        n = str(iname).strip().lower()
        if n in hub.index:
            row = hub.loc[n]
            moa = str(row.moa) if isinstance(row.moa, str) else ""
            kind = "activation" if ACTIVATING.search(moa) and not INHIBITING.search(moa) else "inhibition"
            for t in (str(row.target).split("|") if isinstance(row.target, str) else []):
                if t.strip():
                    store.add(EvidenceRecord(ent, "targets", Entity("gene", "symbol", t.strip()), -1 if kind == "inhibition" else 1,
                                             "curated_annotation", kind, None, "repurposing_hub_20200324", HUB_DATE, "curated"))
            for m in moa.split("|"):
                if m.strip():
                    store.add(EvidenceRecord(ent, "has_moa", Entity("moa", "hub", m.strip().lower()), 0,
                                             "curated_annotation", None, None, "repurposing_hub_20200324", HUB_DATE, "curated"))
        edges: dict[str, str] = {}
        for c in cids:
            for g, kind in mapkg.get(int(c), {}).items():
                if g not in edges or kind == "inhibition" or (kind == "activation" and edges[g] == "binding"):
                    edges[g] = kind
        for g, kind in edges.items():
            sign = {"inhibition": -1, "activation": 1, "binding": 0}[kind]
            store.add(EvidenceRecord(ent, "targets", Entity("gene", "symbol", g), sign, "assay_measurement", kind, None,
                                     "mapkg_20261009", MAPKG_DATE, "assay", depends_on=("chembl", "drugbank")))
    return store, entities, smiles


@dataclass
class CompoundKnowledge:
    """Compiled per-compound knowledge for one snapshot (as_of)."""

    signed: list[dict[str, int]]     # gene -> +1 (resembles knockdown, i.e. inhibition) / -1 (activation)
    tokens: list[frozenset[str]]     # "t:<gene>" for signed targets, "m:<moa>"
    has_hub_target: np.ndarray


def compile_compounds(store: EvidenceStore, entities: list[Entity], as_of: str = "9999-12-31") -> CompoundKnowledge:
    """Signed targets (Hub first, then MAP-KG; binding excluded) via the declared knockdown transport."""
    signed, tokens, hub_t = [], [], []
    kd_template = EvidenceRecord(Entity("perturbation", "l1000", "template"), "response", None, 0,
                                 "interventional_response", "genetic_knockdown", None, "gse92742_cgs", L1000_DATE, "assay")
    for ent in entities:
        q = Query(ent, None, "l1000_landmark_10uM_24h", as_of=as_of)
        targets = store.select(q, ent, "targets", intervention=("inhibition", "activation"))
        moa = store.select(q, ent, "has_moa")
        out: dict[str, int] = {}
        hub = False
        if not isinstance(targets, Absent):
            for r in sorted(targets, key=lambda r: r.source != "repurposing_hub_20200324"):
                if r.obj.id in out:
                    continue
                # the drug resembles the knockdown when it inhibits (relation sign -1) the target
                out[r.obj.id] = transport(kd_template, "inhibition", -r.sign).sign
                hub |= r.source == "repurposing_hub_20200324"
        toks = {"t:" + g for g in out}
        if not isinstance(moa, Absent):
            toks |= {"m:" + r.obj.id for r in moa}
        signed.append(out)
        tokens.append(frozenset(toks))
        hub_t.append(hub)
    return CompoundKnowledge(signed, tokens, np.array(hub_t))


def morgan(smiles: list[str]) -> np.ndarray:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "morgan_phase1.npz"
    digest = hashlib.sha256("\n".join(smiles).encode()).hexdigest()
    if path.is_file():
        z = np.load(path)
        if str(z["digest"]) == digest:
            return z["fps"]
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = np.zeros((len(smiles), 2048), dtype=bool)
    for i, s in enumerate(smiles):
        mol = Chem.MolFromSmiles(s) if s else None
        if mol is not None:
            fps[i] = gen.GetFingerprintAsNumPy(mol).astype(bool)
    np.savez_compressed(path, fps=fps, digest=np.array(digest))
    return fps


def esm_features(genes: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """(unit ESM-5120 rows aligned to `genes`, centred by the mean over all ESM genes; availability mask)."""
    z = np.load(ESM, allow_pickle=True)
    pos = {s: i for i, s in enumerate(z["symbols"])}
    X = z["esm5120"].astype(np.float64)
    X = X - X.mean(0)
    E = np.zeros((len(genes), X.shape[1]), np.float32)
    have = np.zeros(len(genes), bool)
    for i, g in enumerate(genes):
        if g in pos:
            v = X[pos[g]]
            E[i] = v / max(np.linalg.norm(v), 1e-12)
            have[i] = True
    return E, have
