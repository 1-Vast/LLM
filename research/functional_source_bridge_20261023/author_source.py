"""Read named author source at pinned commit; never execute downloaded code."""
from io import BytesIO
import json
from zipfile import ZipFile
from metadata import OUT, fetch

COMMIT='ccb9ee5c37fb5a117cd76d8e9a5a5217ce12338d'

if __name__=='__main__':
    # Explicit named expression/functional objects found in data_utils authorize
    # this one source-only extension after the six initial metadata requests.
    _,r=fetch('author_source.zip',f'https://codeload.github.com/broadinstitute/perturb-seq-depmap-public/zip/{COMMIT}')
    assert r.status_code==200
    excerpts=[]
    with ZipFile(BytesIO(r.content)) as z:
        inventory=[dict(path=x.filename,bytes=x.file_size) for x in z.infolist()]
        for member in z.namelist():
            if not member.endswith(('.py','.R','.md','.gitmodules')):
                continue
            source=z.read(member).decode('utf-8',errors='replace')
            lines=source.splitlines()
            hits=[i for i,l in enumerate(lines) if any(t in l.lower() for t in [
                'figshare','https://','dependency','geneeffect','chronos','crispr_table','taiga'])]
            if hits:
                excerpts.append(dict(path=member,lines=[dict(line=i+1,text=lines[i]) for i in hits]))
    (OUT/'AUTHOR_INVENTORY.json').write_text(json.dumps(dict(commit=COMMIT,inventory=inventory),indent=2),encoding='utf-8')
    (OUT/'AUTHOR_EXCERPTS.json').write_text(json.dumps(excerpts,indent=2),encoding='utf-8')
    print(json.dumps(dict(commit=COMMIT,members=len(inventory),source_files_with_hits=len(excerpts))))
