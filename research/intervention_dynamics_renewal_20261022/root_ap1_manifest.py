"""Two exact GitHub metadata requests, no data blobs or source execution."""
import json
import urllib.parse

import root_search as scout


def main():
    record, raw = scout.get('ap1_repository', 'https://api.github.com/repos/arjunrajlaboratory/cellularmemory')
    if record.get('status') != 200 or 'error_type' in record:
        print('AP1_REPOSITORY_ACCESS_FAILED_RETAINED')
        return 1
    repository = json.loads(raw)
    branch = urllib.parse.quote(repository['default_branch'], safe='')
    url = 'https://api.github.com/repos/arjunrajlaboratory/cellularmemory/git/trees/'+branch+'?recursive=1'
    record, raw = scout.get('ap1_tree', url)
    if record.get('status') != 200 or 'error_type' in record:
        print('AP1_TREE_ACCESS_FAILED_RETAINED')
        return 1
    tree = json.loads(raw)
    manifest = {'repository_id': repository['id'], 'full_name': repository['full_name'],
                'default_branch': repository['default_branch'], 'tree_sha': tree['sha'],
                'truncated': tree['truncated'], 'entries': [
                    {k: item.get(k) for k in ['path', 'type', 'size', 'sha', 'url']} for item in tree['tree']]}
    scout.write(scout.OUT/'AP1_REPOSITORY_MANIFEST.json', manifest)
    print(json.dumps({k: manifest[k] for k in ['repository_id', 'default_branch', 'tree_sha', 'truncated']}
                     | {'entry_count': len(manifest['entries'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
