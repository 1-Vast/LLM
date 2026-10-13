"""Sources, identity and typed provenance for the knowledge-reality study.

File summary
- Path: research/knowledge_reality_20261013/sources.py
- Purpose: one place that names every input file, matches compounds across sources, and turns raw
  drug-gene annotations into typed, provenance-qualified edges with an information tier.
- Core points:
  - Compounds are PRISM 19Q4 primary-screen treatments collapsed to the Broad core identifier.
    They are matched to MAP-KG drugs by InChIKey connectivity block, or by stripped name when the
    structure does not parse.
  - Every edge carries a relation type and a provenance class:
    - relation: `inh`, `act` or `bind`; metabolic relations (substrate, reactant, cofactor) are not
      target relations and are dropped;
    - provenance, from the source and the wording of the relation:
      - `curated_hub`: PRISM's own Repurposing Hub target and MoA columns;
      - `curated_mechanism`: MAP-KG template phrases from curated mechanism databases;
      - `binding_aggregate`: MAP-KG "exhibits strong binding" edges (measured affinity, assay
        format not stated);
      - `assay_biochemical`: a ChEMBL or PubChem assay description with no cell in it;
      - `assay_cell_engagement`: a cell-based assay of the target, such as a reporter in HEK293;
      - `assay_cell_phenotype`: a cell-based growth, proliferation, viability or death readout.
  - Information tier of an edge (see `maestro.information_tier`):
    - T0 admits curated, aggregate-binding and biochemical edges;
    - cell-based edges are observed perturbation responses of the compound, so they are T1;
    - phenotype edges are also outcome-proximal and are never used for this task.
- Interfaces: paths, `sha256`, `brd_core`, `strip_name`, `connectivity`, `relation_type`,
  `provenance_class`, `EDGE_TIER`, `load_prism_primary`, `load_ccle`, `hub_edges`,
  `mapkg_edges`.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRISM = ROOT / "data/external/prism_19q4/raw"
PRISM_LFC = PRISM / "primary-screen-replicate-collapsed-logfold-change.csv"
PRISM_TREATMENTS = PRISM / "primary-screen-replicate-collapsed-treatment-info.csv"
PRISM_LINES = PRISM / "primary-screen-cell-line-info.csv"
PRISM_SECONDARY = PRISM / "secondary-screen-replicate-collapsed-logfold-change.csv"
PRISM_SECONDARY_TREATMENTS = PRISM / "secondary-screen-replicate-collapsed-treatment-info.csv"
CCLE = ROOT / "data/external/depmap_19q4"
CCLE_EXPRESSION = CCLE / "CCLE_expression.csv"
CCLE_MUTATIONS = CCLE / "CCLE_mutations.csv"
CCLE_INFO = CCLE / "sample_info.csv"
HUB = ROOT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
MAPKG = ROOT / "data/external/mapkg_20261009"
MAPKG_EDGES = MAPKG / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
MAPKG_DRUGS = MAPKG / "DRUG_merged_drugs_with_residuals.csv"
MAPKG_GENES = MAPKG / "GENE_tahoe_filtered.csv"
CTRP_ARCHIVE = ROOT / "tmp/gdsc_transport_sources_v5/ctrp_archive.raw.txt"
GDSC2_RAW = ROOT / "tmp/gdsc_transport_sources_v3/GDSC2_public_raw_data_27Oct23.csv"
CACHE = ROOT / "tmp/knowledge_reality_20261013"

RELATIONS = ("inh", "act", "bind")
PROVENANCE = ("curated_hub", "curated_mechanism", "binding_aggregate", "assay_biochemical",
              "assay_cell_engagement", "assay_cell_phenotype")
EDGE_TIER = {"curated_hub": "T0", "curated_mechanism": "T0", "binding_aggregate": "T0",
             "assay_biochemical": "T0", "assay_cell_engagement": "T1", "assay_cell_phenotype": "T1"}
# Outcome-proximal: a growth or viability readout of the compound is the quantity this study
# predicts, so these edges are excluded at every tier, not only at T0.
OUTCOME_PROXIMAL = frozenset({"assay_cell_phenotype"})

ACTIVATING = re.compile(r"agonist|activator|activation|opener|inducer|potentiat|positive (allosteric )?modulat|enhances|stimulat", re.I)
INHIBITING = re.compile(r"inhibit|antagonist|blocker|blocks|negative (allosteric )?modulat|degrader|suppress|inverse agonist", re.I)
METABOLIC = re.compile(r"substrate|reactant|metaboli|cofactor|carrier|transported by", re.I)
TEMPLATE = re.compile(r"^(functions as|acts as|inhibits$|potentiates$|binds to$|positively and allosterically|negatively and allosterically|antagonizes|agonizes|activates$|blocks$)", re.I)
STRONG_BINDING = re.compile(r"^exhibits strong binding", re.I)
CELL = re.compile(r"\bcells?\b|cell[- ]based|cell line|\bHEK ?293|\bCHO\b|\bCOS-?7|\bBa/?F3|\bBAF3|xenograft|tumou?r|\bin vivo\b|primary culture|whole blood|platelet|erythrocyte|neutrophil|lymphocyte|monocyte|macrophage|PBMC|oocyte", re.I)
PHENOTYPE = re.compile(r"proliferat|growth|cytotox|viabilit|antiprolif|cell death|apoptos|surviv|colony|clonogenic|GI50|\bMTT\b|sulforhodamine|\bSRB\b|CellTiter|cell count|cell number|necrosis|antitumou?r|antineoplastic|anticancer", re.I)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    """LF bytes, so the digest does not depend on the platform."""

    Path(path).write_bytes((json.dumps(data, indent=1, sort_keys=False, default=_plain) + "\n").encode("utf-8"))


def _plain(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(type(x))


def brd_core(broad_id: str) -> str:
    return str(broad_id)[:13]


def strip_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def connectivity(smiles: str) -> str | None:
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    for part in str(smiles).split(","):
        mol = Chem.MolFromSmiles(part.strip())
        if mol is not None:
            key = Chem.MolToInchiKey(mol)
            return key.split("-")[0] if key else None
    return None


def relation_type(text: str) -> str | None:
    """Sign of a drug-gene relation; None for metabolic relations, which are not targets."""

    t = str(text)
    if METABOLIC.search(t) and not INHIBITING.search(t):
        return None
    if INHIBITING.search(t):
        return "inh"
    if ACTIVATING.search(t):
        return "act"
    return "bind"


def provenance_class(text: str) -> str:
    """Provenance of a MAP-KG relation, read from the relation's wording alone."""

    t = str(text).strip()
    if STRONG_BINDING.search(t):
        return "binding_aggregate"
    if TEMPLATE.search(t):
        return "curated_mechanism"
    if CELL.search(t):
        return "assay_cell_phenotype" if PHENOTYPE.search(t) else "assay_cell_engagement"
    if PHENOTYPE.search(t):
        return "assay_cell_phenotype"
    return "assay_biochemical"


