"""Post-evaluation ChEMBL enrichment for retrieval, never used in reported models.

Resolve only a unique exact preferred-name/synonym match. Keep protein families,
complexes and non-protein targets as such; components are not assumed to be all
bound by the drug. Curated mechanism assertions are not our own measured effects.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
import pandas as pd

HERE=Path(__file__).resolve().parent
BASE='https://www.ebi.ac.uk/chembl/api/data/'


def normalise(name):
    return re.sub(r'[^a-z0-9]','',str(name).lower())


def retrieve(name):
    url=BASE+name
    with urllib.request.urlopen(url,timeout=30) as response:
        raw=response.read()
    return json.loads(raw),dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))


def fetch(row):
    out=dict(drug_id=row.drug_id,name=row.name,original_target=row.target,
             status='unresolved',used_in_model=False,source_requests=[])
    try:
        query='molecule/search.json?'+urllib.parse.urlencode(dict(q=row.name,limit=30))
        search,receipt=retrieve(query);out['source_requests'].append(receipt)
        candidates=[]
        key=normalise(row.name)
        for molecule in search.get('molecules',[]):
            names=[molecule.get('pref_name') or '']
            for syn in molecule.get('molecule_synonyms',[]):
                names.extend([syn.get('molecule_synonym',''),syn.get('synonyms','')])
            if key in {normalise(n) for n in names}:
                candidates.append(molecule)
        out['exact_candidate_ids']=[m['molecule_chembl_id'] for m in candidates]
        if len(candidates)!=1:
            out['reason']='not exactly one preferred-name/synonym identity match'
            return out
        molecule=candidates[0];mid=molecule['molecule_chembl_id']
        out['molecule']=molecule
        mechanisms,receipt=retrieve('mechanism.json?'+urllib.parse.urlencode(dict(molecule_chembl_id=mid,limit=100)))
        out['source_requests'].append(receipt)
        out['mechanisms']=mechanisms.get('mechanisms',[])
        out['targets']={}
        for tid in sorted({m['target_chembl_id'] for m in out['mechanisms'] if m.get('target_chembl_id')}):
            target,receipt=retrieve(f'target/{tid}.json')
            out['targets'][tid]=target;out['source_requests'].append(receipt)
        out['status']='curated_mechanism_retrieved' if out['mechanisms'] else 'identity_resolved_no_mechanism'
        out['limitations']=['Name-level mapping; benchmark vial structure was not provided',
          'Target components are entity metadata, not a claim that each is bound',
          'No benchmark-matched dose, time, target engagement or cell-specific response',
          'This enrichment was obtained after evaluation; it was not used by any reported model']
    except Exception as error:
        out['status']='retrieval_failed';out['error']=str(error)
    return out


def main():
    HERE.mkdir(exist_ok=True)
    drugs=pd.read_csv(HERE.parent/'knowledge/drugs.tsv',sep='\t',dtype=str,keep_default_na=False)
    rows=list(drugs[drugs.mapped_genes==''].itertuples(index=False))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(fetch,rows))
    (HERE/'chembl_actions.json').write_text(json.dumps(results,indent=2)+'\n')
    brief=[]
    for r in results:
        brief.append(dict(drug_id=r['drug_id'],name=r['name'],status=r['status'],
          molecule_id=r.get('molecule',{}).get('molecule_chembl_id'),
          mechanism_count=len(r.get('mechanisms',[])),
          targets=[dict(id=tid,name=t.get('pref_name'),type=t.get('target_type'),organism=t.get('organism'))
                   for tid,t in r.get('targets',{}).items()]))
    report=dict(retrieved_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      purpose='post-evaluation retrieval-only enrichment; zero use in model experiments',
      total=len(results),status_counts={s:sum(r['status']==s for r in results) for s in sorted({r['status'] for r in results})},
      drugs=brief,license='ChEMBL original terms and attribution retained; see source documentation')
    (HERE/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
