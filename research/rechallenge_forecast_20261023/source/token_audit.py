"""Exact XML prefix-token audit; separate from numerical forecast reconstruction."""
from pathlib import Path
import xml.etree.ElementTree as X
import zipfile
import json

ROOT = Path(__file__).resolve().parents[3]
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

if __name__ == '__main__':
    result = {}
    for n in (3, 4):
        with zipfile.ZipFile(ROOT / f'log/20261023/rechallenge_task/root/transition_exp{n}.body') as z:
            rs = {x.get('Id'): x.get('Target') for x in X.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
            tokens = {}
            for s in X.fromstring(z.read('xl/workbook.xml')).find(NS+'sheets'):
                if s.get('name') not in ('AAAA', 'ANAN'):
                    continue
                t = rs[s.get(REL)]
                t = t.lstrip('/') if t.startswith('/') else 'xl/'+t
                tokens[s.get('name')] = [c.find(NS+'v').text
                                        for row in X.fromstring(z.read(t)).find(NS+'sheetData')
                                        for c in row if c.get('r') in ('B4', 'B5')]
            result[str(n)] = {'tokens': tokens, 'exact_token_equal': tokens['AAAA'] == tokens['ANAN']}
    p = ROOT / 'log/20261023/rechallenge_forecast/source/PREFIX_TOKEN_AUDIT.json'
    assert not p.exists()
    p.write_text(json.dumps(result, indent=2), encoding='utf-8')
