"""Qualify author-linked measured mechanics sources without joining their assays."""
from urllib.parse import urlencode
from fetch_sources import parallel

if __name__=='__main__':
    sources={'neuron_fulltext':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10756289/fullTextXML'}
    for name,doi in {
        'mechanics_2021_index':'10.1126/sciadv.abf2629',
        'mechanics_protocol_2025_index':'10.1038/s41596-024-01106-8',
        'caf_rna_2023_index':'10.1038/s41597-023-02233-9',
        'caf_yap_2024_index':'10.1016/j.actbio.2023.11.015'}.items():
        sources[name]='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':'DOI:"'+doi+'"','format':'json','resultType':'core','pageSize':5})
    parallel(sources)
