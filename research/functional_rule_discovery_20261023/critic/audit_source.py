"""Bind official PDF, checked code blob and exact history-identification scope."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
out = root / 'log/20261023/functional_rule_discovery/critic'
tree = json.loads((out / 'author_tree3.body').read_bytes())
entry = next(x for x in tree['tree'] if x['path'] == 'tta_library/mgtta.py')
raw = (out / 'author_code4.body').read_bytes()
git_sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
result = dict(tree_sha=tree['sha'], code_path=entry['path'], expected_blob_sha=entry['sha'],
              actual_blob_sha=git_sha, blob_matches=git_sha == entry['sha'],
              code_executed=False, paper_sha256=hashlib.sha256((out / 'primary2.body').read_bytes()).hexdigest(),
              history_scope='Exact published title/DOI and preprint2412.16901, MGTTA/keikeiqi and author-name combination: no history md/py/json match before acquisition; not proof of global bibliographic novelty',
              requests=4, visual_pages=[3, 4, 5], full_proof_or_code_audit=False)
(out / 'SOURCE_BINDING.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
(out / 'FAILURES.md').write_text(
    'First pypdf extraction could not encode unpaired PDF-font Unicode surrogates. '
    'Preserved PDF; extraction now replaces only unencodable characters. '
    'Pages 3–5 rendered and visually checked for operative equations/algorithm; '
    'no extra network request. No author code, models or biological data executed.\n', encoding='utf-8')
print(json.dumps(result))
