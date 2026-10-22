"""Inspect author code-tree and GEO metadata only, not response matrices."""
import json
import xml.etree.ElementTree as ET

from lineage_followup import OUT, get


if __name__ == '__main__':
    response = get('watermelon_repo_tree', 'https://api.github.com/repos/yaaraore/watermelon/git/trees/HEAD', {'recursive': 1})
    if response.status_code == 200:
        payload = response.json()
        rows = [{key: row.get(key) for key in ('path', 'type', 'sha', 'size', 'url')} for row in payload['tree']]
        (OUT / 'watermelon_repo_tree.json').write_text(json.dumps({'sha': payload['sha'], 'truncated': payload['truncated'], 'tree': rows}, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'tree_sha': payload['sha'], 'truncated': payload['truncated'], 'files': rows}, ensure_ascii=False))
    else:
        print(json.dumps({'repo_status': response.status_code}))
    response = get('GSE150949_metadata', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi',
                   {'acc': 'GSE150949', 'targ': 'self', 'form': 'xml', 'view': 'quick'})
    if response.status_code == 200:
        tree = ET.fromstring(response.content)
        rows = []
        for node in tree.iter():
            tag = node.tag.split('}')[-1]
            if tag in ('Title', 'Summary', 'Overall-Design', 'Supplementary-Data', 'Sample-Ref', 'Relation', 'Accession'):
                rows.append({'tag': tag, 'text': node.text, 'attributes': node.attrib})
        (OUT / 'GSE150949_metadata.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(rows, ensure_ascii=False))
    else:
        print(json.dumps({'geo_status': response.status_code}))
