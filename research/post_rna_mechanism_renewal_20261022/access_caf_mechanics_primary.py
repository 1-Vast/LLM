"""Follow author JATS and dataset registries; no guessed dataset identifiers."""
import json
from concurrent.futures import ThreadPoolExecutor
from fetch_primary import fetch
SOURCES={
 'caf_mechanics_author_jats':'https://www.biorxiv.org/content/early/2026/09/22/2026.09.19.752881.source.xml',
 'caf_mechanics_datacite_title_search':'https://api.datacite.org/dois?query=%22CAF%20contractility%22&page%5Bsize%5D=10',
 'caf_mechanics_datacite_author_topic_search':'https://api.datacite.org/dois?query=creators.name%3AEmon%20AND%20titles.title%3Acollagen&page%5Bsize%5D=10'}
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)
