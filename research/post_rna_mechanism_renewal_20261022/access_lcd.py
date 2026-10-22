"""Authenticate a close causal-world predecessor exposed by the original index."""
import json
from fetch_primary import fetch
if __name__=='__main__':
    print(json.dumps(fetch(('lcd_fulltext','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13663777/fullTextXML'))),flush=True)
