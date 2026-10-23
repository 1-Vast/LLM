"""Read three exact primary-linked public metadata records, no data arrays."""
import json

from root_data_scout import OUT, get, write


def main():
    records = []
    for name, url in [
        ('bestdr_zenodo_18292966', 'https://zenodo.org/api/records/18292966'),
        ('bestdr_zenodo_18292967', 'https://zenodo.org/api/records/18292967'),
        ('bestdr_figshare_29610530', 'https://api.figshare.com/v2/articles/29610530')]:
        receipt, raw = get(name, url)
        if receipt.get('status') != 200 or 'error_type' in receipt:
            records.append({'name': name, 'status': 'ACCESS_FAILURE_RETAINED'})
            continue
        d = json.loads(raw)
        if 'zenodo' in name:
            meta = d['metadata']
            records.append({'name': name, 'id': d['id'], 'title': meta['title'],
                'description': meta.get('description'), 'doi': d.get('doi'),
                'version': meta.get('version'), 'related_identifiers': meta.get('related_identifiers'),
                'files': d.get('files'), 'links': d.get('links')})
        else:
            records.append({'name': name, 'id': d['id'], 'title': d['title'],
                'description': d.get('description'), 'doi': d.get('doi'),
                'version': d.get('version'), 'files': d.get('files'),
                'references': d.get('references')})
    write(OUT/'BESTDR_MANIFESTS.json', records)
    print(json.dumps(records, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
