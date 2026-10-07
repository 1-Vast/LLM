"""Acquire a small pinned public mutation layer, never combination outcomes."""
import concurrent.futures,hashlib,json,sqlite3,urllib.request
import pandas as pd
from .analyze import HERE,dump,sha256


def run():
    folder=HERE/'next_sources';meta=json.loads((folder/'depmap24q4_metadata.json').read_text())
    files={f['name']:f for f in meta['files']}
    def fetch(name):
        f=files[name];p=folder/name
        with urllib.request.urlopen(f['download_url'],timeout=60) as response:p.write_bytes(response.read())
        assert p.stat().st_size==f['size']
        assert hashlib.md5(p.read_bytes()).hexdigest()==f['computed_md5']
        return {'name':name,'url':f['download_url'],'bytes':p.stat().st_size,'sha256':sha256(p),'md5':f['computed_md5']}
    names=['Model.csv','OmicsSomaticMutationsMatrixHotspot.csv']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:receipts=list(ex.map(fetch,names))
    model=pd.read_csv(folder/'Model.csv',low_memory=False)
    print('MODEL_COLUMNS',list(model.columns))
    if 'SangerModelID' not in model:raise ValueError('No explicit Sanger model ID; require reviewed identity mapping')
    context=pd.read_csv(HERE/'inputs/pathway_125_lines.csv',index_col=0)
    mapping=model[model.SangerModelID.isin(context.index)].copy()
    if mapping.SangerModelID.duplicated().any():raise ValueError('Ambiguous exact SIDM mapping')
    matrix=pd.read_csv(folder/'OmicsSomaticMutationsMatrixHotspot.csv',index_col=0)
    mapping=mapping[mapping.ModelID.isin(matrix.index)]
    sub=matrix.loc[mapping.ModelID].copy();sub.index=mapping.SangerModelID.to_numpy();sub.index.name='SIDM'
    sub.to_csv(HERE/'inputs/hotspot_mapped.csv.gz',compression={'method':'gzip','mtime':0})
    mapping[['SangerModelID','ModelID','CellLineName']].to_csv(HERE/'inputs/depmap_identity_map.csv',index=False)
    long=sub.reset_index().melt(id_vars='SIDM',var_name='gene_identifier',value_name='hotspot')
    long['evidence_kind']='DepMap processed hotspot mutation call; absence and missingness distinct'
    long['source_release']='DepMap 24Q4 v1';long['use_status']='acquired_after_RNA_test_not_used_in_reported_models'
    db=sqlite3.connect(HERE/'feature_catalog.sqlite')
    long.to_sql('hotspot_mutation',db,index=False)
    mapping[['SangerModelID','ModelID','CellLineName']].to_sql('depmap_identity',db,index=False)
    db.execute('CREATE UNIQUE INDEX hotspot_key ON hotspot_mutation(SIDM,gene_identifier)')
    db.execute('INSERT INTO policy VALUES(?)',('Hotspot data were acquired after reported RNA evaluation and have not been tested for biological or action gain.',))
    db.commit();db.close()
    receipt={'source_doi':'10.25452/figshare.plus.27993248.v1','license':meta['license'],'downloads':receipts,'matrix_shape':list(matrix.shape),'exact_sidm_mapped_cells':len(sub),'missing_125_cells':sorted(set(context.index)-set(sub.index)),'genes':len(sub.columns),'missing_feature_values':int(sub.isna().sum().sum()),'positive_calls':int((sub==1).sum().sum()),'not_used_in_reported_models':True}
    dump(folder/'mutation_acquisition.json',receipt)
    manifest=json.loads((HERE/'evidence_catalog_manifest.json').read_text());manifest['feature_db_sha256']=sha256(HERE/'feature_catalog.sqlite');manifest['mutation_layer']=receipt
    dump(HERE/'evidence_catalog_manifest.json',manifest)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['downloads','license']}))

if __name__=='__main__':run()
