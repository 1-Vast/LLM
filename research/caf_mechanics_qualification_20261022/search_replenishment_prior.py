"""Retrieve precise primary-index predecessors for the proposed activity term."""
from urllib.parse import urlencode
from fetch_sources import parallel
if __name__=='__main__':
    queries={
      'activity_replenishment_primary':'TITLE:"Activity-dependent modulation of the rate at which synaptic vesicles become available to undergo exocytosis"',
      'calmodulin_recruitment_primary':'TITLE:"Calmodulin mediates rapid recruitment of fast-releasing synaptic vesicles at a calyx-type synapse"',
      'tension_replenishment_primary':'TITLE_ABS:tension AND (TITLE_ABS:"vesicle replenishment" OR TITLE_ABS:"vesicle recruitment")'}
    parallel({name:'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':q,'format':'json','resultType':'core','pageSize':10}) for name,q in queries.items()})
