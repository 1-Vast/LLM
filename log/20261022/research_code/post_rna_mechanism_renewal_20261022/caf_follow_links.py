"""Follow PMC/EuropePMC supplement routes and targeted primary-index history search."""
from concurrent.futures import ThreadPoolExecutor
import json
from fetch_primary import fetch
from search_primary import search
SOURCES={
 'caf_current_pmc_oa_locator':'https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC13680625',
 'caf_europepmc_supplement_methods':'https://europepmc.org/articles/PMC13680625/bin/41392_2026_2965_MOESM1_ESM.docx',
 'caf_europepmc_supplement_samples':'https://europepmc.org/articles/PMC13680625/bin/41392_2026_2965_MOESM2_ESM.xlsx'}
QUERIES={
 'caf_history_primary':'("cancer-associated fibroblast" OR "cancer associated fibroblasts") AND (memory OR sequential OR washout OR hysteresis) AND FIRST_PDATE:[2000-01-01 TO 2026-10-22]',
 'fibroblast_hysteresis_primary':'fibroblast AND (hysteresis OR "signaling memory" OR "cytokine memory") AND ("TGF" OR cytokine OR "interferon") AND FIRST_PDATE:[2000-01-01 TO 2026-10-22]'}
if __name__=='__main__':
    jobs=[(fetch,x) for x in SOURCES.items()]+[(search,x) for x in QUERIES.items()]
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(lambda pair:pair[0](pair[1]),jobs):print(json.dumps(result),flush=True)
