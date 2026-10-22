from cipa_assets import get
import json

if __name__=='__main__':
    response=get('cipa_supplement_europepmc','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6226030/supplementaryFiles')
    print(json.dumps({'zip_signature':response.content.startswith(b'PK'),'prefix':response.content[:80].decode('ascii','replace') if not response.content.startswith(b'PK') else 'ZIP'}))
