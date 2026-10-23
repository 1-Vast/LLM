"""Retrieve author design assets; inspect metadata headers only, no data rows."""
import base64
import gzip
import io
import json

from lineage_followup import OUT, get


def main():
    tree = json.loads((OUT / 'watermelon_repo_tree.json').read_text(encoding='utf-8'))
    wanted = {'README.md', 'data/pc9_time_course.rds', 'data/pooled_persisters.rds'}
    summaries = []
    for row in tree['tree']:
        if row['path'] not in wanted:
            continue
        name = 'author_blob_' + row['sha']
        response = get(name, row['url'])
        response.raise_for_status()
        body = base64.b64decode(response.json()['content'])
        (OUT / (name + '.decoded.txt')).write_bytes(body)
        summaries.append({'path': row['path'], 'blob_sha': row['sha'], 'decoded_text': body.decode('utf-8')})
    directory = get('geo_supplement_directory',
                    'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE150nnn/GSE150949/suppl/')
    summaries.append({'directory_status': directory.status_code})
    for filename in ('GSE150949_metaData_with_lineage.txt.gz',
                     'GSE150949_pooled_watermelon.metadata.matrix.csv.gz'):
        response = get(filename.replace('.', '_'),
                       'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE150nnn/GSE150949/suppl/' + filename)
        if response.status_code != 200:
            summaries.append({'file': filename, 'status': response.status_code})
            continue
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as stream:
            first = stream.readline(2_000_001)
        assert len(first) <= 2_000_000
        text = first.decode('utf-8-sig').rstrip('\r\n')
        summaries.append({'file': filename, 'header_only': text,
                          'compressed_bytes_contacted': len(response.content), 'rows_parsed': 0})
    path = OUT / 'WATERMELON_HEADER_RESULT.json'
    with path.open('x', encoding='utf-8') as stream:
        json.dump(summaries, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(summaries, ensure_ascii=False))


if __name__ == '__main__':
    main()
