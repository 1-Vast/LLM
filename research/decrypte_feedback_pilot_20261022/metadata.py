"""Read chemical identities only and freeze scaffold-disjoint value partitions."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from rdkit import Chem, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'
PRIOR = ROOT / 'log/20261022/decrypte_source_qualification'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def main():
    destination = OUT / 'PARTITIONS.json'
    assert not destination.exists(), 'Partition is immutable once written'
    source = PRIOR / 'supplement.xlsx'
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha == 'ef30d2fd91783e9cd23ca9a592c6e679912ea551a17b20a257cc23fef47db956'
    with zipfile.ZipFile(source) as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        sheet = next(s for s in workbook.findall('s:sheets/s:sheet', NS) if s.attrib['name'] == 'Table S1 - Cpd info')
        rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rel = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}[rid]
        member = rel.lstrip('/') if rel.startswith('/') else 'xl/' + rel
        strings = ET.fromstring(z.read('xl/sharedStrings.xml'))
        records = []
        for row in ET.fromstring(z.read(member)).findall('s:sheetData/s:row', NS):
            index = int(row.attrib['r'])
            if index == 1:
                continue
            record = {'row': index}
            for cell in row.findall('s:c', NS):
                column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                if column not in ('A', 'C', 'D', 'E'):
                    continue
                if cell.find('s:v', NS) is None:
                    continue
                assert cell.attrib.get('t') == 's' and cell.find('s:f', NS) is None, (cell.attrib['r'], cell.attrib.get('t'))
                record[{'A': 'drug', 'C': 'type', 'D': 'chembl', 'E': 'smiles'}[column]] = ''.join(strings[int(cell.find('s:v', NS).text)].itertext())
            if 'drug' not in record:
                continue
            if 'smiles' not in record:
                record['group'] = 'UNKNOWN_STRUCTURE'
                records.append(record)
                continue
            mol = Chem.MolFromSmiles(record['smiles'])
            assert mol is not None, record['drug']
            fragments = Chem.GetMolFrags(mol, asMols=True)
            parent = max(fragments, key=lambda m: (m.GetNumHeavyAtoms(), Chem.MolToSmiles(m)))
            scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=parent, includeChirality=False)
            # Empty scaffolds cannot make all unrelated acyclic molecules one artificial family.
            record['group'] = scaffold or ('ACYCLIC:' + Chem.MolToSmiles(parent, isomericSmiles=False))
            records.append(record)
    identities = json.loads((PRIOR / 'IDENTITIES.json').read_text(encoding='utf-8'))['rows']
    functional = set(r['drug'] for r in identities if r['cell'] == 'Jurkat')
    aliases = {'Cyclosporin A ': 'Cyclosporin A', 'TG-100-115': 'TG100-115'}
    for record in records:
        if record['drug'] in aliases:
            record['chemical_table_drug'] = record['drug']
            record['drug'] = aliases[record['drug']]
    assert set(r['drug'] for r in records) == functional, {'chemical_only': sorted(set(r['drug'] for r in records) - functional), 'functional_only': sorted(functional - set(r['drug'] for r in records))}
    assert len(records) == len(functional) == 144
    groups = {}
    for r in records:
        groups.setdefault(r['group'], []).append(r['drug'])
    exposed = next(r['group'] for r in records if r['drug'] == '(+)-JQ-1')
    forced = [exposed] + (['UNKNOWN_STRUCTURE'] if 'UNKNOWN_STRUCTURE' in groups else [])
    allocation = {name: [] for name in ('development', 'selection', 'later')}
    ordered = sorted(groups, key=lambda g: hashlib.sha256(('MAESTRO-decryptE-20261022-v1|' + g).encode()).hexdigest())
    ordered = forced + [g for g in ordered if g not in forced]
    group_allocation = {}
    for group in ordered:
        split = 'development' if group in forced else min(allocation, key=lambda k: (len(allocation[k]), list(allocation).index(k)))
        allocation[split].extend(sorted(groups[group]))
        group_allocation[group] = split
    result = {'source_sha256': sha, 'rdkit': rdBase.rdkitVersion,
              'algorithm': 'Largest fragment Murcko scaffold (no chirality), acyclic parent fallback; salted SHA256 group order; exposed JQ1 and missing-structure groups forced development; greedy least-populated split with development/selection/later tie order',
              'groups': groups, 'group_allocation': group_allocation, 'explicit_identity_aliases': aliases,
              'partitions': {k: sorted(v) for k, v in allocation.items()}, 'chemical_metadata': records,
              'response_values_read': False, 'exposure': ['(+)-JQ-1 qualitative Effect three endpoints already development-exposed', 'Published article was read; not a literature-blind evaluation']}
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'groups': len(groups), 'largest_group': max(map(len, groups.values())),
                      'partitions': {k: len(v) for k, v in allocation.items()},
                      'development_types': dict(Counter(r['type'] for r in records if r['drug'] in allocation['development']))}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
