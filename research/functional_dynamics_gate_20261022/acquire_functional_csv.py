"""Acquire three manifest-pinned CSVs; expose headers only, never responses."""
import csv
import hashlib
import io
import json

from root_data_scout import OUT, get, write


FILES = [
    ('hct116_replicates', 'https://ndownloader.figshare.com/files/56428388',
     295392, 'ae55aacf1f6549b04471f9d9d68e6cfe'),
    ('hct116_dose_response', 'https://ndownloader.figshare.com/files/56428391',
     392663, '010489434a9e563f4f23afa304c70aca'),
    ('hts001', 'https://zenodo.org/api/records/18292967/files/HTS001.csv/content',
     3039472, 'a5959a38166685707e840369ce34d74d'),
]


def main():
    out = []
    for name, url, size, md5 in FILES:
        receipt, raw = get(name, url, cap=4_000_000)
        rec = {'name': name, 'status': receipt.get('status'),
               'bytes': len(raw), 'redirect_received': bool(receipt.get('location'))}
        if receipt.get('status') == 200 and 'error_type' not in receipt:
            rec['size_matches'] = len(raw) == size
            rec['md5_matches'] = hashlib.md5(raw).hexdigest() == md5
            if not rec['size_matches'] or not rec['md5_matches']:
                raise ValueError('manifest_integrity_mismatch: '+name)
            reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')))
            rec['header'] = next(reader)
            rec['row_count'] = sum(1 for _ in reader)
        out.append(rec)
    write(OUT/'CSV_HEADERS.json', out)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
