"""Primary PubChem name/structure proxy audit; never read biological outcomes."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import quote

import requests
from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/api_evidence_innovation'
OUT = LOG / 'chemical_proxy'
SOURCE = ROOT / 'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def components(rows, fields):
    parents = {row['compound_label']: row['compound_label'] for row in rows}
    def find(key):
        while parents[key] != key:
            key = parents[key]
        return key
    buckets = defaultdict(list)
    for row in rows:
        for field in fields:
            buckets[(field, row[field])].append(row['compound_label'])
    for members in buckets.values():
        for member in members[1:]:
            left, right = find(members[0]), find(member)
            parents[max(left, right)] = min(left, right)
    groups = defaultdict(list)
    for label in parents:
        groups[find(label)].append(label)
    return sorted((sorted(values) for values in groups.values()), key=lambda group: (-len(group), group))


def main():
    OUT.mkdir(exist_ok=True)
    write(OUT / 'STARTED.json', {'utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': digest(SOURCE),
          'protocol_sha256': digest(LOG / 'CHEMICAL_PROXY_PROTOCOL.md'), 'script_sha256': digest(Path(__file__)),
          'rdkit_version': rdBase.rdkitVersion, 'future_biological_outcomes_opened': False})
    names = json.loads(SOURCE.read_text(encoding='utf-8'))['results']['both']['accepted_identity_only']
    assert len(names) == 47 and len({row['compound_label'] for row in names}) == 47
    rows, statuses = [], Counter()
    for number, identity in enumerate(names):
        name = identity['compound_label']
        url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/' + quote(name, safe='') + '/property/CanonicalSMILES,InChIKey,MolecularFormula/JSON'
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url, 'logical_request': 1, 'name': name}
        row = {'compound_label': name, 'experiment': identity['experiment'], 'resolution': 'UNRESOLVED'}
        try:
            response = requests.get(url, timeout=25)
            body = OUT / ('request_' + str(number).zfill(2) + '.body')
            with body.open('xb') as stream:
                stream.write(response.content)
            receipt.update(status=response.status_code, bytes=len(response.content), sha256=digest(body), final_url=response.url)
            statuses[str(response.status_code)] += 1
            if response.status_code == 200:
                properties = response.json().get('PropertyTable', {}).get('Properties', [])
                if len(properties) == 1:
                    record = properties[0]
                    smiles = record.get('ConnectivitySMILES') or record.get('CanonicalSMILES')
                    mol = Chem.MolFromSmiles(smiles) if smiles else None
                    if mol is not None and any(atom.GetAtomicNum() == 6 for atom in mol.GetAtoms()):
                        parent = rdMolStandardize.Uncharger().uncharge(rdMolStandardize.FragmentParent(mol))
                        parent_smiles = Chem.MolToSmiles(parent, isomericSmiles=False)
                        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=parent, includeChirality=False)
                        row.update(resolution='NAME_RESOLVED_PROXY_ONLY', CID=record['CID'],
                                   pubchem_inchikey=record.get('InChIKey'), formula=record.get('MolecularFormula'),
                                   released_name=name, connectivity_smiles=smiles, neutral_parent=parent_smiles,
                                   scaffold=scaffold, scaffold_key=scaffold or 'acyclic:' + parent_smiles,
                                   fragment_count=len(Chem.GetMolFrags(mol)),
                                   parent_differs=Chem.MolToSmiles(mol, isomericSmiles=False) != parent_smiles)
                    else:
                        row['reason'] = 'structure_unparseable_or_noncarbon'
                else:
                    row.update(reason='not_exactly_one_property_record', returned_records=len(properties))
            else:
                row['reason'] = 'HTTP_' + str(response.status_code)
        except Exception as exc:
            receipt.update(error_type=type(exc).__name__)
            statuses['EXCEPTION'] += 1
            row['reason'] = type(exc).__name__
        write(OUT / ('request_' + str(number).zfill(2) + '.json'), receipt)
        rows.append(row)
        print(json.dumps({'completed': number + 1, 'of': 47, 'name': name, 'resolution': row['resolution']}), flush=True)
        time.sleep(0.5)
    resolved = [row for row in rows if row['resolution'] == 'NAME_RESOLVED_PROXY_ONLY']
    result = {'status': 'EXPLORATORY_NAME_STRUCTURE_PROXY', 'input_labels': 47,
              'resolved_proxies': len(resolved), 'unresolved_labels': 47 - len(resolved),
              'requests': dict(statuses), 'rows': rows,
              'parent_components': components(resolved, ('neutral_parent',)),
              'parent_scaffold_components': components(resolved, ('neutral_parent', 'scaffold_key')),
              'rdkit_version': rdBase.rdkitVersion, 'true_source_material_identity_authenticated': False,
              'future_biological_outcomes_opened': False, 'new_fits': 0}
    write(OUT / 'RESULT.json', result)
    print(json.dumps({key: value for key, value in result.items() if key not in ('rows', 'parent_components', 'parent_scaffold_components')}
                     | {'parent_groups': len(result['parent_components']), 'scaffold_linked_groups': len(result['parent_scaffold_components'])}), flush=True)


if __name__ == '__main__':
    main()
