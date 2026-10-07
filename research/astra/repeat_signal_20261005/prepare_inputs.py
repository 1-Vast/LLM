"""Restore public inputs in a fresh checkout; refuse changed existing bytes."""
import hashlib,shutil,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rna=ROOT/'research/astra/knowledge_transfer_20261004/context/pathway_125_lines.csv'
    rna.parent.mkdir(parents=True,exist_ok=True)
    src=HERE/'inputs/pathway_125_lines.csv'
    if rna.exists():assert sha(rna)==sha(src)
    else:shutil.copyfile(src,rna)
    source=ROOT/'research/astra/knowledge_transfer_20261004/assets/jaaks.csv'
    expected='1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278'
    if not source.exists():
        source.parent.mkdir(parents=True,exist_ok=True);temp=source.with_suffix('.download')
        with urllib.request.urlopen('https://ndownloader.figshare.com/files/34006655',timeout=60) as r,temp.open('wb') as f:
            shutil.copyfileobj(r,f,1024*1024)
        assert sha(temp)==expected;temp.rename(source)
    assert sha(source)==expected
    print('Public Jaaks and pinned RNA inputs match expected digests.')
if __name__=='__main__':main()
