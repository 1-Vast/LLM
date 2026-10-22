"""Use official REST supplement bundle and title/abstract-restricted queries."""
from concurrent.futures import ThreadPoolExecutor
import json
from fetch_primary import fetch
from search_primary import search
QUERIES={
 'caf_history_title_abstract':'(TITLE_ABS:"cancer-associated fibroblast" OR TITLE_ABS:"cancer associated fibroblasts") AND (TITLE_ABS:memory OR TITLE_ABS:hysteresis OR TITLE_ABS:washout OR TITLE_ABS:sequential) AND FIRST_PDATE:[2000-01-01 TO 2026-10-22]',
 'fibroblast_hysteresis_title_abstract':'TITLE_ABS:fibroblast AND (TITLE_ABS:hysteresis OR TITLE_ABS:"signaling memory" OR TITLE_ABS:"cytokine memory") AND FIRST_PDATE:[2000-01-01 TO 2026-10-22]',
 'fibroblast_ifn_history_title_abstract':'TITLE_ABS:fibroblast AND TITLE_ABS:interferon AND (TITLE_ABS:pretreatment OR TITLE_ABS:washout OR TITLE_ABS:memory) AND FIRST_PDATE:[2000-01-01 TO 2026-10-22]'}
if __name__=='__main__':
    jobs=[(fetch,('caf_rest_supplementary_bundle','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13680625/supplementaryFiles'))]+[(search,x) for x in QUERIES.items()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda pair:pair[0](pair[1]),jobs):print(json.dumps(result),flush=True)
