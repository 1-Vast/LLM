"""Follow actual author publications and a distinct authenticated data-deposit lead."""
from urllib.parse import urlencode
from fetch_sources import parallel

if __name__=='__main__':
    parallel({
      'saif_recent_publications':'https://saif.mechse.illinois.edu/recent-publications/',
      'neuron_zenodo_record':'https://zenodo.org/api/records/8385319',
      'neuron_primary_index':'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':'TITLE:"Synapses without Tension Fail to Fire"','format':'json','resultType':'core','pageSize':25})})
