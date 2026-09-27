"""GSE70138 (LINCS L1000 Phase II) as the external study: choosing lines and doses at 24 h.

File summary
- Path: research/belief_planning/external_phase2.py
- Purpose: define the external task from Phase II metadata before any Phase II measurement is read
  (`manifest`), then build the study inside the vault (`open_study`) with the frozen rules.
- Core points:
  - Task `P2LD`, the structure of the SciPlex3 B development tier:
    - three cell lines by four doses at 24 h;
    - at most two measurements and 16 assay-days (six per measurement);
    - the fixed expert order measures 10 uM in the first two lines.
    - The doses are the Phase II doses nearest SciPlex3 B's (10 nM, 100 nM, 1 uM, 10 uM): 0.04,
      0.12, 1.11 and 10 uM.
    - The lines are the three core Phase II lines with the most reference compounds measured at
      all four doses, ties broken by name (metadata only).
  - Known and new compounds:
    - A compound is *known* if its Broad ID is in GSE92742, or its InChIKey connectivity block is
      in GSE92742 or SciPlex3. Known compounds are the reference arm: their annotations were
      available in development, and they are the templates and references for the new compounds.
    - A compound is *new* otherwise. The test compounds are new compounds with a parsable
      structure, measured at all twelve conditions.
    - The test compounds' mechanism labels are read only in the vault, for scoring and for the
      forced-choice contrast. No policy sees them.
  - Frozen rules applied to the known references inside the vault:
    - Hypothesis pool: classes with at least six identities among references measured at all
      conditions, and at least two of them detected somewhere (the `lincs_prepare` rule).
    - Validator: calibrated on the references by `common.calibrate`.
    - World-model hyperparameters: by the frozen empirical-Bayes procedure.
  - Independent unit: connected components of test compounds sharing an InChIKey block or a
    Bemis-Murcko scaffold.
- Interfaces: `manifest`, `open_study`, `KEYS_RULE`
- Depends on: l1000_level5.py, tasks.py, research/sequence_audit (lincs_prepare, lincs_evaluate)
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np
import pandas as pd

from . import l1000_level5 as L5
from . import tasks as T

P, C, E, LP = T.P, T.C, T.E, T.LP
CORE_LINES = ("MCF7", "PC3", "A375", "HT29", "HA1E", "YAPC", "HELA")
DOSES_NM = (40.0, 120.0, 1110.0, 10000.0)
N_LINES = 3
BUDGET_DAYS = 16.0
REFERENCE_FOLD, TEST_FOLD = 0, 1
KEYS_RULE = ("three core Phase II lines with the most known reference compounds measured at all four doses "
             "(ties by name) x doses 0.04, 0.12, 1.11, 10 uM (nearest to SciPlex3 B's) at 24 h")


def days(key) -> float:
    return LP.days(key)


def manifest() -> dict:
    """Everything the external run needs that metadata can decide; no measurement, QC metric or label."""
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    sig2 = L5.sig_info("phase2")
    sig1 = L5.sig_info("phase1")
    pert1, pert2 = L5.pert_info("phase1"), L5.pert_info("phase2").set_index("pert_id")
    ids1 = set(sig1[sig1.pert_type == "trt_cp"].pert_id) | set(pert1.pert_id)
    blocks1 = {k.split("-")[0] for k in pert1.inchi_key if k and k != "-666"}
    blocks3 = L5.inchikey_blocks_sciplex3()
    treated = sig2[(sig2.pert_type == "trt_cp") & (sig2.time == L5.TIME) & sig2.dose_nm.isin(DOSES_NM)
                   & sig2.cell_id.isin(CORE_LINES)]
    cover = treated.groupby(["pert_id", "cell_id"]).dose_nm.apply(set)

    def block(pid):
        smiles = pert2.canonical_smiles.get(pid, "")
        mol = Chem.MolFromSmiles(smiles) if smiles and smiles != "-666" else None
        listed = pert2.inchi_key.get(pid, "")
        listed = listed.split("-")[0] if listed and listed != "-666" else None
        computed = Chem.MolToInchiKey(mol).split("-")[0] if mol is not None else None
        return mol is not None, listed, computed

    info, known, new = {}, set(), set()
    for pid in sorted(treated.pert_id.unique()):
        parsable, listed, computed = block(pid)
        blocks = {b for b in (listed, computed) if b}
        is_known = pid in ids1 or bool(blocks & blocks1) or bool(blocks & blocks3)
        info[pid] = {"parsable": parsable, "identity": listed or computed or pid,
                     "known_by": ("broad_id" if pid in ids1 else "inchikey_GSE92742" if blocks & blocks1 else
                                  "inchikey_SciPlex3" if blocks & blocks3 else None)}
        (known if is_known else new).add(pid)
    full = {(p, l) for (p, l), d in cover.items() if set(DOSES_NM) <= d}
    ranking = sorted(CORE_LINES, key=lambda l: (-sum((p, l) in full for p in known), l))
    lines = tuple(ranking[:N_LINES])
    keys = tuple((line, L5.TIME, dose) for line in lines for dose in DOSES_NM)
    fixed = tuple((line, L5.TIME, 10000.0) for line in lines[:2])
    measured_any = {p for (p, l) in cover.index if l in lines}
    references = sorted(p for p in known if p in measured_any)
    excluded = defaultdict(int)
    test = []
    for pid in sorted(new):
        if not all((pid, l) in full for l in lines):
            excluded["not_measured_at_all_twelve_conditions"] += 1
        elif not info[pid]["parsable"]:
            excluded["no_parsable_structure"] += 1
        else:
            test.append(pid)
    smiles = {p: pert2.canonical_smiles.get(p, "") for p in test}
    frame = pd.DataFrame({"compound": test, "identity": [info[p]["identity"] for p in test],
                          "scaffold": [LP.scaffold(smiles[p]) or "" for p in test]})
    component = LP.components(frame)
    ref_scaffolds = {LP.scaffold(pert2.canonical_smiles.get(p, "")) for p in references} - {None}
    dev_scaffolds = {LP.scaffold(s) for s in pert1.canonical_smiles if s and s != "-666"} - {None}
    batches2 = set(treated[treated.pert_id.isin(test)].batch)
    audit = {
        "known_compounds_measured": len(references), "new_compounds": len(new), "test_compounds": len(test),
        "excluded_new": dict(excluded),
        "known_by": {k: sum(1 for p in known if info[p]["known_by"] == k)
                     for k in ("broad_id", "inchikey_GSE92742", "inchikey_SciPlex3")},
        "test_identity_in_development": sum(1 for p in test if p in ids1 or info[p]["identity"] in blocks1 | blocks3),
        "test_scaffold_in_reference_arm": sum(1 for p in test if LP.scaffold(smiles[p]) in ref_scaffolds),
        "test_scaffold_in_GSE92742": sum(1 for p in test if LP.scaffold(smiles[p]) in dev_scaffolds),
        "test_batches": sorted(batches2),
        "test_batches_in_GSE92742": sorted(batches2 & set(sig1.batch)),
        "line_ranking": {l: sum((p, l) in full for p in known) for l in CORE_LINES},
    }
    return {
        "manifest_version": "1", "study": "GSE70138", "task": "P2LD", "keys_rule": KEYS_RULE,
        "keys": [list(k) for k in keys], "fixed_order": [list(k) for k in fixed], "budget_days": BUDGET_DAYS,
        "max_measurements": 2, "reference_compounds": references,
        "test_compounds": [{"compound": p, "identity": info[p]["identity"], "unit": component[p],
                            "scaffold": frame.set_index("compound").scaffold[p] or None, "smiles": smiles[p]}
                           for p in test],
        "audit": audit,
        "sources": {str(path.relative_to(T.ROOT)).replace("\\", "/"): L5.LP.digest(path) for path in (
            L5.FILES["phase2"]["sig_info"], L5.FILES["phase2"]["pert_info"], L5.FILES["phase1"]["sig_info"],
            L5.FILES["phase1"]["pert_info"])},
    }


def open_study(man: dict):
    """Inside the vault: measurements, QC, detection and labels; then the frozen pool, validator and episodes."""
    keys = tuple(tuple(k) for k in man["keys"])
    references = list(man["reference_compounds"])
    test = pd.DataFrame(man["test_compounds"])
    conditions, shift, null = L5.build_conditions("phase2", keys, set(references) | set(test.compound))
    labels = L5.annotations("phase2", set(references) | set(test.compound))
    pert2 = L5.pert_info("phase2").set_index("pert_id")
    qc = conditions[conditions.qc]
    measured = qc.groupby("compound").apply(lambda g: set(zip(g.cell_line, g.time, g.dose)), include_groups=False)
    detected_any = set(qc[qc.detected].compound)
    ref_rows = []
    for pid in references:
        ident = pert2.inchi_key.get(pid, "")
        ref_rows.append({"compound": pid, "klass": labels.get(pid, {}).get("klass"),
                         "identity": ident.split("-")[0] if ident and ident != "-666" else pid,
                         "scaffold": LP.scaffold(pert2.canonical_smiles.get(pid, "")),
                         "smiles": pert2.canonical_smiles.get(pid) or None, "fold": REFERENCE_FOLD, "role": "reference"})
    refs = pd.DataFrame(ref_rows)
    is_complete = pd.Series([set(keys) <= measured.get(c, set()) for c in refs.compound], index=refs.index)
    complete = refs[is_complete & refs.klass.notna()]
    stats = {}
    for klass, group in complete.groupby("klass"):
        stats[klass] = {"identities": int(group.identity.nunique()),
                        "detected_identities": int(group[group.compound.isin(detected_any)].identity.nunique())}
    pool = tuple(sorted(k for k, s in stats.items() if s["identities"] >= LP.POOL_MIN_IDENTITIES
                        and s["detected_identities"] >= LP.POOL_MIN_DETECTED_IDENTITIES))
    test = test.assign(klass=[labels.get(c, {}).get("klass") for c in test.compound], fold=TEST_FOLD, role="test")
    eligible = tuple(sorted(c for c, k in zip(test.compound, test.klass) if k in pool))
    compounds = pd.concat([refs, test[["compound", "klass", "identity", "scaffold", "smiles", "fold", "role"]]],
                          ignore_index=True)
    compounds = compounds[compounds.klass.isin(pool) | (compounds.role == "test")].copy()
    compounds["component"] = compounds.compound.map({**{r: f"r:{r}" for r in references},
                                                     **dict(zip(test.compound, test.unit))})
    compounds["skeleton"] = compounds.identity
    keep = conditions.compound.isin(set(compounds.compound)).to_numpy()
    conditions = conditions[keep].reset_index(drop=True)
    data = L5.as_data(conditions, shift[keep], compounds.reset_index(drop=True))
    tier = C.Tier("P2LD", keys, pool, eligible)
    detected = data.conditions.detected.to_numpy(bool)
    ctx = T.LE.context(data, tier, TEST_FOLD, detected, C.load_protocol())
    setting = P.Setting("gse70138", keys, tuple(tuple(k) for k in man["fixed_order"]), days, BUDGET_DAYS)
    summary = {"vehicle_null": null, "conditions": int(len(conditions)), "qc_passed": int(conditions.qc.sum()),
               "detected": int(conditions.detected.sum()),
               "detected_by_key": {C.action_id(k): [int(g.detected.sum()), int(g.qc.sum())]
                                   for k, g in conditions.groupby(["cell_line", "time", "dose"])},
               "pool": list(pool), "class_stats": stats, "eligible_test_compounds": len(eligible),
               "test_labelled_single_moa": int(test.klass.notna().sum()),
               "test_units": int(test[test.compound.isin(eligible)].unit.nunique()),
               "validator": {k: v for k, v in ctx.params.items() if k != "grid"}}
    return data, ctx, setting, summary


def write_manifest(path) -> dict:
    man = manifest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(man, indent=1, sort_keys=True).encode("utf-8"))
    return man


if __name__ == "__main__":
    out = T.ROOT / "research" / "belief_planning" / "manifests" / "gse70138_p2ld.json"
    m = write_manifest(out)
    print(json.dumps({k: m[k] for k in ("keys", "fixed_order")}, indent=None))
    print(json.dumps(m["audit"], indent=1))
