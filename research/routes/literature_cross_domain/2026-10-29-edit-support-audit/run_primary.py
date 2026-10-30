"""Frozen metadata-only support audit. Never access response columns."""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from itertools import combinations, product
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import zipfile

import pyarrow.parquet as pq
from rdkit import Chem, rdBase
from rdkit.Chem import rdMMPA
from rdkit.Chem.Scaffolds import MurckoScaffold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = ROOT / "tmp/extq1/gsdc_well_stats.zip"
NAMES = ROOT / "tmp/extq1/gdsc-007_matrix_results.csv"
CHEMICAL = HERE / "sources/root_metadata/tahoe_drug_metadata.body"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
METALS = {3, 4, 11, 12, 13} | set(range(19, 32)) | set(range(37, 51)) | set(range(55, 85)) | set(range(87, 117))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump(name, obj):
    with (HERE / f"primary_{name}.json").open("x", encoding="utf-8") as target:
        json.dump(obj, target, ensure_ascii=False, indent=2)
        target.write("\n")


def admitted(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, "parse_failure"
    if len(Chem.GetMolFrags(mol)) != 1:
        return None, "multiple_components"
    if not any(a.GetAtomicNum() == 6 for a in mol.GetAtoms()):
        return None, "no_carbon"
    if sum(a.GetFormalCharge() for a in mol.GetAtoms()) != 0:
        return None, "nonzero_charge"
    if any(a.GetAtomicNum() in METALS for a in mol.GetAtoms()):
        return None, "metal"
    if mol.GetNumHeavyAtoms() < 6:
        return None, "too_small"
    return mol, None


def normalize_fragment(mol):
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetIsotope(0)
            atom.SetAtomMapNum(1)
    parameters = Chem.RemoveHsParameters()
    parameters.removeDummyNeighbors = False
    parameters.removeIsotopes = False
    parameters.showWarnings = False
    return Chem.RemoveHs(mol, parameters)


def fragments(mol):
    explicit = Chem.AddHs(mol)
    cuts = [b.GetIdx() for b in explicit.GetBonds()
            if not b.IsInRing() and b.GetBondType() == Chem.BondType.SINGLE]
    found = set()
    if not cuts:
        return found
    for _, combined in rdMMPA.FragmentMol(explicit, cuts, 1, 1, True):
        pieces = [normalize_fragment(p) for p in Chem.GetMolFrags(combined, asMols=True)]
        assert len(pieces) == 2
        for core, variable in (pieces, pieces[::-1]):
            ch = sum(a.GetAtomicNum() > 1 for a in core.GetAtoms())
            vh = sum(a.GetAtomicNum() > 1 for a in variable.GetAtoms())
            if ch < 6 or vh > 8 or ch < 2 * vh:
                continue
            if vh == 0 and sorted(a.GetAtomicNum() for a in variable.GetAtoms()) != [0, 1]:
                continue
            dummy = [a for a in core.GetAtoms() if a.GetAtomicNum() == 0]
            assert len(dummy) == 1 and dummy[0].GetDegree() == 1
            neighbor = dummy[0].GetNeighbors()[0]
            bond = core.GetBondBetweenAtoms(dummy[0].GetIdx(), neighbor.GetIdx())
            attachment = (neighbor.GetAtomicNum(), neighbor.GetIsAromatic(), neighbor.IsInRing(), str(bond.GetBondType()))
            found.add((Chem.MolToSmiles(core, isomericSmiles=True),
                       Chem.MolToSmiles(variable, isomericSmiles=True), attachment))
    return found


def engineering_checks():
    def edit_keys(a, b):
        left = fragments(Chem.MolFromSmiles(a))
        right = fragments(Chem.MolFromSmiles(b))
        return {(tuple(sorted((va, vb))), attach)
                for ca, va, attach in left for cb, vb, ab in right
                if ca == cb and attach == ab and va != vb and a != b}
    one = edit_keys("c1ccccc1", "Cc1ccccc1")
    two = edit_keys("Fc1ccccc1", "Cc1ccc(F)cc1")
    common = one & two
    assert common and any(set(v) == {"[H][*:1]", "C[*:1]"} for v, _ in common)
    assert not edit_keys("c1ccccc1", "c1ccccc1")
    assert admitted("c1ccccc1.[Na+]")[0] is None
    assert admitted("C[N+](C)(C)CCC")[0] is None
    return {"synthetic_only": True, "checks": 4, "common_edits": sorted(common)}


def main():
    hashes = {str(p): sha(p) for p in (ARCHIVE, NAMES, CHEMICAL, HERE / "support_protocol.md", Path(__file__))}
    assert hashes[str(ARCHIVE)] == "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
    assert hashes[str(CHEMICAL)] == "7a04c7a6611e74c92253163b994ff0a47191928ee7511f1c2ca508cee0e79f28"
    checks = engineering_checks()
    names_by_id, ids_by_name = defaultdict(set), defaultdict(set)
    matrix_rows = 0
    with NAMES.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            matrix_rows += 1
            for side in (1, 2):
                drug, name = row[f"lib{side}_ID"].strip(), row[f"lib{side}_name"].strip().casefold()
                names_by_id[drug].add(name)
                ids_by_name[name].add(drug)
    chemical_by_name = defaultdict(set)
    for row in pq.read_table(CHEMICAL, columns=["drug", "canonical_smiles", "pubchem_cid"]).to_pylist():
        chemical_by_name[row["drug"].strip().casefold()].add((row["canonical_smiles"], str(row["pubchem_cid"])))

    # This loop transiently tokenizes a row, then semantically accesses ONLY the eight frozen metadata fields.
    selected, metadata_counts, all_ids, all_cells = {}, Counter(), set(), set()
    decimal_cache = {}
    with zipfile.ZipFile(ARCHIVE) as archive, archive.open(MEMBER) as stream:
        for row in csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")):
            metadata_counts["rows"] += 1
            project, cell = row["PROJECT_ID"].strip(), row["MASTER_CELL_ID"].strip()
            all_cells.add((project, cell))
            for side in (1, 2):
                drug, ref = row[f"lib{side}_drug_id"].strip(), row[f"lib{side}_drug"].strip()
                text = row[f"lib{side}_conc"].strip()
                all_ids.add(drug)
                if text not in decimal_cache:
                    try:
                        value = Decimal(text)
                        decimal_cache[text] = value if value.is_finite() and value > 0 else None
                    except InvalidOperation:
                        decimal_cache[text] = None
                dose = decimal_cache[text]
                if dose is None or not ref:
                    metadata_counts["invalid_dose_or_ref_sides"] += 1
                if not ref:
                    continue
                key = (project, cell, drug)
                if key not in selected or ref < selected[key][0]:
                    selected[key] = (ref, set())
                if ref == selected[key][0] and dose is not None:
                    selected[key][1].add(dose)
    dose_records = [{"project": p, "cell": c, "drug_id": d, "ref": r,
                     "doses_uM": [str(q) for q in sorted(qs)]}
                    for (p, c, d), (r, qs) in sorted(selected.items())]
    dump("metadata", dose_records)

    mapping, mol_by_smiles, ids_by_smiles = [], {}, defaultdict(set)
    for drug in sorted(all_ids):
        record = {"drug_id": drug, "names": sorted(names_by_id[drug])}
        if len(names_by_id[drug]) != 1:
            record["status"] = "missing_or_ambiguous_id_name"
        else:
            name = next(iter(names_by_id[drug]))
            records = chemical_by_name[name]
            if len(ids_by_name[name]) != 1:
                record["status"] = "ambiguous_name_id"
            elif len(records) != 1:
                record["status"] = "no_exact_chemical_match" if not records else "ambiguous_chemical_record"
            else:
                smiles, cid = next(iter(records))
                record.update(source_smiles=smiles, pubchem_cid=cid)
                mol, reason = admitted(smiles) if smiles else (None, "missing_smiles")
                record["status"] = reason or "admitted"
                if mol is not None:
                    canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
                    record["canonical_smiles"] = canonical
                    mol_by_smiles[canonical] = mol
                    ids_by_smiles[canonical].add(drug)
        mapping.append(record)
    dump("mapping", mapping)

    by_core = defaultdict(lambda: defaultdict(set))
    fragment_count = 0
    for smiles, mol in sorted(mol_by_smiles.items()):
        for core, variable, attach in fragments(mol):
            by_core[(core, attach)][variable].add(smiles)
            fragment_count += 1
    structures = set()
    for (core, attach), variables in sorted(by_core.items()):
        for va, vb in combinations(sorted(variables), 2):
            for ma, mb in product(sorted(variables[va]), sorted(variables[vb])):
                if ma != mb:
                    structures.add((core, va, vb, attach, ma, mb))
    doses = defaultdict(dict)
    for (project, cell, drug), (_, qs) in selected.items():
        doses[drug][(project, cell)] = qs
    edges, supported = [], []
    for core, va, vb, attach, ma, mb in sorted(structures):
        edit = json.dumps([va, vb, attach], separators=(",", ":"))
        scaffold = Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(Chem.MolFromSmiles(core)), isomericSmiles=True)
        for da, db in product(sorted(ids_by_smiles[ma]), sorted(ids_by_smiles[mb])):
            opportunities = defaultdict(set)
            for project, cell in sorted(doses[da].keys() & doses[db].keys()):
                for dose in doses[da][(project, cell)] & doses[db][(project, cell)]:
                    opportunities[(project, dose)].add(cell)
            rectangles = [{"project": p, "q_uM": str(q), "cells": sorted(cs)}
                          for (p, q), cs in sorted(opportunities.items()) if len(cs) >= 2]
            edge = {"core": core, "scaffold": scaffold, "variable_from": va, "variable_to": vb,
                    "attachment": attach, "edit_key": edit, "molecule_from": ma, "molecule_to": mb,
                    "drug_from": da, "drug_to": db, "two_cell_opportunities": rectangles}
            edges.append(edge)
            if rectangles:
                supported.append(edge)
    dump("edges", edges)
    grouped = defaultdict(list)
    for index, edge in enumerate(edges):
        if edge["two_cell_opportunities"]:
            grouped[edge["edit_key"]].append(index)
    repetitions, examples, different_scaffold = 0, [], 0
    for edit, indices in sorted(grouped.items()):
        for ia, ib in combinations(indices, 2):
            a, b = edges[ia], edges[ib]
            if a["core"] == b["core"] or len({a["molecule_from"], a["molecule_to"], b["molecule_from"], b["molecule_to"]}) != 4:
                continue
            ar = {(r["project"], Decimal(r["q_uM"])): set(r["cells"]) for r in a["two_cell_opportunities"]}
            br = {(r["project"], Decimal(r["q_uM"])): set(r["cells"]) for r in b["two_cell_opportunities"]}
            for project, dose in sorted(ar.keys() & br.keys()):
                cells = sorted(ar[(project, dose)] & br[(project, dose)])
                if len(cells) >= 2:
                    repetitions += 1
                    distinct = a["scaffold"] != b["scaffold"]
                    different_scaffold += distinct
                    if len(examples) < 20:
                        examples.append({"edit_key": edit, "edge_indices": [ia, ib], "project": project,
                                         "q_uM": str(dose), "cells": cells, "different_scaffolds": distinct})
    dump("summary", {"input_sha256": hashes, "rdkit_version": rdBase.rdkitVersion,
                     "engineering_checks": checks, "matrix_rows": matrix_rows, "metadata_counts": metadata_counts,
                     "project_cell_count": len(all_cells), "raw_drug_ids": len(all_ids),
                     "selected_project_cell_drug_count": len(selected),
                     "mapping_status_counts": Counter(r["status"] for r in mapping),
                     "admitted_unique_molecules": len(mol_by_smiles), "fragment_records": fragment_count,
                     "canonical_structure_edges": len(structures), "id_edges": len(edges),
                     "two_cell_supported_id_edges": len(supported),
                     "repeated_edit_parent_pair_project_dose_count": repetitions,
                     "different_scaffold_parent_pair_project_dose_count": different_scaffold,
                     "deterministic_examples": examples,
                     "qualification": "structural_opportunity_present" if repetitions else "not_ready_in_mapped_subset",
                     "full_measurement_qualification": "unknown", "response_values_accessed": False})
    print(json.dumps({"rows": metadata_counts["rows"], "mapped_molecules": len(mol_by_smiles),
                      "id_edges": len(edges), "repeated_edit_support": repetitions}))


if __name__ == "__main__":
    if sys.argv[1:] == ["--engineering-only"]:
        print(json.dumps(engineering_checks()))
    else:
        assert not sys.argv[1:]
        main()
