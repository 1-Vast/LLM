"""Reference-only skipped-exon definition and coordinate-presence audit.

Never parses counts, PSI, significance or treatment-response values.
"""
import csv
import gzip
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
GENE = re.compile(r'gene_id "([^"]+)"')
TRANSCRIPT = re.compile(r'transcript_id "([^"]+)"')


def canonical(gene, chrom, strand, start, end, left_start, left_end, right_start, right_end):
    left, right = sorted(((int(left_start), int(left_end)), (int(right_start), int(right_end))))
    return (gene.strip('"').split('.')[0], chrom, strand, int(start), int(end), *left, *right)


def main():
    transcripts = {}
    header = []
    with gzip.open(HERE / 'sources/gencode.v19.annotation.gtf.gz', 'rt') as handle:
        for line in handle:
            if line.startswith('#'):
                header.append(line.strip())
                continue
            row = line.rstrip('\n').split('\t')
            if row[2] != 'exon':
                continue
            tid = TRANSCRIPT.search(row[8]).group(1)
            gene = GENE.search(row[8]).group(1).split('.')[0]
            entry = transcripts.setdefault(tid, (gene, row[0], row[6], []))
            assert entry[:3] == (gene, row[0], row[6])
            entry[3].append((int(row[3]) - 1, int(row[4])))
    edges, triples = set(), set()
    for gene, chrom, strand, exons in transcripts.values():
        exons = sorted(set(exons))
        for left, right in zip(exons, exons[1:]):
            edges.add((gene, chrom, strand, *left, *right))
        for left, middle, right in zip(exons, exons[1:], exons[2:]):
            triples.add((gene, chrom, strand, *middle, *left, *right))
    reference = {key for key in triples if (key[0], key[1], key[2], *key[5:9]) in edges}
    del transcripts, edges, triples
    columns = ['gene', 'chr', 'strand', 'exonStart_0base', 'exonEnd', 'upstreamES', 'upstreamEE', 'downstreamES', 'downstreamEE']
    with (HERE / 'reference_se.tsv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerow(columns)
        writer.writerows(sorted(reference))
    report = {'reference': 'GENCODE19; annotated consecutive inclusion triple plus annotated direct skipping junction in same gene',
              'coordinate_convention': 'zero-based starts, exclusive ends; genomic flank order, with strand retained',
              'gtf_header': header, 'reference_events': len(reference), 'reference_genes': len({key[0] for key in reference}),
              'outcome_columns_parsed': False, 'archives': []}
    common = set(reference)
    for item in json.loads((HERE / 'selected_archives.json').read_text()):
        with tarfile.open(HERE / 'sources' / (item['accession'] + '.tar.gz'), 'r:gz') as archive:
            names = [name for name in archive.getnames() if name.endswith('/SE.MATS.JunctionCountOnly.txt')]
            assert len(names) == 1
            rows = csv.DictReader((line.decode('utf-8-sig') for line in archive.extractfile(names[0])), delimiter='\t')
            keys = []
            for row in rows:
                keys.append(canonical(row['GeneID'], row['chr'], row['strand'], *[row[col] for col in columns[3:]]))
        present = reference.intersection(keys)
        common.intersection_update(present)
        report['archives'].append({'accession': item['accession'], 'rows': len(keys), 'unique_coordinate_gene_keys': len(set(keys)),
                                   'reference_present': len(present), 'reference_missing': len(reference - present)})
    report['common_reference_events'] = len(common)
    report['all_reference_events_emitted_by_all_six'] = common == reference
    (HERE / 'annotation_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
