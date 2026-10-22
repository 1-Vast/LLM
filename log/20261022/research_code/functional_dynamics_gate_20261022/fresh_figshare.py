"""One registered cache-distinct signing request per file, immediate redirect."""
import csv
import hashlib
import io
import json
import time
from urllib.parse import urlsplit

from acquire_functional_csv import FILES
from root_data_scout import OUT, get, write


def main():
    rows = []
    for name, url, size, md5 in FILES[:2]:
        r, raw = get(name+'_fresh', url+'?maestro_functional='+str(time.time_ns()), cap=4_000_000)
        location = r.get('location')
        if r.get('status') == 302 and location:
            parsed = urlsplit(location)
            if (parsed.scheme != 'https' or parsed.hostname != 's3-eu-west-1.amazonaws.com'
                    or not parsed.path.startswith('/pfigshare-u-files/')):
                raise ValueError('unexpected_redirect_host')
            r, raw = get(name+'_fresh_object', location, cap=4_000_000)
        row = {'name': name, 'status': r.get('status'), 'bytes': len(raw)}
        if r.get('status') == 200 and 'error_type' not in r:
            if len(raw) != size or hashlib.md5(raw).hexdigest() != md5:
                raise ValueError('manifest_mismatch')
            reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')))
            row.update(header=next(reader), rows=sum(1 for _ in reader), md5_matches=True)
        rows.append(row)
    write(OUT/'HCT116_FRESH_HEADERS.json', rows)
    print(json.dumps(rows, ensure_ascii=False))


if __name__ == '__main__':
    main()
