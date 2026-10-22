"""Qualify an actual pharmacological-history lead exposed by targeted search."""
import json
from concurrent.futures import ThreadPoolExecutor
from fetch_primary import fetch
SOURCES={
 'caf_mechanics_author_metadata':'https://api.biorxiv.org/details/biorxiv/10.64898/2026.09.19.752881',
 'caf_mechanics_repository_search':'https://api.github.com/search/repositories?q=%22752881%22+in%3Areadme&per_page=10',
 'caf_mechanics_title_repository_search':'https://api.github.com/search/repositories?q=%22CAF%22+%22collagen%22+%22stiffness%22+in%3Areadme&per_page=10'}
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)
