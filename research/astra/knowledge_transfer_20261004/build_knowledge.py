"""Build an outcome-free, provenance-preserving biological prior and its controls.

Target annotations are NOT converted into proven binding or causal claims. Network
signatures encode signed topology, not the sign or magnitude of a drug intervention.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import sqlite3

import numpy as np
import pandas as pd
from scipy import sparse

from .acquire import ASSETS, HERE, digest

OUT = HERE / 'knowledge'
EXCLUDED_PMIDS = {'35197630', '39168097'}
ANNOTATION_COLUMNS = [f'{side}_{col}' for side in ('ANCHOR', 'LIBRARY')
                      for col in ('ID', 'NAME', 'TARGET', 'PATHWAY', 'DRUG_TYPE')]


def normalise_rows(x):
    x = sparse.csr_matrix(x, dtype=float)
    norm = np.sqrt(np.asarray(x.multiply(x).sum(axis=1)).ravel())
    return sparse.diags(1 / np.maximum(norm, 1e-12)) @ x


def cosine(x):
    z = normalise_rows(x)
    return (z @ z.T).toarray()


def resolver(frame):
    """Approved symbols take precedence; ambiguous aliases are unresolved."""
    approved = {str(r.symbol).upper(): str(r.symbol) for r in frame.itertuples()}
    aliases = {}
    for r in frame.itertuples():
        for field in ('alias_symbol', 'prev_symbol'):
            value = getattr(r, field)
            if pd.notna(value):
                for alias in str(value).split('|'):
                    aliases.setdefault(alias.upper(), set()).add(str(r.symbol))

    def resolve(token):
        key = token.strip().upper()
        if key in approved:
            return approved[key], 'approved_symbol'
        vals = aliases.get(key, set())
        if len(vals) == 1:
            return next(iter(vals)), 'unambiguous_hgnc_alias'
        return None, 'ambiguous_alias' if vals else 'unresolved_annotation'
    return resolve


def annotations():
    # No assay response, growth, QC or outcome column is read here.
    raw = pd.read_csv(ASSETS / 'jaaks.csv', usecols=ANNOTATION_COLUMNS, dtype=str)
    frames = []
    for side in ('ANCHOR', 'LIBRARY'):
        frame = raw[[f'{side}_{c}' for c in ('ID', 'NAME', 'TARGET', 'PATHWAY', 'DRUG_TYPE')]].copy()
        frame.columns = ['drug_id', 'name', 'target', 'pathway', 'drug_type']
        frames.append(frame)
    drugs = pd.concat(frames).fillna('').drop_duplicates().sort_values('drug_id')
    if drugs.drug_id.duplicated().any():
        raise ValueError('conflicting drug annotations require explicit adjudication')
    return drugs.reset_index(drop=True)


def signed_operator(genes, edge_rows):
    """Outgoing, row-L1-normalised operator; conflicting gene-pair signs excluded."""
    gi = {g: i for i, g in enumerate(genes)}
    signs = {}
    for a, b, sign in edge_rows:
        if a in gi and b in gi:
            signs.setdefault((a, b), set()).add(sign)
    good = [(a, b, next(iter(s))) for (a, b), s in signs.items() if len(s) == 1]
    rr = [gi[a] for a, b, s in good]
    cc = [gi[b] for a, b, s in good]
    vv = [s for a, b, s in good]
    mat = sparse.csr_matrix((vv, (rr, cc)), shape=(len(genes), len(genes)), dtype=float)
    norm = np.asarray(abs(mat).sum(axis=1)).ravel()
    return sparse.diags(1 / np.maximum(norm, 1)) @ mat, len(good), len(signs) - len(good)


def main():
    OUT.mkdir(exist_ok=True)
    hgnc = pd.read_csv(ASSETS / 'hgnc.tsv', sep='\t', dtype=str)
    hgnc = hgnc[hgnc.status == 'Approved'].copy()
    resolve = resolver(hgnc)
    drugs = annotations()
    ids = list(drugs.drug_id)
    mapped, mappings, token_sets, path_sets = [], [], [], []
    for r in drugs.itertuples():
        tokens = sorted(set(t.strip() for t in re.split(r'[,|]', r.target) if t.strip()))
        token_sets.append(tokens)
        path_sets.append(sorted(set(t.strip() for t in r.pathway.split('|') if t.strip())))
        genes = set()
        for token in tokens:
            gene, how = resolve(token)
            if gene:
                genes.add(gene)
            mappings.append(dict(drug_id=r.drug_id, raw_target=token, gene=gene, resolution=how,
                                 claim_type='provider_target_annotation', action_sign=None,
                                 binding_assay_evidence=None))
        mapped.append(genes)

    graph_rows = []
    gene_edges = {'omnipath': [], 'collectri': []}
    graph_stats = {}
    for kind in gene_edges:
        frame = pd.read_csv(ASSETS / f'{kind}.tsv', sep='\t', dtype=str).fillna('')
        counts = dict(raw_rows=len(frame), retained_claims=0, operator_candidates=0,
                      benchmark_reference_excluded=0, no_reference=0, unresolved_endpoints=0,
                      unsigned_or_conflicting=0, undirected=0, complex_endpoint_rows=0)
        for r in frame.itertuples():
            refs = set(re.findall(r'(?<!\d)\d{5,9}(?!\d)', r.references))
            if refs & EXCLUDED_PMIDS:
                counts['benchmark_reference_excluded'] += 1
                continue
            a, _ = resolve(r.source_genesymbol)
            b, _ = resolve(r.target_genesymbol)
            directed = r.is_directed.lower() in ('1', 'true')
            pos = r.is_stimulation.lower() in ('1', 'true')
            neg = r.is_inhibition.lower() in ('1', 'true')
            sign = (1 if pos else -1) if pos != neg else None
            complex_endpoint = r.source.startswith('COMPLEX:') or r.target.startswith('COMPLEX:')
            usable = bool(refs and a and b and directed and sign is not None and not complex_endpoint)
            counts['no_reference'] += not bool(refs)
            counts['unresolved_endpoints'] += not bool(a and b)
            counts['complex_endpoint_rows'] += complex_endpoint
            counts['unsigned_or_conflicting'] += sign is None
            counts['undirected'] += not directed
            counts['retained_claims'] += 1
            counts['operator_candidates'] += usable
            graph_rows.append((kind, r.source, r.target, a, b, int(directed), sign,
                               r.sources, r.references, int(usable)))
            if usable:
                gene_edges[kind].append((a, b, sign))
        graph_stats[kind] = counts

    genes = sorted(set().union(*mapped, *[{a for a, b, s in es} | {b for a, b, s in es}
                                         for es in gene_edges.values()]))
    gi = {g: i for i, g in enumerate(genes)}
    seed = sparse.lil_matrix((len(ids), len(genes)), dtype=float)
    for i, gs in enumerate(mapped):
        for g in gs:
            seed[i, gi[g]] = 1
    seed = normalise_rows(seed)
    protein, n_p, conflicts_p = signed_operator(genes, gene_edges['omnipath'])
    tf, n_t, conflicts_t = signed_operator(genes, gene_edges['collectri'])
    hop1 = seed @ protein
    hop2 = hop1 @ protein
    transcription = (seed + 0.5 * hop1) @ tf
    # Separate feature blocks; do not add protein and transcriptional state as if
    # they were observations at the same time point. Block weights are fixed.
    net_features = sparse.hstack([seed, .5 * normalise_rows(hop1),
                                 .25 * normalise_rows(hop2),
                                 .25 * normalise_rows(transcription)], format='csr')
    k_net = cosine(net_features)

    def indicators(sets):
        vocab = sorted(set().union(*map(set, sets)))
        vi = {v: j for j, v in enumerate(vocab)}
        m = np.zeros((len(ids), len(vocab)))
        for i, ss in enumerate(sets):
            for s in ss:
                m[i, vi[s]] = 1
        return m
    k_annotation = .5 * cosine(indicators(token_sets)) + .5 * cosine(indicators(path_sets))
    covered = np.array([bool(g) for g in mapped])
    perm = np.arange(len(ids))
    perm[covered] = np.random.default_rng(20261004).permutation(perm[covered])
    # Unmapped drugs have a zero network feature, in both real and permuted arms.
    semantic = {
        'drug_id': np.eye(len(ids)),
        'annotation': .5 * np.eye(len(ids)) + .5 * k_annotation,
        'network': .5 * np.eye(len(ids)) + .25 * k_annotation + .25 * k_net,
        'permuted_network': .5 * np.eye(len(ids)) + .25 * k_annotation +
                            .25 * k_net[np.ix_(perm, perm)],
    }
    for k in semantic:
        d = np.sqrt(np.maximum(np.diag(semantic[k]), 1e-12))
        semantic[k] = semantic[k] / np.outer(d, d)
        if np.linalg.eigvalsh(semantic[k]).min() < -1e-8:
            raise AssertionError('non-PSD kernel')
    np.savez_compressed(OUT / 'drug_kernels.npz', drug_ids=np.array(ids),
                        network_covered=covered, permutation=perm, **semantic)
    drugs['mapped_genes'] = ['|'.join(sorted(g)) for g in mapped]
    drugs.to_csv(OUT / 'drugs.tsv', sep='\t', index=False)
    (OUT / 'target_mapping.json').write_text(json.dumps(mappings, indent=2)+'\n')

    dbpath = OUT / 'knowledge.sqlite'
    if dbpath.exists():
        dbpath.unlink()
    db = sqlite3.connect(dbpath)
    db.executescript('''
      CREATE TABLE release(file TEXT PRIMARY KEY, url TEXT, sha256 TEXT, retrieved_utc TEXT,
                           license_note TEXT);
      CREATE TABLE gene(symbol TEXT PRIMARY KEY, hgnc_id TEXT, ensembl_id TEXT, uniprot_ids TEXT);
      CREATE TABLE drug(drug_id TEXT PRIMARY KEY, name TEXT, target_annotation TEXT,
                        pathway_annotation TEXT, drug_type TEXT);
      CREATE TABLE drug_target_annotation(drug_id TEXT, raw_target TEXT, gene TEXT,
                        resolution TEXT, claim_type TEXT, action_sign INTEGER,
                        binding_assay_evidence TEXT);
      CREATE TABLE claim(id INTEGER PRIMARY KEY, dataset TEXT, source_uniprot TEXT,
        target_uniprot TEXT, source_gene TEXT, target_gene TEXT, directed INTEGER, sign INTEGER,
        source_resources TEXT, references_raw TEXT, usable_before_gene_conflict_check INTEGER,
        species TEXT DEFAULT 'Homo sapiens', tissue TEXT, cell_line TEXT, dose TEXT, time TEXT,
        evidence_note TEXT DEFAULT 'Aggregated literature annotation; assay context not extracted');
      CREATE INDEX claim_source ON claim(source_gene);
      CREATE INDEX claim_target ON claim(target_gene);
      CREATE INDEX drug_gene ON drug_target_annotation(gene);
    ''')
    releases = json.loads((HERE / 'download_manifest.json').read_text())
    db.executemany('INSERT INTO release VALUES (?,?,?,?,?)', [
        (r['file'], r['url'], r['sha256'], r['retrieved_utc'],
         'Original source licenses retained; commercial filter is not a blanket license grant')
        for r in releases if r['status'] == 'downloaded'])
    db.executemany('INSERT INTO gene VALUES (?,?,?,?)', [
        (r.symbol, r.hgnc_id, None if pd.isna(r.ensembl_gene_id) else r.ensembl_gene_id,
         None if pd.isna(r.uniprot_ids) else r.uniprot_ids) for r in hgnc.itertuples()])
    db.executemany('INSERT INTO drug VALUES (?,?,?,?,?)', [
        (r.drug_id, r.name, r.target, r.pathway, r.drug_type) for r in drugs.itertuples()])
    db.executemany('INSERT INTO drug_target_annotation VALUES (?,?,?,?,?,?,?)', [
        tuple(m[k] for k in ('drug_id', 'raw_target', 'gene', 'resolution', 'claim_type',
                            'action_sign', 'binding_assay_evidence')) for m in mappings])
    db.executemany('''INSERT INTO claim(dataset,source_uniprot,target_uniprot,source_gene,
                      target_gene,directed,sign,source_resources,references_raw,
                      usable_before_gene_conflict_check) VALUES (?,?,?,?,?,?,?,?,?,?)''', graph_rows)
    db.commit()
    db.close()
    report = dict(drugs=len(ids), drugs_with_resolved_gene=int(covered.sum()),
                  drugs_without_resolved_gene=[ids[i] for i in range(len(ids)) if not covered[i]],
                  unique_mapped_target_genes=len(set().union(*mapped)),
                  annotation_rows=len(mappings), resolved_annotation_rows=sum(m['gene'] is not None for m in mappings),
                  unresolved_tokens=sorted({m['raw_target'] for m in mappings if m['gene'] is None}),
                  graph=graph_stats, operator_gene_nodes=len(genes),
                  protein_operator_edges=n_p, transcription_operator_edges=n_t,
                  protein_conflicting_gene_pairs=conflicts_p,
                  transcription_conflicting_gene_pairs=conflicts_t,
                  unknown_context_is_match=False,
                  conditions='Human aggregate; tissue/cell/dose/time unknown',
                  measured_drug_effect_claims=0,
                  outcome_columns_read=[],
                  excluded_benchmark_pmids=sorted(EXCLUDED_PMIDS))
    report['output_sha256'] = {p.name: digest(p) for p in sorted(OUT.iterdir())
                               if p.is_file() and p.name != 'coverage.json'}
    (OUT / 'coverage.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