def hub_relation(moa: str) -> str:
    """Sign of a Repurposing Hub mechanism string; most MoA strings name inhibitors."""

    if not isinstance(moa, str) or not moa.strip():
        return "bind"
    if INHIBITING.search(moa):
        return "inh"
    if ACTIVATING.search(moa):
        return "act"
    return "bind"


def load_prism_primary() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compound-by-line log2 fold change at 2.5 uM, collapsed to the Broad core.

    Treatments sharing a core (HTS and MTS004 runs of one compound) are averaged per line.
    Returns (lfc[core x line], compounds) where compounds holds name, SMILES, MoA and targets.
    """

    lfc = pd.read_csv(PRISM_LFC, index_col=0)
    info = pd.read_csv(PRISM_TREATMENTS)
    info["core"] = info["broad_id"].map(brd_core)
    cols = info.set_index("column_name")["core"]
    lfc = lfc.loc[:, [c for c in lfc.columns if c in cols.index]]
    by_core = lfc.T.groupby(cols.reindex(lfc.columns).values).mean()
    first = info.sort_values(["core", "screen_id"]).groupby("core").first()

    def merged(series: pd.Series) -> str:
        items = sorted({x.strip() for v in series.dropna() for x in str(v).split(",") if x.strip()})
        return ", ".join(items)

    compounds = pd.DataFrame({
        "name": first["name"],
        "smiles": first["smiles"],
        "moa": info.groupby("core")["moa"].apply(merged),
        "target": info.groupby("core")["target"].apply(merged),
        "phase": first["phase"],
        "screens": info.groupby("core")["screen_id"].apply(lambda s: ",".join(sorted(set(s)))),
    }).loc[by_core.index]
    return by_core, compounds


def load_ccle(lines: list[str], genes: set[str] | None = None) -> dict:
    """CCLE 19Q4 expression (log2 TPM+1) and protein-changing mutations for the given lines.

    Expression columns are 'SYMBOL (ENTREZ)'; the symbol is kept. Mutations are reduced to three
    gene-by-line indicators: any protein-changing, hotspot (TCGA or COSMIC), and deleterious.
    """

    header = pd.read_csv(CCLE_EXPRESSION, nrows=0).columns.tolist()
    symbols = [c.split(" (")[0] for c in header[1:]]
    keep = [0] + [i + 1 for i, s in enumerate(symbols) if genes is None or s in genes]
    expr = pd.read_csv(CCLE_EXPRESSION, usecols=keep, index_col=0)
    expr.columns = [c.split(" (")[0] for c in expr.columns]
    expr = expr.loc[:, ~expr.columns.duplicated()]
    present = [l for l in lines if l in expr.index]
    expr = expr.loc[present]
    mut = pd.read_csv(CCLE_MUTATIONS, usecols=["Hugo_Symbol", "Variant_Classification", "isDeleterious",
                                               "isTCGAhotspot", "isCOSMIChotspot", "DepMap_ID"])
    mut = mut[mut["DepMap_ID"].isin(present)]
    if genes is not None:
        mut = mut[mut["Hugo_Symbol"].isin(genes)]
    changing = ~mut["Variant_Classification"].isin(["Silent", "Intron", "3'UTR", "5'UTR", "IGR", "RNA", "lincRNA", "Flank"])
    mut = mut[changing]
    hot = mut["isTCGAhotspot"].fillna(False).astype(bool) | mut["isCOSMIChotspot"].fillna(False).astype(bool)
    dele = mut["isDeleterious"].fillna(False).astype(bool)
    pairs = {"any": set(zip(mut["Hugo_Symbol"], mut["DepMap_ID"])),
             "hotspot": set(zip(mut.loc[hot, "Hugo_Symbol"], mut.loc[hot, "DepMap_ID"])),
             "deleterious": set(zip(mut.loc[dele, "Hugo_Symbol"], mut.loc[dele, "DepMap_ID"]))}
    info = pd.read_csv(CCLE_INFO, index_col=0)
    return {"expression": expr, "mutations": pairs, "lines": present, "info": info.reindex(present)}


def hub_edges(compounds: pd.DataFrame) -> pd.DataFrame:
    """PRISM's own Hub annotations as typed edges (one per compound and target gene)."""

    rows = []
    for core, r in compounds.iterrows():
        rel = hub_relation(r["moa"])
        for g in [x.strip() for x in str(r["target"]).split(",") if x.strip() and x.strip() != "nan"]:
            rows.append((core, g, rel, "curated_hub", "prism_19q4_treatment_info", str(r["moa"])))
    return pd.DataFrame(rows, columns=["core", "gene", "relation", "provenance", "source", "evidence"])


