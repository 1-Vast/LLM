"""Follow explicit primary links and use repository index discovery, not guessed assets."""
from concurrent.futures import ThreadPoolExecutor
import json
from fetch_primary import fetch

SOURCES={
 'labcompass_author_jats':'https://www.biorxiv.org/content/early/2026/10/09/2026.10.07.756550.source.xml',
 'resolution_author_jats':'https://www.biorxiv.org/content/early/2026/10/01/2026.09.30.755756.source.xml',
 'labcompass_repository_search':'https://api.github.com/search/repositories?q=LabCompass&per_page=10',
 'resolution_repository_search':'https://api.github.com/search/repositories?q=%22recoverable+resolution%22&per_page=10',
 'labcompass_europepmc_full':'https://www.ebi.ac.uk/europepmc/webservices/rest/PPR1338161/fullTextXML'}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)
