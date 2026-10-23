"""Read metadata of the exact primary-linked Response-Dynamics repository."""
import json
import urllib.parse

import root_search as scout


def main():
    base = 'https://api.github.com/repos/schultz-lab/Response-Dynamics'
    receipt, raw = scout.get('response_repository', base)
    if receipt.get('status') != 200 or 'error_type' in receipt:
        print('RESPONSE_REPOSITORY_ACCESS_FAILURE_RETAINED')
        return 1
    repo = json.loads(raw)
    branch = urllib.parse.quote(repo['default_branch'], safe='')
    receipt, raw = scout.get('response_tree', base+'/git/trees/'+branch+'?recursive=1')
    if receipt.get('status') != 200 or 'error_type' in receipt:
        print('RESPONSE_TREE_ACCESS_FAILURE_RETAINED')
        return 1
    tree = json.loads(raw)
    manifest = {'repository_id': repo['id'], 'full_name': repo['full_name'],
        'default_branch': repo['default_branch'], 'tree_sha': tree['sha'],
        'truncated': tree['truncated'], 'entries': [
            {k: item.get(k) for k in ('path', 'type', 'size', 'sha', 'url')}
            for item in tree['tree']]}
    scout.write(scout.OUT/'RESPONSE_DYNAMICS_MANIFEST.json', manifest)
    print(json.dumps({k: manifest[k] for k in ('repository_id', 'default_branch', 'tree_sha', 'truncated')}
                     | {'entries': manifest['entries']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
