"""Restore pinned public dependency inputs; verify original full-file hashes."""
import hashlib,json,os,urllib.request
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent

def run():
    dest=HERE/'assets/depmap_crispr.csv';dest.parent.mkdir(exist_ok=True)
    url='https://ndownloader.figshare.com/files/51064667'
    expected='3d8f3ec6dbf2db7ff834b79b508622ec0b226f3518003fe96ecf5a4fcf167e3b'
    h=hashlib.sha256();md5=hashlib.md5();size=0
    with urllib.request.urlopen(url,timeout=60) as response,dest.with_suffix('.part').open('wb') as stream:
        while chunk:=response.read(1024*1024):
            stream.write(chunk);h.update(chunk);md5.update(chunk);size+=len(chunk)
        stream.flush();os.fsync(stream.fileno())
    assert size==428678699 and h.hexdigest()==expected and md5.hexdigest()=='6edf7ade09b9b34199210b559d4745d3'
    dest.with_suffix('.part').rename(dest)
    context=pd.read_csv(HERE/'inputs/pathway_125_lines.csv',index_col=0)
    model=pd.read_csv(HERE/'next_sources/Model.csv',low_memory=False)
    mapping=model[model.SangerModelID.isin(context.index)]
    assert not mapping.SangerModelID.duplicated().any()
    genes=set(pd.read_csv(HERE/'inputs/drug_target_annotation.csv').gene.dropna())
    header=pd.read_csv(dest,nrows=0).columns.tolist();columns=[header[0]]+[c for c in header[1:] if c.split(' (')[0] in genes]
    matrix=pd.read_csv(dest,usecols=columns,index_col=0);matrix.columns=[c.split(' (')[0] for c in matrix.columns]
    mapping=mapping[mapping.ModelID.isin(matrix.index)]
    sub=matrix.loc[mapping.ModelID].copy();sub.index=mapping.SangerModelID.to_numpy();sub.index.name='SIDM'
    sub=sub.reindex(columns=sorted(sub.columns));sub.to_csv(HERE/'inputs/target_dependency.csv')
    receipt={'doi':'10.25452/figshare.plus.27993248.v1','url':url,'source_bytes':size,'source_sha256':h.hexdigest(),'source_md5':md5.hexdigest(),'mapped_cells':len(sub),'target_genes':len(sub.columns),'missing_cells':sorted(set(context.index)-set(sub.index)),'missing_target_genes':sorted(genes-set(sub.columns)),'derived_sha256':hashlib.sha256((HERE/'inputs/target_dependency.csv').read_bytes()).hexdigest(),'license':'CC BY 4.0','note':'Recovery; derived column order canonicalized, substantive data unchanged; CRISPR knockout is not pharmacologic inhibition.'}
    assert sub.shape==(94,61) and not sub.isna().any().any()
    (HERE/'next_sources/dependency_acquisition.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':run()
