"""Independently audit saved chemistry responses; no network or outcome access."""
from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/api_evidence_innovation'
DATA = LOG/'data'
CHEM = LOG/'chemical_proxy'
MENU = ROOT/'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(groups):
    return sorted(sorted(group) for group in groups)


def bfs_components(rows, scaffold):
    adjacency = {row['compound_label']: set() for row in rows}
    for left_pos, left in enumerate(rows):
        for right in rows[left_pos+1:]:
            edge = left['neutral_parent'] == right['neutral_parent']
            if scaffold:
                edge |= bool(left['scaffold']) and left['scaffold'] == right['scaffold']
            if edge:
                adjacency[left['compound_label']].add(right['compound_label'])
                adjacency[right['compound_label']].add(left['compound_label'])
    remaining, groups = set(adjacency), []
    while remaining:
        queue, group = deque([min(remaining)]), set()
        while queue:
            node = queue.popleft()
            if node in group:
                continue
            group.add(node)
            queue.extend(adjacency[node] - group)
        remaining -= group
        groups.append(group)
    return normalize(groups)


def main():
    out = DATA/'CHEMICAL_PROXY_AUDIT.json'
    assert not out.exists()
    protocol = DATA/'CHEMICAL_PROXY_AUDIT_PROTOCOL.md'
    all_files = [MENU, protocol, Path(__file__), CHEM/'RESULT.json', CHEM/'STARTED.json']
    all_files += sorted(CHEM.glob('request_*.json')) + sorted(CHEM.glob('request_*.body'))
    inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in all_files}
    with (DATA/'CHEMICAL_PROXY_AUDIT_PRE_EXECUTION.json').open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'sha256': inputs}, stream, indent=2)
        stream.write('\n')
    failures, checks = [], 0

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    menu = json.loads(MENU.read_bytes())['results']['both']['accepted_identity_only']
    result = json.loads((CHEM/'RESULT.json').read_bytes())
    started = json.loads((CHEM/'STARTED.json').read_bytes())
    check(started['source_sha256'] == sha(MENU), 'source_binding')
    check(len(menu) == len(result['rows']) == 47, '47labels')
    check(len(list(CHEM.glob('request_*.json'))) == 47, '47receipts')
    check(len(list(CHEM.glob('request_*.body'))) == 47, '47bodies')
    statuses, errors, bytes_total = Counter(), [], 0
    records = {}
    for index, identity in enumerate(menu):
        receipt_path = CHEM/f'request_{index:02}.json'
        body_path = CHEM/f'request_{index:02}.body'
        receipt, body = json.loads(receipt_path.read_bytes()), body_path.read_bytes()
        check(receipt['name'] == identity['compound_label'], f'{index}:name')
        check(receipt['logical_request'] == 1, f'{index}:logicalrequest')
        check(receipt['bytes'] == len(body), f'{index}:bytes')
        check(receipt['sha256'] == sha(body_path), f'{index}:sha')
        check('/name/'+identity['compound_label']+'/property/' in unquote(receipt['url']), f'{index}:exactnameURL')
        statuses[str(receipt['status'])] += 1
        bytes_total += len(body)
        if 'error_type' in receipt:
            errors.append({'compound_label': receipt['name'], 'error_type': receipt['error_type'],
                           'http_status': receipt['status'], 'body_retained': True})
        if receipt['status'] == 200:
            records[identity['compound_label']] = json.loads(body)['PropertyTable']['Properties']
    check(dict(statuses) == {'200': 46, '404': 1}, 'httpstatuses')
    check(result['requests'].get('200') == 46 and result['requests'].get('404') == 1, 'rootHTTPcounts')
    check(len(errors) == result['requests'].get('EXCEPTION') == 1, 'postprocess_exception_count')
    check(len(errors) == 1 and errors[0]['compound_label'] == 'adapin', 'adapin_error')
    resolved = [row for row in result['rows'] if row['resolution'] == 'NAME_RESOLVED_PROXY_ONLY']
    unresolved = [row for row in result['rows'] if row['resolution'] != 'NAME_RESOLVED_PROXY_ONLY']
    check(len(resolved) == result['resolved_proxies'] == 45, '45resolved')
    check({row['compound_label'] for row in unresolved} == {'adapin', 'naphthyl isothiocyanate'}, 'unresolved_names')
    acyclic = []
    regenerated = []
    for row in resolved:
        name = row['compound_label']
        props = records[name]
        check(len(props) == 1, name+':oneproperty')
        record = props[0]
        smiles = record.get('ConnectivitySMILES') or record.get('CanonicalSMILES')
        mol = Chem.MolFromSmiles(smiles)
        check(mol is not None, name+':parse')
        parent = rdMolStandardize.Uncharger().uncharge(rdMolStandardize.FragmentParent(mol))
        parent_smiles = Chem.MolToSmiles(parent, isomericSmiles=False)
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=parent, includeChirality=False)
        expected_key = scaffold if scaffold else 'acyclic:'+parent_smiles
        for field, value in [('CID', record['CID']), ('pubchem_inchikey', record.get('InChIKey')),
                             ('formula', record.get('MolecularFormula')), ('connectivity_smiles', smiles),
                             ('neutral_parent', parent_smiles), ('scaffold', scaffold),
                             ('scaffold_key', expected_key), ('fragment_count', len(Chem.GetMolFrags(mol))),
                             ('parent_differs', Chem.MolToSmiles(mol, isomericSmiles=False) != parent_smiles)]:
            check(row[field] == value, name+':'+field)
        regenerated.append({'compound_label': name, 'neutral_parent': parent_smiles, 'scaffold': scaffold})
        if not scaffold:
            acyclic.append({'compound_label': name, 'parent_specific_key': expected_key})
    parent_groups = bfs_components(regenerated, False)
    scaffold_groups = bfs_components(regenerated, True)
    check(parent_groups == normalize(result['parent_components']), 'parentpartition_BFS')
    check(scaffold_groups == normalize(result['parent_scaffold_components']), 'parentscaffoldpartition_BFS')
    check(len(parent_groups) == 45, '45parentgroups')
    check(len(scaffold_groups) == 39, '39scaffoldgroups')
    check(len({row['parent_specific_key'] for row in acyclic}) == len(acyclic), 'acyclicnotmerged')
    check(result['true_source_material_identity_authenticated'] is False, 'material_not_authenticated')
    check(result['future_biological_outcomes_opened'] is False and result['new_fits'] == 0, 'no_outcomeclaim')
    check(rdBase.rdkitVersion == result['rdkit_version'], 'rdkit_version')
    report = {'status': 'PASS_INTERNAL_PROXY_AUDIT' if not failures else 'FAIL',
              'checks': checks, 'failures': failures, 'http_request_receipts': 47,
              'http_statuses': dict(statuses), 'http_body_bytes': bytes_total,
              'postprocessing_errors_not_extra_HTTP': errors, 'resolved_proxies': len(resolved),
              'parent_components': len(parent_groups), 'parent_scaffold_components': len(scaffold_groups),
              'acyclic_parent_specific_keys': acyclic, 'rdkit_version': rdBase.rdkitVersion,
              'input_sha256': inputs, 'new_HTTP': 0, 'new_fits': 0,
              'source_material_identity_authenticated': False,
              'limits': ['Checks internal integrity of name-resolved proxy structures only',
                         'No actual source salt/stereochemistry/material/donor identity proved',
                         'Root records retained unchanged; unresolved labels not rescued']}
    with out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('input_sha256', 'acyclic_parent_specific_keys')}, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == '__main__':
    raise SystemExit(main())
