"""Compare archive member identities and known identity-source bytes only."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
OLD = ROOT/'log/20261023/post_anchor_mechanism/root_sources'
tree = json.loads((OLD/'aml_tree.body').read_text(encoding='utf-8'))['tree']
pinned = {row['path'] for row in tree if row['type'] == 'blob'}
names = [('python_scripts/1_LineagePreprocessing.py', 'aml_join_1_LineagePreprocessing.body'),
         ('python_scripts/2_TagClustering.py', 'aml_join_2_TagClustering.body'),
         ('python_scripts/AML_lineage_utilities.py', 'aml_join_AML_lineage_utilities.body'),
         ('R_scripts/single_cell_GEX_initial_processing.R', 'aml_gex.body'),
         ('R_scripts/single_cell_lineage_analysis.R', 'aml_lineage.body')]
with zipfile.ZipFile(OUT/'author_archive.body') as archive:
    members = {name.split('/', 1)[1]: name for name in archive.namelist() if not name.endswith('/')}
    checks = []
    for relative, old in names:
        body = archive.read(members[relative])
        checks.append(dict(path=relative, sha256=hashlib.sha256(body).hexdigest(),
                           identical_to_old=body == (OLD/old).read_bytes()))
    result = dict(archive_files=len(members), pinned_files=len(pinned),
                  archive_only_paths=sorted(set(members)-pinned), pinned_only_paths=sorted(pinned-set(members)),
                  source_comparisons=checks)
(OUT/'ARCHIVE_COMPARISON.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
