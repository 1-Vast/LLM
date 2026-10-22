"""Inspect annotation package source only; never read RNA samples."""
import tarfile
from pathlib import Path
p=Path('log/20261022/tggates_rna_feedback_pilot')
with tarfile.open(p/'r_dependencies/hgu133plus2cdf_2.18.0.tar.gz') as t:
    with (p/'CDF_PACKAGE_SOURCE_DIAGNOSIS.txt').open('x', encoding='utf-8') as out:
        for m in t.getmembers():
            out.write(f'{m.name}\t{m.size}\n')
            if m.isfile() and (m.name.endswith(('DESCRIPTION','NAMESPACE')) or '/R/' in m.name):
                out.write(t.extractfile(m).read().decode('utf-8')+'\n')
