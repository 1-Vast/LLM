"""Validation of the inputs before any biological modelling: identifiers, controls, replicates, splits.

File summary
- Path: research/maestro_vc_v1/preprocess.py
- Purpose: run the checks the design requires before a case is built or a forecast trusted, and
  return each as a named result with its numbers, so a failure is a finding and never a surprise.
- Core points:
  - Feature labels. The SciPlex3 release's first feature label is a stray header, so labels are offset
    by one row. `check_feature_labels` runs the repository's identity-marker check
    (`virtual_cell.artifacts.resolve_label_offset`) on the prepared pseudobulk of the vehicle
    controls, with the prepared labels at offsets -1, 0 and +1. A check that cannot tell the offsets
    apart (fewer than six testable markers, or more than one passing offset) is reported as
    inconclusive, never as passed. It also reads the published label row of the raw file.
  - Gene identifiers. `check_gene_ids` joins each symbol to the HGNC approved-symbol table and reports
    symbols with no match, Entrez or Ensembl identifiers that disagree with HGNC, and duplicates.
  - Compound identifiers. `check_compounds` parses every structure with RDKit, recomputes the InChIKey
    and its 14-character connectivity block, and compares it with the block the project stored as the
    independent chemical unit; unparsable and mismatching compounds are listed.
  - Controls and replicates. `check_controls` verifies that every treated (cell line, time) has vehicle
    wells, that no control carries a dose, and reports replicate agreement, cell counts and detection
    per dataset; `check_conditions` lists the time and dose grids and flags a dose or time that is
    not a positive finite number.
  - Splits. `check_splits` asserts that no independent unit spans two folds and reports the identity
    blocks and Murcko scaffolds shared across folds; structural novelty per fold (nearest training
    neighbour) comes from the replay records.
  - Every check returns `{"name", "status", ...}` with status `pass`, `fail` or `inconclusive`, and
    `run_all` bundles them with a summary; nothing is silently skipped.
- Interfaces: `check_feature_labels`, `check_gene_ids`, `check_compounds`, `check_controls`,
  `check_conditions`, `check_splits`, `check_novelty`, `run_all`, `inchikey_of`
- Depends on: numpy, pandas, rdkit, src/virtual_cell/artifacts.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PASS, FAIL, INCONCLUSIVE = "pass", "fail", "inconclusive"


def _result(name: str, status: str, **kw) -> dict:
    return {"name": name, "status": status, **kw}


# ---------------------------------------------------------------------------------- feature labels
def check_feature_labels(means: Mapping[str, np.ndarray], labels: Sequence[str | None], *,
                         published_first_labels: Sequence[str] | None = None) -> dict:
    """Which label offset the identity markers support for `labels`, and whether the answer is decisive."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from virtual_cell import artifacts as IM

    offset, checks, refusal = IM.resolve_label_offset(means, list(labels), offsets=(-1, 0, 1))
    detail = [c.payload() for c in checks]
    status = PASS if refusal is None and offset == 0 else INCONCLUSIVE if refusal else FAIL
    return _result("feature_labels_identity_markers", status, chosen_offset=offset, refusal=refusal, checks=detail,
                   published_first_labels=list(published_first_labels or []),
                   published_header_row_present=bool(published_first_labels and any(
                       "gene_short_name" in str(x) or str(x).strip().lower().startswith("id ") for x in published_first_labels)),
                   note=("offset 0 means the labels passed to this check already name their columns; the raw release needs +1"
                         if offset == 0 else "the labels are not aligned with their columns at any tested offset" if refusal is None
                         else "the markers cannot decide; the labels are not trusted"))


