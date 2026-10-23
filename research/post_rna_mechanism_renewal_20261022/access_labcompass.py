"""Inspect discovered author-organization repository without executing its code."""
import json
from concurrent.futures import ThreadPoolExecutor
from fetch_primary import fetch
SOURCES={
 'labcompass_readme':'https://raw.githubusercontent.com/theislab/LabCompass/main/README.md',
 'labcompass_tree':'https://api.github.com/repos/theislab/LabCompass/git/trees/main?recursive=1',
 'labcompass_repo_metadata':'https://api.github.com/repos/theislab/LabCompass'}
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)
