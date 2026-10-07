"""Download the exact public footprint snapshot; produce SIDM-aligned matrices."""
from __future__ import annotations
import concurrent.futures
import json
from pathlib import Path
import time
import urllib.request

import pandas as pd
from ..acquire import digest

HERE = Path(__file__).resolve().parent
COMMIT = '0dd01090977b9171d54dee284007a320e1ca6b38'
FILES = {
 'readme.md': '80c090d5b5f1660fa15233c024d331f3b0c3acfb6b54b30e0af30346eaec67cc',
 'scripts/GDSC_footprint.R': 'b4567e384fc498f5ad50447ec70eb80bf910056f2991b7672ce03a13bdf64b47',
 'results/GDSC_progeny_activities.csv': '59f72f89a5f242e4303f943f7cd1c18be7982a47d4902bceb7f1339812f8860c',
 'results/GDSC_TF_activities.csv': 'b5c77bbe1c79605b74ab3051625ee11b5eb37268511d6a7242bcb34218cec272',
 'support/rnaseq_tpm_20220624_header': 'd6cdd664d2afc9b10c10db1736899363644bec580fc988017a8a55524513836d',
 'LICENSE': '230184f60bae2feaf244f10a8bac053c8ff33a183bcc365b4d8b876d2b7f4809',
}


def main():
    raw = HERE / 'raw'
    raw.mkdir(exist_ok=True)
    def fetch(item):
        name, expected = item
        path = raw / name.split('/')[-1]
        url = f'https://raw.githubusercontent.com/saezlab/GDSC_footprints/{COMMIT}/{name}'
        # Verify the immutable URL, even if an initial main-branch copy is cached.
        with urllib.request.urlopen(url, timeout=45) as response:
            content = response.read()
        temporary = path.with_suffix(path.suffix+'.part')
        temporary.write_bytes(content)
        if digest(temporary) != expected:
            temporary.unlink()
            raise ValueError(f'upstream snapshot mismatch: {name}')
        temporary.replace(path)
        return dict(path=name, local=str(path.relative_to(HERE)), url=url,
                    bytes=path.stat().st_size, sha256=expected,
                    retrieved_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(fetch, FILES.items()))
    (HERE/'pinned_sources.json').write_text(json.dumps(rows,indent=2)+'\n')
    split = json.loads((HERE.parents[1]/'confirmation_campaign_20261004/protocol/partition.json').read_text())['split']
    lines = sorted({x for t in split.values() for group in ('HD','E') for x in t[group]})
    out = {}
    for kind, filename in [('pathway','GDSC_progeny_activities.csv'),('tf','GDSC_TF_activities.csv')]:
        x = pd.read_csv(raw/filename,index_col=0).T
        if x.index.duplicated().any() or x.columns.duplicated().any():
            raise ValueError('duplicate line or footprint IDs')
        out[kind] = dict(rows=len(x), features=len(x.columns), overlap=len(set(lines)&set(x.index)),
                         missing_lines=sorted(set(lines)-set(x.index)),
                         missing_values=int(x.isna().sum().sum()))
        if out[kind]['missing_lines'] or out[kind]['missing_values']:
            raise ValueError('missing data require a separately documented handling decision')
        x.reindex(lines).to_csv(HERE/f'{kind}_125_lines.csv')
    (HERE/'coverage.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__ == '__main__':
    main()