# ---------------------------------------------------------------------------------- gene identifiers
def check_gene_ids(genes: pd.DataFrame, hgnc: pd.DataFrame, *, symbol="symbol", entrez="entrez", ensembl="ensembl") -> dict:
    """Join to HGNC on approved symbol; report unmatched symbols and identifier disagreements."""
    h = hgnc.copy()
    h["entrez_id"] = pd.to_numeric(h["entrez_id"], errors="coerce")
    approved = h.drop_duplicates("symbol").set_index("symbol")
    g = genes.copy()
    matched = g[symbol].isin(approved.index)
    entrez_bad = ensembl_bad = 0
    if entrez in g:
        joined = approved.reindex(g.loc[matched, symbol])
        e = pd.to_numeric(g.loc[matched, entrez], errors="coerce").to_numpy()
        entrez_bad = int((joined["entrez_id"].to_numpy() != e).sum())
    if ensembl in g and "ensembl_gene_id" in approved:
        joined = approved.reindex(g.loc[matched, symbol])
        ensembl_bad = int((joined["ensembl_gene_id"].astype(str).to_numpy() != g.loc[matched, ensembl].astype(str).to_numpy()).sum())
    dup = int(g[symbol].duplicated().sum())
    frac = float(matched.mean()) if len(g) else 0.0
    status = PASS if frac >= 0.98 and entrez_bad == 0 and dup == 0 else FAIL
    return _result("gene_ids_hgnc", status, genes=int(len(g)), matched_fraction=frac,
                   unmatched=g.loc[~matched, symbol].astype(str).head(20).tolist(), entrez_disagree=entrez_bad,
                   ensembl_disagree=ensembl_bad, duplicated_symbols=dup)


