"""Two targeted original-index queries; the shared helper owns receipts."""
from pathlib import Path
import importlib.util
import json
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('bounded_fetch', HERE.parent/'fetch_source.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
queries = {
    'recent_global_epistasis.json': 'TITLE_ABS:("global epistasis") AND FIRST_PDATE:[2025-01-01 TO 2026-10-31]',
    'conditional_gi_prediction.json': 'TITLE_ABS:(("genetic interaction" OR "genetic interactions") AND (environment OR environmental) AND (predict OR prediction OR transfer)) AND FIRST_PDATE:[2025-01-01 TO 2026-10-31]',
}
for name, query in queries.items():
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode({'query': query, 'format': 'json', 'pageSize': 25})
    module.fetch(url, name, 'root', 2*1024*1024)
    path = HERE/'sources'/name
    if path.exists():
        result = json.loads(path.read_text(encoding='utf-8'))
        print(json.dumps({'query': query, 'hitCount': result.get('hitCount'),
                          'records': [{k: row.get(k) for k in ('title','doi','pmcid','id','firstPublicationDate')}
                                      for row in result.get('resultList',{}).get('result',[])]}, ensure_ascii=False))
