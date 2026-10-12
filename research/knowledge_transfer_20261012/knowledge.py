"""Knowledge sources for block Q: curated targets and mechanism, MAP-KG drug-gene edges, chemistry.

Every source is keyed to a compound record built from L1000 metadata (name, PubChem CID, SMILES).
* Repurposing Hub (``repurposing_drugs_20200324.txt``): targets by name; sign from the mechanism
  string (agonist, activator, opener or inducer read as activation; everything else as inhibition).
* MAP-KG (Feng et al., Nat. Mach. Intell. 2026): drug-gene edges by PubChem CID with a relation
  text, classed as inhibition, activation or binding. Metabolic edges (substrate, reactant) are not
  targets and are dropped.
* Chemistry: Morgan fingerprints (radius 2, 2,048 bits) from the canonical SMILES.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
MAPKG_EDGES = ROOT / "data/external/mapkg_20261009/DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
MAPKG_GENES = ROOT / "data/external/mapkg_20261009/GENE_tahoe_filtered.csv"

ACTIVATING = re.compile(r"agonist|activator|opener|inducer|potentiat|positive (allosteric )?modulator|enhances", re.I)
INHIBITING = re.compile(r"inhibit|antagonist|blocker|negative (allosteric )?modulator|degrader|suppress", re.I)
BINDING = re.compile(r"bind|radioligand|binding constant|drugmatrix|affinity|displacement", re.I)
METABOLIC = re.compile(r"substrate|reactant|metaboli", re.I)


def relation_class(text: str) -> str | None:
    t = str(text)
    if METABOLIC.search(t):
        return None
    if ACTIVATING.search(t):
        return "act"
    if INHIBITING.search(t):
        return "inh"
    if BINDING.search(t):
        return "bind"
    return "bind"


@dataclass
class CompoundKnowledge:
    key: str
    name: str
    cids: tuple[int, ...] = ()
    smiles: str = ""
    hub_targets: dict[str, int] = field(default_factory=dict)     # symbol -> +1 inhibition, -1 activation
    hub_moa: frozenset[str] = frozenset()
    mapkg: dict[str, str] = field(default_factory=dict)           # symbol -> inh | act | bind

    def signed_targets(self, *, include_binding: bool = False) -> dict[str, int]:
        """Target -> sign (+1: the drug should resemble the knockdown, -1: the opposite).

        Curated targets take precedence; MAP-KG adds signed edges, and binding edges only on request.
        """
        out = dict(self.hub_targets)
        for g, kind in self.mapkg.items():
            if g in out:
                continue
            if kind == "inh" or (kind == "bind" and include_binding):
                out[g] = 1
            elif kind == "act":
                out[g] = -1
        return out

    def target_set(self) -> frozenset[str]:
        return frozenset(self.signed_targets())


def load_hub() -> pd.DataFrame:
    hub = pd.read_csv(HUB, sep="\t", comment="!")
    hub["n"] = hub.pert_iname.astype(str).str.strip().str.lower()
    return hub.drop_duplicates("n").set_index("n")


def load_mapkg() -> dict[int, dict[str, str]]:
    genes = pd.read_csv(MAPKG_GENES)
    symbol = dict(zip(genes["Gene stable ID"], genes["Gene name"].astype(str)))
    edges = pd.read_csv(MAPKG_EDGES)
    edges["kind"] = edges.relation.map(relation_class)
    edges = edges.dropna(subset=["kind"])
    rank = {"inh": 0, "act": 1, "bind": 2}
    out: dict[int, dict[str, str]] = {}
    for cid, gid, kind in zip(edges["Drug ID"], edges["Gene ID"], edges["kind"]):
        sym = symbol.get(gid)
        if not sym:
            continue
        d = out.setdefault(int(cid), {})
        if sym not in d or rank[kind] < rank[d[sym]]:
            d[sym] = kind
    return out


def hub_entry(hub: pd.DataFrame, name: str) -> tuple[dict[str, int], frozenset[str]]:
    n = str(name).strip().lower()
    if n not in hub.index:
        return {}, frozenset()
    row = hub.loc[n]
    moa = str(row.moa) if isinstance(row.moa, str) else ""
    sign = -1 if ACTIVATING.search(moa) and not INHIBITING.search(moa) else 1
    targets = {t.strip(): sign for t in str(row.target).split("|") if isinstance(row.target, str) and t.strip()}
    return targets, frozenset(m.strip().lower() for m in moa.split("|") if m.strip())


def build_knowledge(keys, names, cid_lists, smiles_list) -> list[CompoundKnowledge]:
    hub = load_hub()
    mapkg = load_mapkg()
    out = []
    for key, name, cids, smi in zip(keys, names, cid_lists, smiles_list):
        targets, moa = hub_entry(hub, name)
        edges: dict[str, str] = {}
        for c in cids:
            for g, kind in mapkg.get(int(c), {}).items():
                if g not in edges or kind == "inh" or (kind == "act" and edges[g] == "bind"):
                    edges[g] = kind
        out.append(CompoundKnowledge(key=key, name=name, cids=tuple(int(c) for c in cids), smiles=smi or "",
                                     hub_targets=targets, hub_moa=moa, mapkg=edges))
    return out


def morgan_matrix(smiles_list, n_bits: int = 2048, radius: int = 2) -> np.ndarray:
    """Boolean fingerprint matrix; an unparsable or missing SMILES gives an all-zero row."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    fps = np.zeros((len(smiles_list), n_bits), dtype=bool)
    for i, s in enumerate(smiles_list):
        if not s or not isinstance(s, str) or s in ("-666", "restricted"):
            continue
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            continue
        fps[i] = gen.GetFingerprintAsNumPy(mol).astype(bool)
    return fps


def tanimoto(fps: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Tanimoto similarity of each row of ``fps`` to ``query`` (0 where either is empty)."""
    a = fps.astype(np.float32)
    q = query.astype(np.float32)
    inter = a @ q
    union = a.sum(1) + q.sum() - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)


def phase1_records(npz) -> list[CompoundKnowledge]:
    pert = pd.read_csv(ROOT / "data/external/lincs_l1000_gse92742/GSE92742_Broad_LINCS_pert_info.txt.gz",
                       sep="\t", low_memory=False).set_index("pert_id")
    keys, names, cids, smiles = [], [], [], []
    for key, iname, pids in zip(npz["compound"], npz["iname"], npz["pert_ids"]):
        rows = pert.loc[[p for p in str(pids).split("|") if p in pert.index]]
        c = pd.to_numeric(rows.pubchem_cid, errors="coerce").dropna().astype(int).unique().tolist()
        smi = next((s for s in rows.canonical_smiles.astype(str) if s and s not in ("-666", "nan", "restricted")), "")
        keys.append(str(key)); names.append(str(iname)); cids.append(c); smiles.append(smi)
    return build_knowledge(keys, names, cids, smiles)