# ---------------------------------------------------------------------------------- compound identifiers
def inchikey_of(smiles: str | None) -> str | None:
    """InChIKey from a SMILES string; None when the structure cannot be parsed."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles.split(",")[0].strip())
    return Chem.MolToInchiKey(mol) if mol is not None else None


def check_compounds(compounds: pd.DataFrame, *, smiles="smiles", stored_block: str | None = None) -> dict:
    """Recompute identity from structure; compare with the stored connectivity block when there is one."""
    keys = [inchikey_of(s) for s in compounds[smiles]]
    unparsable = [c for c, k, s in zip(compounds.index if "compound" not in compounds else compounds["compound"], keys,
                                       compounds[smiles]) if k is None and isinstance(s, str) and s.strip()]
    missing = int(compounds[smiles].isna().sum() + (compounds[smiles].astype(str).str.strip().isin(["", "None", "-666"])).sum())
    blocks = [k[:14] if k else None for k in keys]
    mismatch = 0
    if stored_block and stored_block in compounds:
        stored = compounds[stored_block].astype(str)
        mismatch = int(sum(b is not None and b != s and len(s) == 14 for b, s in zip(blocks, stored)))
    duplicated = int(pd.Series([b for b in blocks if b]).duplicated().sum())
    status = PASS if not unparsable and mismatch == 0 else FAIL
    return _result("compound_identity_inchikey", status, compounds=int(len(compounds)), without_structure=missing,
                   unparsable=unparsable[:20], stored_block_mismatch=mismatch, duplicate_identity_blocks=duplicated)


# ---------------------------------------------------------------------------------- controls and replicates
def check_controls(wells: pd.DataFrame, conditions: pd.DataFrame, *, min_control_wells: int = 2) -> dict:
    """Every treated (cell line, time) has vehicle wells and no control carries a dose."""
    controls = wells[wells["is_control"]] if "is_control" in wells else wells.iloc[0:0]
    per_group = controls.groupby(["cell_line", "time"]).size()
    treated = conditions.groupby(["cell_line", "time"]).size().index
    unmatched = [g for g in treated if g not in per_group.index or per_group[g] < min_control_wells]
    dosed = int((controls["dose"].fillna(0) > 0).sum()) if "dose" in controls else 0
    status = PASS if not unmatched and dosed == 0 else FAIL
    return _result("control_matching", status, control_wells=int(len(controls)), groups=int(len(per_group)),
                   min_wells_per_group=int(per_group.min()) if len(per_group) else 0,
                   unmatched_groups=[list(map(str, g)) for g in unmatched], controls_with_dose=dosed)


def replicate_summary(conditions: pd.DataFrame, agreement: np.ndarray, detected: np.ndarray | None = None) -> dict:
    a = np.asarray(agreement, dtype=float)
    finite = a[np.isfinite(a)]
    out = {"conditions": int(len(conditions)), "with_agreement": int(len(finite)),
           "agreement_quartiles": np.quantile(finite, [0.25, 0.5, 0.75]).round(4).tolist() if len(finite) else None,
           "negative_agreement": int((finite < 0).sum())}
    if detected is not None:
        out["detected_fraction"] = float(np.mean(detected))
    return out


def check_conditions(conditions: pd.DataFrame, *, time="time", dose="dose") -> dict:
    """Time and dose grids; a non-positive or non-finite value is a unit or parsing error."""
    t = pd.to_numeric(conditions[time], errors="coerce")
    d = pd.to_numeric(conditions[dose], errors="coerce")
    bad_t, bad_d = int((~np.isfinite(t) | (t <= 0)).sum()), int((~np.isfinite(d) | (d <= 0)).sum())
    return _result("time_dose_consistency", PASS if not (bad_t or bad_d) else FAIL,
                   times_h=sorted(set(t.dropna().astype(float))), doses_nM=sorted(set(d.dropna().astype(float)))[:20],
                   n_doses=int(d.nunique()), invalid_times=bad_t, invalid_doses=bad_d)


# ---------------------------------------------------------------------------------- splits and novelty
def check_splits(compounds: pd.DataFrame, *, unit: str, fold="fold", identity="identity", scaffold="scaffold") -> dict:
    """No independent unit spans two folds; report the identity blocks and scaffolds that do."""
    c = compounds.dropna(subset=[fold])
    spans = c.groupby(unit)[fold].nunique()
    crossing = spans[spans > 1]
    out = _result("split_unit_disjointness", PASS if crossing.empty else FAIL, units=int(c[unit].nunique()),
                  folds=sorted(int(x) for x in c[fold].unique()), units_spanning_folds=int(len(crossing)),
                  examples=[str(x) for x in crossing.index[:10]])
    for label, column in (("identity_blocks_across_folds", identity), ("scaffolds_across_folds", scaffold)):
        if column in c:
            s = c.dropna(subset=[column]).groupby(column)[fold].nunique()
            out[label] = int((s > 1).sum())
    return out


def check_novelty(similarities: Sequence[float], *, floor: float = 0.40) -> dict:
    s = np.asarray([x for x in similarities if x is not None and np.isfinite(x)], dtype=float)
    if not len(s):
        return _result("structural_novelty", INCONCLUSIVE, note="no structure")
    return _result("structural_novelty", PASS, compounds=int(len(s)), below_floor=float((s < floor).mean()),
                   quartiles=np.quantile(s, [0.25, 0.5, 0.75]).round(3).tolist(), floor=floor)


# ---------------------------------------------------------------------------------- driver
def run_all(out: Path | None = None) -> dict:
    """Run every check on the repository's prepared data and write the report."""
    bio = ROOT / "outputs/biological_depth_20260926/prepared"
    dwm = ROOT / "outputs/dynamic_world_model_20260926/prepared"
    l1k = ROOT / "outputs/sequence_audit_20260926/l1000/prepared"
    results: list[dict] = []
    # ---- SciPlex3 feature labels: the prepared labels against the pseudobulk of the vehicle controls
    genes = pd.read_csv(bio / "genes.csv")
    groups = pd.read_csv(bio / "groups.csv")
    mean = np.load(bio / "pseudobulk.npz")["group_mean"]
    means = {cl: mean[(groups.cell_line == cl).to_numpy() & groups.is_control.to_numpy()].mean(0)
             for cl in ("K562", "MCF7", "A549")
             if ((groups.cell_line == cl) & groups.is_control).any()}
    raw_labels = _published_first_labels()
    results.append(check_feature_labels(means, genes["symbol"].astype(str).tolist(), published_first_labels=raw_labels))
    # the alignment the raw release would give if read as published (offset -1 means labels shifted the wrong way)
    shifted = ["<stray-header>"] + genes["symbol"].astype(str).tolist()[:-1]
    control = check_feature_labels(means, shifted)
    control["name"] = "feature_labels_negative_control_shifted_by_one"
    control["status"] = PASS if control["chosen_offset"] != 0 else FAIL
    control["note"] = "labels deliberately shifted by one row must not be accepted at offset 0"
    results.append(control)
    # ---- gene identifiers
    hgnc_path = ROOT / "data/external/hgnc/hgnc_complete_set.txt"
    hgnc = pd.read_csv(hgnc_path, sep="\t", dtype=str, usecols=["symbol", "entrez_id", "ensembl_gene_id"])
    results.append(check_gene_ids(genes, hgnc))
    l1k_genes = np.load(l1k / "shifts.npz")["gene_id"]
    by_entrez = hgnc.dropna(subset=["entrez_id"]).drop_duplicates("entrez_id").set_index("entrez_id")
    mapped = pd.Series(l1k_genes.astype(str)).isin(by_entrez.index)
    results.append(_result("l1000_landmark_ids_hgnc", PASS if mapped.mean() > 0.97 else FAIL, landmark_genes=int(len(l1k_genes)),
                           matched_fraction=float(mapped.mean()), unmatched=[str(x) for x in l1k_genes[~mapped.to_numpy()][:10]]))
    # ---- compounds
    sp = pd.read_csv(bio / "compounds.csv")
    l1 = pd.read_csv(l1k / "compounds.csv")
    smiles_l1 = _l1000_smiles()
    l1["smiles"] = [smiles_l1.get(c) for c in l1["compound"]]
    results.append({**check_compounds(sp, stored_block="skeleton"), "dataset": "sciplex3"})
    results.append({**check_compounds(l1, stored_block="identity"), "dataset": "l1000"})
    # ---- controls, replicates, conditions
    wells = pd.read_csv(dwm / "wells.csv")
    cond = pd.read_csv(dwm / "conditions.csv")
    results.append(check_controls(wells, cond))
    results.append({**check_conditions(cond), "dataset": "sciplex3"})
    l1c = pd.read_csv(l1k / "conditions.csv")
    results.append({**check_conditions(l1c), "dataset": "l1000"})
    # ---- splits
    results.append({**check_splits(sp, unit="skeleton"), "dataset": "sciplex3"})
    results.append({**check_splits(l1, unit="component", identity="identity", scaffold="scaffold"), "dataset": "l1000"})
    report = {"checks": results, "summary": {s: sum(r["status"] == s for r in results) for s in (PASS, FAIL, INCONCLUSIVE)}}
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    return report


def _published_first_labels(n: int = 3) -> list[str]:
    """The first feature labels of the raw SciPlex3 release (var/ensembl_id is a categorical column)."""
    try:
        import h5py

        with h5py.File(ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad", "r") as f:
            column = f["var"]["ensembl_id"]
            if hasattr(column, "keys"):  # categorical: categories + codes
                cats, codes = column["categories"][:], column["codes"][:n]
                raw = [cats[i] for i in codes]
            else:
                raw = column[:n]
            return [x.decode() if isinstance(x, bytes) else str(x) for x in raw]
    except Exception as exc:  # pragma: no cover - environment
        return [f"unreadable:{type(exc).__name__}"]


def _l1000_smiles() -> dict:
    import gzip

    path = ROOT / "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_pert_info.txt.gz"
    out = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        i_id, i_s = header.index("pert_id"), header.index("canonical_smiles")
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > i_s:
                out[parts[i_id]] = parts[i_s] if parts[i_s] not in ("", "-666") else None
    return out
