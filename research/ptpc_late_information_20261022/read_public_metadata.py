"""Summarize exact-DOI public full-text locations without opening tables."""
from pathlib import Path
import json

root=Path('D:/MAESTRO/log/20261022/ptpc_late_information/source')
crossref=json.loads((root/'crossref_exact_doi.body').read_text(encoding='utf-8'))['message']
openalex=json.loads((root/'openalex_exact_doi.body').read_text(encoding='utf-8'))
assert crossref['DOI'].lower() == '10.1038/s41586-026-11001-9'
assert openalex['doi'].lower() == 'https://doi.org/10.1038/s41586-026-11001-9'
result=dict(crossref_title=crossref['title'], crossref_links=crossref.get('link'), crossref_relation=crossref.get('relation'),
            openalex_title=openalex['title'], openalex_open_access=openalex['open_access'],
            openalex_best_oa_location=openalex.get('best_oa_location'),
            openalex_locations=[{key:loc.get(key) for key in ('is_oa','landing_page_url','pdf_url','license','version','is_accepted','is_published')} for loc in openalex['locations']])
target=root/'PUBLIC_FULLTEXT_LOCATIONS.json'
assert not target.exists()
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
