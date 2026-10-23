"""Follow newly discovered institutional and indexed full-text locations."""
from urllib.parse import urlencode
from fetch_sources import parallel

if __name__=='__main__':
    parallel({
      'openalex_indexed_pdf':'https://content.openalex.org/works/W7214340488.pdf',
      'openalex_indexed_grobid':'https://content.openalex.org/works/W7214340488.grobid-xml',
      'saif_author_lab':'https://saif.mechse.illinois.edu/',
      'datacite_emon_saif':'https://api.datacite.org/dois?'+urlencode({'query':'Emon AND Saif','page[size]':100}),
      'datacite_bashar_emon':'https://api.datacite.org/dois?'+urlencode({'query':'"Bashar Emon"','page[size]':100})})
