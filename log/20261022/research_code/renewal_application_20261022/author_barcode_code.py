"""Retrieve the already-authenticated author barcode-processing source blob."""
import base64
import json

from lineage_followup import OUT, get


if __name__ == '__main__':
    tree = json.loads((OUT / 'watermelon_repo_tree.json').read_text(encoding='utf-8'))
    row = next(x for x in tree['tree'] if x['path'] == 'code/10X_WTA_dialOut.Rmd')
    response = get('watermelon_barcode_code_blob', row['url'])
    response.raise_for_status()
    body = base64.b64decode(response.json()['content'])
    (OUT / 'watermelon_10X_WTA_dialOut.Rmd').write_bytes(body)
    print(json.dumps({'path': row['path'], 'blob_sha': row['sha'], 'decoded_bytes': len(body)}))