def mapkg_identity(compounds: pd.DataFrame) -> tuple[dict, dict]:
    """PRISM core -> MAP-KG PubChem CIDs, by InChIKey connectivity, else stripped name.

    The MAP-KG connectivity table is computed once into tmp/ (it reads 187,088 SMILES).
    Returns (mapping, stats).
    """

    CACHE.mkdir(parents=True, exist_ok=True)
    table = CACHE / "mapkg_connectivity.json"
    drugs = pd.read_csv(MAPKG_DRUGS, dtype={"PubChem ID": str}, low_memory=False)
    if table.is_file():
        conn = json.loads(table.read_text(encoding="utf-8"))
    else:
        conn = {str(cid): connectivity(s) for cid, s in zip(drugs["PubChem ID"], drugs["smiles"])}
        write_json(table, conn)
    by_key: dict = {}
    for cid, key in conn.items():
        if key:
            by_key.setdefault(key, []).append(cid)
    by_name: dict = {}
    for cid, name in zip(drugs["PubChem ID"], drugs["Drug Name"]):
        by_name.setdefault(strip_name(name), []).append(str(cid))
    mapping, how = {}, {"connectivity": 0, "name": 0, "unmatched": 0}
    for core, r in compounds.iterrows():
        key = connectivity(r["smiles"]) if isinstance(r["smiles"], str) else None
        if key and key in by_key:
            mapping[core] = sorted(by_key[key]); how["connectivity"] += 1
        elif strip_name(r["name"]) in by_name and len(strip_name(r["name"])) >= 4:
            mapping[core] = sorted(by_name[strip_name(r["name"])]); how["name"] += 1
        else:
            how["unmatched"] += 1
    return mapping, how


def mapkg_edges(mapping: dict) -> pd.DataFrame:
    """MAP-KG drug-gene edges for the mapped compounds, typed and provenance-classed."""

    genes = pd.read_csv(MAPKG_GENES).set_index("Gene stable ID")["Gene name"]
    raw = pd.read_csv(MAPKG_EDGES, dtype={"Drug ID": str})
    cid_to_cores: dict = {}
    for core, cids in mapping.items():
        for c in cids:
            cid_to_cores.setdefault(c, []).append(core)
    raw = raw[raw["Drug ID"].isin(cid_to_cores)]
    rows = []
    for gid, cid, text in zip(raw["Gene ID"], raw["Drug ID"], raw["relation"]):
        rel = relation_type(text)
        symbol = genes.get(gid)
        if symbol is None or not isinstance(symbol, str):
            continue
        prov = provenance_class(text) if rel is not None else "metabolic"
        for core in cid_to_cores[cid]:
            rows.append((core, symbol, rel or "metabolic", prov, "mapkg_2026", str(text)[:200]))
    return pd.DataFrame(rows, columns=["core", "gene", "relation", "provenance", "source", "evidence"])
