"""Record original equations and author tree paths; no author-code execution."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[3]
out = root / 'log/20261023/feedback_sufficiency_renewal/critic'
xml = ET.fromstring((out / 'primary2.body').read_bytes())
paragraphs = [' '.join(''.join(x.itertext()).split()) for x in xml.iter() if x.tag == 'p']
equations = [' '.join(''.join(x.itertext()).split()) for x in xml.iter() if x.tag == 'disp-formula']
tree = json.loads((out / 'author_tree4.body').read_bytes())
paths = {'maml_train_system.py', 'main_maml_train.py', 'model_utils/get_optimizer.py'}
result = dict(
    doi='10.1016/j.jpha.2025.101386', tree_sha=tree['sha'], tree_truncated=tree['truncated'],
    source_paragraphs=[x for x in paragraphs if 'Single updating step' in x or
                       'inner-loop learning rate' in x or 'zero-shot configuration' in x],
    equations=equations,
    author_code_paths_not_downloaded=[x for x in tree['tree'] if x['path'] in paths],
    code_implementation_verified=False, model_fits=0,
    exact_history_check='No exact-title or DOI-number hit in historical log/research md/py before primary fetch')
(out / 'EVIDENCE_CONTRACT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: result[k] for k in ['tree_sha', 'author_code_paths_not_downloaded']}, indent=2))
