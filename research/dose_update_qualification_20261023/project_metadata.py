"""Project dataset identities and candidate source repositories, never outcomes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification/sources'

if __name__ == '__main__':
    dataset = json.loads((OUT / 'emeraldbay_metadata.body').read_text())
    print(json.dumps(dict(id=dataset['id'], sha=dataset['sha'],
        last_modified=dataset.get('lastModified'),
        relevant_files=[row['rfilename'] for row in dataset['siblings']
            if not row['rfilename'].startswith('expression_data/')]), indent=2))
    repo_file = OUT / 'rhaister_repos.body'
    if repo_file.exists():
        repos = json.loads(repo_file.read_text())
        print(json.dumps(dict(total=repos.get('total_count'),
            candidates=[{key: row.get(key) for key in
                ['full_name', 'html_url', 'description', 'default_branch']}
                for row in repos.get('items', [])]), indent=2))
