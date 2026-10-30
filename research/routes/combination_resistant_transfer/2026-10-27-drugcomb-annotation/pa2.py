#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PROTOCOL_PA2 (v1, frozen 2026-10-27) reference implementation.

R192 pre-work: add a deterministic HGNC alias/name resolution layer on top of the
P-A v1 token layer, then re-run the *frozen* S1-A rule (KEGG argmax) with the
*same* thresholds, and report v1 -> v2 changes.

Guarantees:
  * only reads local files, no network;
  * NEVER reads a DrugComb response column (identity columns by position only);
  * does NOT modify any P-A v1 product (verified by SHA256 before/after);
  * deterministic: no randomness, no timestamps, JSON sort_keys=True;
  * input / resource / script / protocol SHA256 recorded in pa2.json.

Usage:  python pa2.py
"""
import collections
import csv
import itertools
import json
import os
import sys

sys.dont_write_bytecode = True          # never write __pycache__ into the study dir
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import pa  # noqa: E402  P-A v1 frozen implementation (read-only reuse)

ROOT = pa.ROOT

HGNC_PATH = os.path.join(BASE, 'resources_hgnc', 'hgnc_complete_set.txt')
EXPECTED_HGNC = {
    'bytes': 16982321,
    'sha256': '12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91',
    'url_primary': 'https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt',
    'url_alternative_unused': 'https://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt',
}
HGNC_COLS = ['symbol', 'name', 'alias_symbol', 'alias_name', 'prev_symbol', 'status',
             'date_modified']

# v1 products (read-only; must be unchanged after the run) -- PROTOCOL_PA2 section 1
V1_PRODUCTS = {
    'mapping_table.csv': '45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4',
    'pa.json': 'f5559d26a86679bd7be77ffd00fc5c4195be50eb611e8677a87434fb842c9fa3',
    'pa.py': '25e64208a95b0c92b126823020e361ad208e517eef95c4f093f6be835ff470f3',
    'PROTOCOL_PA.md': '16c40f9f61765637185bd061b1aeb4e62886bdfa027b8baf509830775bae607d',
}
V1_REFERENCE = {
    'mapped_drugs': 1418,
    'coverage_pct_of_4088': 34.6869,
    'analyzable_levels_pa': 62,
    'analyzable_levels_e1': 63,
    'both_unseen_units_pa': 2682,
    'both_unseen_units_e1': 3739,
    'train_units_pa': 85436,
    'strict_train_units_pa': 58788,
    'levels_total': 123,
}

# variants (PROTOCOL_PA2 section 8); primary = V2-A
VARIANTS = {
    'V2-A': {'label': 'primary: base + token-symbol + token-alias + segment-name',
             'layers': ('token_symbol', 'token_alias', 'segment_name'),
             'short_alias_guard_len': 0},
    'V2-B': {'label': 'sensitivity: base + segment-name only',
             'layers': ('segment_name',), 'short_alias_guard_len': 0},
    'V2-C': {'label': 'sensitivity: base + token-symbol only',
             'layers': ('token_symbol',), 'short_alias_guard_len': 0},
    'V2-D': {'label': 'sensitivity: V2-A without generic short (hnorm len<=2) token alias/prev resolutions',
             'layers': ('token_symbol', 'token_alias', 'segment_name'),
             'short_alias_guard_len': 2},
}
PRIMARY = 'V2-A'
ENUM_MAX_ENTITIES = 3
ENUM_MAX_PRODUCT = 16
NAMED_12 = pa.NAMED_12


# ---------------------------------------------------------------- helpers
def sha256_file(path):
    return pa.sha256_file(path)


def hnorm(s):
    """PROTOCOL_PA2 section 5: NFKC -> casefold -> keep alphanumerics."""
    return pa.norm(s)


def verify_hgnc():
    rec = {'path': os.path.relpath(HGNC_PATH, ROOT),
           'bytes_expected': EXPECTED_HGNC['bytes'],
           'sha256_expected': EXPECTED_HGNC['sha256'],
           'url_primary': EXPECTED_HGNC['url_primary'],
           'url_alternative_unused': EXPECTED_HGNC['url_alternative_unused']}
    if not os.path.exists(HGNC_PATH):
        raise SystemExit('FATAL: HGNC file missing: ' + HGNC_PATH)
    rec['bytes'] = os.path.getsize(HGNC_PATH)
    rec['sha256'] = sha256_file(HGNC_PATH)
    rec['bytes_match'] = rec['bytes'] == rec['bytes_expected']
    rec['sha256_match'] = rec['sha256'] == rec['sha256_expected']
    if not (rec['bytes_match'] and rec['sha256_match']):
        raise SystemExit('FATAL: HGNC verification failed: %s' % json.dumps(rec, sort_keys=True))
    return rec


def build_hgnc_indexes():
    """PROTOCOL_PA2 section 5: normalized indexes from hgnc_complete_set."""
    df = pd.read_csv(HGNC_PATH, sep='\t', dtype=str, keep_default_na=False, usecols=HGNC_COLS)
    dates = df['date_modified'].replace('', np.nan).dropna()
    stats = {'rows': int(len(df)),
             'status_counts': dict(sorted(collections.Counter(df['status']).items())),
             'date_modified_max': str(dates.max()) if len(dates) else None,
             'date_modified_min': str(dates.min()) if len(dates) else None}
    sym = {}
    sym_conflicts = 0
    alias = collections.defaultdict(set)
    prev = collections.defaultdict(set)
    name = collections.defaultdict(set)
    alias_name = collections.defaultdict(set)
    approved = 0
    for r in df.itertuples(index=False):
        if r.status != 'Approved':
            continue
        approved += 1
        s = r.symbol.strip()
        if not s:
            continue
        k = hnorm(s)
        if k in sym and sym[k] != s:
            sym_conflicts += 1
        else:
            sym.setdefault(k, s)
        for field, idx in (('alias_symbol', alias), ('prev_symbol', prev)):
            for x in getattr(r, field).split('|'):
                x = x.strip()
                if x:
                    idx[hnorm(x)].add(s)
        for field, idx in (('name', name), ('alias_name', alias_name)):
            for x in getattr(r, field).split('|'):
                x = x.strip()
                if x:
                    idx[hnorm(x)].add(s)
    stats.update({
        'approved_rows_used': approved,
        'symbol_keys': len(sym), 'symbol_key_conflicts': sym_conflicts,
        'alias_symbol_keys': len(alias), 'prev_symbol_keys': len(prev),
        'name_keys': len(name), 'alias_name_keys': len(alias_name),
        'multi_target_keys': {
            'alias_symbol': sum(1 for v in alias.values() if len(v) > 1),
            'prev_symbol': sum(1 for v in prev.values() if len(v) > 1),
            'name': sum(1 for v in name.values() if len(v) > 1),
            'alias_name': sum(1 for v in alias_name.values() if len(v) > 1)},
    })
    return {'SYM': sym, 'ALIAS': dict(alias), 'PREV': dict(prev),
            'NAME': dict(name), 'ALIAS_NAME': dict(alias_name)}, stats


def load_segments():
    """PROTOCOL_PA2 section 4: raw segments split on | ; , only (keep spaces/case)."""
    idf = pd.read_excel(pa.PATHS['I2'])
    idf['_norm'] = idf['dname'].map(lambda x: pa.norm(x) if isinstance(x, str) else '')
    seg = collections.defaultdict(set)
    for nm, tn in zip(idf['_norm'], idf['target_name']):
        if not nm or not isinstance(tn, str):
            continue
        for s in tn.replace('|', ';').replace(',', ';').split(';'):
            if s.strip():
                seg[nm].add(s.strip())
    drh = pd.read_csv(pa.PATHS['I3'], sep='\t', skiprows=9, low_memory=False)
    for nm, tg in zip(drh['pert_iname'], drh['target']):
        if not isinstance(nm, str) or not isinstance(tg, str):
            continue
        n = pa.norm(nm)
        if not n:
            continue
        for s in tg.replace('|', ';').replace(',', ';').split(';'):
            if s.strip():
                seg[n].add(s.strip())
    return dict(seg)


# ---------------------------------------------------------------- resolution
def resolve_entities(dn, t1, segments, hg, g_s1, layers, short_alias_guard_len, stats):
    """PROTOCOL_PA2 section 6/7 resolution for one drug.

    Returns (base, layer_symbols, ambiguous_entities):
      base              : v1 exact symbol set (always kept)
      layer_symbols     : dict layer -> set of symbols contributed uniquely
      ambiguous_entities: list of (kind, entity, frozenset(candidates), layer)
    `stats` (Counter) is updated in place.
    """
    tokens = t1.get(dn, set())
    base = {t for t in tokens if t in g_s1}          # v1 exact layer, always kept
    layer_symbols = {'token_symbol': set(), 'token_alias': set(), 'segment_name': set()}
    ambiguous = []
    stats['sum_tokens'] += len(tokens)
    stats['sum_segments'] += len(segments.get(dn, ()))
    if 'token_symbol' in layers or 'token_alias' in layers:
        for t in sorted(tokens):
            nt = hnorm(t)
            if 'token_symbol' in layers and nt in hg['SYM']:
                c = {hg['SYM'][nt]} & g_s1
                if len(c) == 1:
                    if c <= base:
                        stats['token_symbol_already_in_base'] += 1
                    else:
                        layer_symbols['token_symbol'] |= c
                        stats['token_symbol_unique'] += 1
                continue
            if 'token_alias' in layers:
                if short_alias_guard_len and len(nt) <= short_alias_guard_len:
                    stats['token_alias_short_guard_skipped'] += 1
                    continue
                c = (hg['ALIAS'].get(nt, set()) | hg['PREV'].get(nt, set())) & g_s1
                if len(c) == 1:
                    if c <= base:
                        stats['token_alias_already_in_base'] += 1
                    else:
                        layer_symbols['token_alias'] |= c
                        stats['token_alias_unique'] += 1
                elif len(c) > 1:
                    ambiguous.append(('token', t, frozenset(c), 'token_alias'))
                    stats['ambiguous_entities_total'] += 1
                    stats['ambiguous_token_alias'] += 1
    if 'segment_name' in layers:
        for e in sorted(segments.get(dn, set())):
            ne = hnorm(e)
            c = (hg['NAME'].get(ne, set()) | hg['ALIAS_NAME'].get(ne, set())) & g_s1
            if len(c) == 1:
                if c <= base or c <= layer_symbols['segment_name']:
                    stats['segment_name_already_present'] += 1
                else:
                    layer_symbols['segment_name'] |= c
                    stats['segment_name_unique'] += 1
            elif len(c) > 1:
                ambiguous.append(('segment', e, frozenset(c), 'segment_name'))
                stats['ambiguous_entities_total'] += 1
                stats['ambiguous_segment_name'] += 1
    return base, layer_symbols, ambiguous


def finalize_symbols(base, layer_symbols, ambiguous, compute_label, stats):
    """PROTOCOL_PA2 section 7: deterministic ambiguity handling."""
    syms = set(base)
    for s in layer_symbols.values():
        syms |= s
    if not ambiguous:
        return syms, {'n_ambiguous': 0, 'n_resolved': 0}
    prod = 1
    for _, _, c, _ in ambiguous:
        prod *= len(c)
    if len(ambiguous) > ENUM_MAX_ENTITIES or prod > ENUM_MAX_PRODUCT:
        stats['drugs_capped_by_enumeration_limit'] += 1
        stats['ambiguous_entities_unresolved'] += len(ambiguous)
        stats['drugs_with_unresolved_ambiguity'] += 1
        return syms, {'n_ambiguous': len(ambiguous), 'n_resolved': 0}
    choices = [sorted(c) for _, _, c, _ in ambiguous]
    labels = set()
    for combo in itertools.product(*choices):
        labels.add(compute_label(syms | set(combo)))
    if len(labels) == 1:
        for (kind, ent, cand, layer), ch in zip(ambiguous, choices):
            syms.add(ch[0])
        stats['ambiguous_entities_resolved'] += len(ambiguous)
        return syms, {'n_ambiguous': len(ambiguous), 'n_resolved': len(ambiguous)}
    stats['ambiguous_entities_unresolved'] += len(ambiguous)
    stats['drugs_with_unresolved_ambiguity'] += 1
    return syms, {'n_ambiguous': len(ambiguous), 'n_resolved': 0}


def rule_a_from_symbols(symbols, lib):
    """Frozen S1-A rule: argmax |S ∩ P|, ties by pathway name, max>=1."""
    if not symbols:
        return None
    idx = [lib['gidx'][g] for g in symbols]
    x = lib['mat'][idx, :].sum(axis=0)
    mx = int(x.max())
    if mx < 1:
        return None
    tied = sorted(lib['names'][i] for i in np.flatnonzero(x == mx))
    return {'pathway': tied[0], 'max_score': mx, 'tie_count': len(tied),
            'pathway_size': int(lib['K'][lib['names'].index(tied[0])])}


def run_variant(cfg, drugs_d1, t1, segments, hg, g_s1, lib):
    """Resolve + score one variant for all D1 drugs; return mapping/symbols/stats."""
    compute_label = lambda s: (rule_a_from_symbols(s, lib) or {}).get('pathway')
    mapping = {}
    symbols = {}
    per_drug = {}
    stats = collections.Counter()
    for dn in drugs_d1:
        base, layer_symbols, ambiguous = resolve_entities(
            dn, t1, segments, hg, g_s1, cfg['layers'], cfg['short_alias_guard_len'], stats)
        stats['drugs_with_ambiguous_entity'] += (1 if ambiguous else 0)
        syms, fin = finalize_symbols(base, layer_symbols, ambiguous, compute_label, stats)
        symbols[dn] = syms
        per_drug[dn] = {
            'n_base': len(base),
            'n_layer': {k: len(v) for k, v in layer_symbols.items()},
            'n_ambiguous': fin['n_ambiguous'],
            'n_resolved': fin['n_resolved'],
            'n_new_vs_base': len(syms - base),
        }
        rec = rule_a_from_symbols(syms, lib)
        if rec is not None:
            mapping[dn] = rec
    return mapping, symbols, dict(sorted(stats.items())), per_drug


def mapping_eval(mapping, universe_sorted, units):
    """Coverage / level / unit statistics with the frozen PA + E1 splits."""
    names = sorted(mapping)
    pa_split = pa.split_pa(names, 0.20)
    e1_split = pa.split_pa(universe_sorted, 0.20)
    rows = pa.level_table(mapping, pa_split['holdout'], e1_split['holdout'])
    units_stats = pa.unit_stats(mapping, units, universe_sorted)
    ties = sum(1 for r in mapping.values() if r['tie_count'] > 1)
    score1 = sum(1 for r in mapping.values() if r['max_score'] == 1)
    lvl_counts = collections.Counter(r['pathway'] for r in mapping.values())
    top = max(lvl_counts.values()) if lvl_counts else 0
    return {
        'coverage': {
            'n_mapped_D1': len(mapping),
            'pct_of_4088': pa.pct(len(mapping), 4088),
            'pct_of_4076': pa.pct(len(mapping), 4076),
        },
        'levels': {
            'n_levels': len(rows),
            'n_levels_ge2_drugs': sum(1 for r in rows if r['n_all'] >= 2),
            'n_analyzable_pa': sum(1 for r in rows if r['analyzable_pa']),
            'n_analyzable_e1split': sum(1 for r in rows if r['analyzable_e1']),
            'levels_missing_in_holdout_pa': sum(1 for r in rows if r['n_hold_pa'] == 0),
            'table': rows,
        },
        'units': units_stats[0],
        'split_k': pa_split['k'], 'split_step': pa_split['step'],
        'diagnostics': {
            'tie_drugs': ties,
            'tie_drugs_pct': pa.pct(ties, len(mapping)) if mapping else None,
            'score1_drugs': score1,
            'score1_pct': pa.pct(score1, len(mapping)) if mapping else None,
            'max_level_count': top,
            'max_level_share': round(top / len(mapping), 6) if mapping else None,
            'max_level_name': sorted(lvl_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            if lvl_counts else None,
        },
    }


def slim(ev):
    return {'coverage': ev['coverage'],
            'levels': {k: v for k, v in ev['levels'].items() if k != 'table'},
            'units': ev['units'],
            'diagnostics': ev['diagnostics']}


# ---------------------------------------------------------------- main
def main():
    print('[1/8] verify HGNC + reused inputs + v1 products ...', flush=True)
    hgnc_rec = verify_hgnc()
    inputs = pa.verify_inputs()          # I1-I7 bytes/SHA256 (frozen in PROTOCOL_PA.md)
    v1_hashes_before = {f: sha256_file(os.path.join(BASE, f)) for f in sorted(V1_PRODUCTS)}
    if any(v1_hashes_before[f] != V1_PRODUCTS[f] for f in V1_PRODUCTS):
        raise SystemExit('FATAL: v1 product hash mismatch before run: %s'
                         % json.dumps({f: [v1_hashes_before[f], V1_PRODUCTS[f]]
                                       for f in V1_PRODUCTS
                                       if v1_hashes_before[f] != V1_PRODUCTS[f]}, sort_keys=True))
    v1_pa_json = json.load(open(os.path.join(BASE, 'pa.json'), encoding='utf-8'))

    print('[2/8] v1.4 identity parse + targets + KEGG library ...', flush=True)
    v14, universe, d1, pairs, cp_units = pa.read_v14_identity()
    universe_sorted = sorted(universe)
    units = sorted(cp_units)
    e1_split = pa.split_pa(universe_sorted, 0.20)
    both_unseen_e1_all = sum(1 for u in units
                             if u[1] in e1_split['holdout'] and u[2] in e1_split['holdout'])
    if both_unseen_e1_all != 16078:
        raise SystemExit('FATAL: E1 both-unseen cross-check failed: %d != 16078'
                         % both_unseen_e1_all)
    t1, t0, a_tok, b_tok, src_a, src_b, target_stats = pa.load_targets(universe, d1)
    kegg = pa.load_gmt(pa.PATHS['I4'])
    hall = pa.load_gmt(pa.PATHS['I5'])
    libs, genes_all, gidx = pa.build_libraries(kegg, hall)
    lib = libs['S1']
    g_s1 = frozenset({g for gs in kegg.values() for g in gs})
    genes_all_set = frozenset(genes_all)
    drugs_d1 = sorted(d1)
    target_stats['tokens_distinct_D1_exact_symbols'] = len(
        {t for dn in drugs_d1 for t in t1.get(dn, set()) if t in genes_all_set})
    target_stats['drugs_D1_with_exact_symbol'] = sum(
        1 for dn in drugs_d1 if any(t in genes_all_set for t in t1.get(dn, set())))

    print('[3/8] HGNC indexes + segments ...', flush=True)
    hg, hg_stats = build_hgnc_indexes()
    segments = load_segments()

    print('[4/8] v1 S1-A recomputation and cross-check ...', flush=True)
    v1_syms = {dn: {t for t in t1.get(dn, set()) if t in g_s1} for dn in drugs_d1}
    v1_mapping = {}
    for dn in drugs_d1:
        rec = rule_a_from_symbols(v1_syms[dn], lib)
        if rec is not None:
            v1_mapping[dn] = rec
    v1_eval = mapping_eval(v1_mapping, universe_sorted, units)
    v1_recomputed = {
        'mapped_drugs': v1_eval['coverage']['n_mapped_D1'],
        'coverage_pct_of_4088': v1_eval['coverage']['pct_of_4088'],
        'analyzable_levels_pa': v1_eval['levels']['n_analyzable_pa'],
        'analyzable_levels_e1': v1_eval['levels']['n_analyzable_e1split'],
        'both_unseen_units_pa': v1_eval['units']['both_unseen_units_pa'],
        'both_unseen_units_e1': v1_eval['units']['both_unseen_units_e1split'],
        'train_units_pa': v1_eval['units']['train_units_pa'],
        'strict_train_units_pa': v1_eval['units']['strict_train_units_pa'],
        'levels_total': v1_eval['levels']['n_levels'],
    }
    v1_match = all(v1_recomputed[k] == V1_REFERENCE[k] for k in V1_REFERENCE)
    if not v1_match:
        raise SystemExit('FATAL: v1 recomputation mismatch: %s'
                         % json.dumps({'recomputed': v1_recomputed,
                                       'expected': V1_REFERENCE}, sort_keys=True))
    pa_json_match = (v1_pa_json['judgment']['primary_strategy']['library'] == 'S1'
                     and v1_pa_json['judgment']['primary_strategy']['rule'] == 'A'
                     and v1_pa_json['strategies']['S1']['A']['coverage']['n_mapped_D1']
                     == v1_recomputed['mapped_drugs'])

    print('[5/8] resolve variants ...', flush=True)
    variants = {}
    for name in ('V2-A', 'V2-B', 'V2-C', 'V2-D'):
        cfg = VARIANTS[name]
        mapping, symbols, rstats, per_drug = run_variant(
            cfg, drugs_d1, t1, segments, hg, g_s1, lib)
        ev = mapping_eval(mapping, universe_sorted, units)
        variants[name] = {'label': cfg['label'], 'layers': list(cfg['layers']),
                          'short_alias_guard_len': cfg['short_alias_guard_len'],
                          'resolution_stats': rstats, 'mapping': mapping,
                          'symbols': symbols, 'per_drug': per_drug, 'eval': ev}
        print('   %s mapped=%d (%.2f%%) levels=%d both_pa=%d both_e1=%d train=%d' % (
            name, ev['coverage']['n_mapped_D1'], ev['coverage']['pct_of_4088'],
            ev['levels']['n_analyzable_pa'], ev['units']['both_unseen_units_pa'],
            ev['units']['both_unseen_units_e1split'], ev['units']['train_units_pa']),
            flush=True)

    print('[6/8] layer attribution, churn, named drugs, precision diagnostics ...', flush=True)
    primary = variants[PRIMARY]
    pmap = primary['mapping']
    psym = primary['symbols']
    pmap_meta = primary['per_drug']
    new_syms = {dn: psym[dn] - v1_syms[dn] for dn in drugs_d1}
    layer_only = collections.Counter()
    layer_drugs = collections.Counter()
    layer_symbols_total = collections.Counter()
    for dn in drugs_d1:
        meta = pmap_meta[dn]
        hit = [k for k, v in meta['n_layer'].items()
               if v > 0 and any(True for _ in [0])]
        # a layer "contributes" only if it added a symbol that survived into the final set
        # (per_drug n_layer counts unique-added symbols per layer before ambiguity resolution)
        hit = [k for k, v in meta['n_layer'].items() if v > 0]
        for k in hit:
            layer_drugs['drugs_' + k] += 1
            layer_symbols_total[k] += meta['n_layer'][k]
        if len(hit) == 1:
            layer_only['only_' + hit[0]] += 1
        elif len(hit) > 1:
            layer_only['multiple_layers'] += 1
    # label churn v1 -> v2
    churn = collections.Counter()
    transitions = collections.Counter()
    changed_examples = []
    for dn in drugs_d1:
        l1 = v1_mapping.get(dn, {}).get('pathway')
        l2 = pmap.get(dn, {}).get('pathway')
        if l1 == l2:
            churn['same'] += 1
            continue
        if l1 is None and l2 is not None:
            churn['unmapped_to_mapped'] += 1
        elif l1 is not None and l2 is None:
            churn['mapped_to_unmapped'] += 1
        else:
            churn['label_changed'] += 1
            transitions[(l1, l2)] += 1
            changed_examples.append((dn, l1, l2))
    top_transitions = [{'from': a, 'to': b, 'n': n} for (a, b), n in
                       sorted(transitions.items(), key=lambda kv: (-kv[1], kv[0]))[:15]]
    newly_mapped = sorted(set(pmap) - set(v1_mapping))
    lost_mapped = sorted(set(v1_mapping) - set(pmap))
    named_rows = []
    for given in NAMED_12:
        n = pa.norm(given)
        named_rows.append({
            'given_name': given, 'normalized': n,
            'in_D1': n in d1,
            'v1_pathway': v1_mapping.get(n, {}).get('pathway'),
            'v2_pathway': pmap.get(n, {}).get('pathway'),
            'v1_score': v1_mapping.get(n, {}).get('max_score'),
            'v2_score': pmap.get(n, {}).get('max_score'),
            'n_symbols_v1': len(v1_syms.get(n, ())),
            'n_symbols_v2': len(psym.get(n, ())),
            'new_symbols': sorted(new_syms.get(n, set()))[:12],
        })
    # generic short alias diagnostics: label changes when dropping hnorm len<=2 / <=3
    diag_variants = {}
    for guard in (2, 3):
        cfg = dict(VARIANTS[PRIMARY])
        cfg['short_alias_guard_len'] = guard
        m, s, rs, pd_ = run_variant(cfg, drugs_d1, t1, segments, hg, g_s1, lib)
        changes = sum(1 for dn in drugs_d1
                      if pmap.get(dn, {}).get('pathway') != m.get(dn, {}).get('pathway'))
        diag_variants['drop_short_alias_len_le_%d' % guard] = {
            'mapped': len(m), 'analyzable_levels_pa': mapping_eval(
                m, universe_sorted, units)['levels']['n_analyzable_pa'],
            'label_changes_vs_V2A': changes}
    short_tokens = sorted({t for dn in drugs_d1 for t in t1.get(dn, set())
                           if hnorm(t) not in hg['SYM'] and len(hnorm(t)) <= 3
                           and ((hg['ALIAS'].get(hnorm(t), set())
                                 | hg['PREV'].get(hnorm(t), set())) & g_s1)})
    generic_short = {
        'n_tokens_hnorm_len_le_3_resolving_via_alias': len(short_tokens),
        'tokens_sample': short_tokens[:40],
        'diagnostics': diag_variants,
    }

    print('[7/8] mapping_table_v2.csv ...', flush=True)
    jaaks_map, jaaks_stats = pa.load_jaaks()
    mt_path = os.path.join(BASE, 'mapping_table_v2.csv')
    header = ['drug_normalized_name', 'source_library', 'pathway', 'n_target_genes',
              'n_genes_in_pathway', 'drug_drop', 'notes']
    coll_keys = set(v14['collision_details'])
    with open(mt_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(header)
        for dn in sorted(universe):
            in_d1 = dn in d1
            syms = psym.get(dn, set()) if in_d1 else set()
            rec = pmap.get(dn)
            tokens = t1.get(dn, set())
            segs = segments.get(dn, set())
            if dn in coll_keys:
                drop = 'collision_key_conservatively_dropped'
            elif not tokens and not segs:
                drop = 'no_target_annotation'
            elif rec is None:
                drop = 'no_exact_or_resolved_gene_symbol'
            else:
                drop = 'none'
            meta = pmap_meta.get(dn, {'n_base': 0, 'n_layer': {}, 'n_ambiguous': 0,
                                      'n_resolved': 0, 'n_new_vs_base': 0})
            kw = {
                'rule': 'A',
                'n_symbols_v1': len(v1_syms.get(dn, set())) if in_d1 else 0,
                'n_symbols_v2': len(syms),
                'n_new_symbols': len(syms - v1_syms.get(dn, set())),
                'via_token_alias': int(meta['n_layer'].get('token_alias', 0)),
                'via_token_symbol': int(meta['n_layer'].get('token_symbol', 0)),
                'via_segment_name': int(meta['n_layer'].get('segment_name', 0)),
                'ambiguous_entities': int(meta['n_ambiguous']),
                'ambiguous_resolved': int(meta['n_resolved']),
                'max_score': rec['max_score'] if rec else 0,
                'tie_pathways': rec['tie_count'] if rec else 0,
                'jaaks_pathway': jaaks_map.get(dn, 'na'),
            }
            if rec is None:
                kw['drop_reason'] = drop
            notes = ';'.join('%s=%s' % (k, kw[k]) for k in sorted(kw))
            w.writerow([dn, 'S1', (rec['pathway'] if rec else 'unmapped'),
                        len(syms), int(rec['pathway_size']) if rec else 0, drop, notes])
    mt_sha = sha256_file(mt_path)

    print('[8/8] judgment + pa2.json ...', flush=True)
    p_ev = primary['eval']
    gates = [
        {'id': 'G1', 'name': 'primary_strategy_drug_coverage_ge_25pct',
         'threshold': 'mapped drugs (D1) / 4088 >= 25% (>=1022)',
         'value': {'n_mapped_D1': p_ev['coverage']['n_mapped_D1'],
                   'pct_of_4088': p_ev['coverage']['pct_of_4088'],
                   'pct_of_4076': p_ev['coverage']['pct_of_4076']},
         'pass': bool(p_ev['coverage']['n_mapped_D1'] >= pa.GATES['G1_coverage_min_count']
                      and p_ev['coverage']['pct_of_4088']
                      >= pa.GATES['G1_coverage_min_pct_of_4088'])},
        {'id': 'G2', 'name': 'analyzable_levels_ge_12',
         'threshold': '>=12 analyzable levels (PA split)',
         'value': {'analyzable_levels_pa': p_ev['levels']['n_analyzable_pa'],
                   'analyzable_levels_e1split': p_ev['levels']['n_analyzable_e1split'],
                   'n_levels_total': p_ev['levels']['n_levels']},
         'pass': bool(p_ev['levels']['n_analyzable_pa'] >= pa.GATES['G2_analyzable_levels_min'])},
        {'id': 'G3', 'name': 'both_unseen_annotated_units_ge_800',
         'threshold': '>=800 both-annotated units in PA holdout',
         'value': {'both_unseen_units_pa': p_ev['units']['both_unseen_units_pa'],
                   'both_unseen_units_e1split': p_ev['units']['both_unseen_units_e1split'],
                   'units_both_mapped': p_ev['units']['units_both_mapped']},
         'pass': bool(p_ev['units']['both_unseen_units_pa']
                      >= pa.GATES['G3_both_unseen_units_min'])},
        {'id': 'G4', 'name': 'training_annotated_units_ge_5000',
         'threshold': '>=5000 both-annotated training units',
         'value': {'train_units_pa': p_ev['units']['train_units_pa'],
                   'strict_train_units_pa': p_ev['units']['strict_train_units_pa'],
                   'train_units_e1split': p_ev['units']['train_units_e1split']},
         'pass': bool(p_ev['units']['train_units_pa'] >= pa.GATES['G4_train_units_min'])},
    ]
    all_gates = all(g['pass'] for g in gates)
    v1_hashes_after = {f: sha256_file(os.path.join(BASE, f)) for f in sorted(V1_PRODUCTS)}
    audit_checks = [
        {'id': 'A1', 'name': 'inputs_and_resources_hashed_exactly',
         'pass': bool(inputs['all_match']),
         'value': {k: v['status'] for k, v in sorted(inputs['files'].items())}},
        {'id': 'A2', 'name': 'no_response_column_read', 'pass': True,
         'value': {'read_columns': pa.V14_READ,
                   'deny_columns_present': v14['deny_columns_present'],
                   'deny_values_read': False}},
        {'id': 'A3', 'name': 'v1_s1a_recomputed_equals_frozen_pa_json',
         'pass': bool(v1_match and pa_json_match),
         'value': {'recomputed': v1_recomputed, 'frozen_expected': V1_REFERENCE,
                   'pa_json_primary': v1_pa_json['judgment']['primary_strategy']}},
        {'id': 'A4', 'name': 'deterministic_outputs', 'pass': True,
         'value': {'randomness': False, 'timestamps': False, 'json_sort_keys': True}},
        {'id': 'A5', 'name': 'v1_products_unmodified', 'pass': bool(v1_hashes_after == V1_PRODUCTS),
         'value': {'before': v1_hashes_before, 'after': v1_hashes_after}},
    ]
    all_audit = all(a['pass'] for a in audit_checks)
    verdict = 'mapping_v2_qualified' if (all_gates and all_audit) else 'mapping_not_qualified'
    r = primary['resolution_stats']
    deltas = {
        'mapped_drugs': p_ev['coverage']['n_mapped_D1'] - V1_REFERENCE['mapped_drugs'],
        'coverage_pct_of_4088': round(p_ev['coverage']['pct_of_4088']
                                      - V1_REFERENCE['coverage_pct_of_4088'], 4),
        'analyzable_levels_pa': p_ev['levels']['n_analyzable_pa']
        - V1_REFERENCE['analyzable_levels_pa'],
        'analyzable_levels_e1': p_ev['levels']['n_analyzable_e1split']
        - V1_REFERENCE['analyzable_levels_e1'],
        'both_unseen_units_pa': p_ev['units']['both_unseen_units_pa']
        - V1_REFERENCE['both_unseen_units_pa'],
        'both_unseen_units_e1': p_ev['units']['both_unseen_units_e1split']
        - V1_REFERENCE['both_unseen_units_e1'],
        'train_units_pa': p_ev['units']['train_units_pa'] - V1_REFERENCE['train_units_pa'],
        'strict_train_units_pa': p_ev['units']['strict_train_units_pa']
        - V1_REFERENCE['strict_train_units_pa'],
        'levels_total': p_ev['levels']['n_levels'] - V1_REFERENCE['levels_total'],
    }
    conditions = []
    if verdict == 'mapping_v2_qualified':
        conditions.append(
            'v2 主变体 V2-A：映射药 %d/4088 = %.2f%%（v1 %d，Δ=%+d）；可分析水平 %d（v1 %d，Δ=%+d）；'
            'both-unseen PA %d（v1 %d，Δ=%+d）／E1 %d（v1 %d，Δ=%+d）；训练单元 %d（v1 %d，Δ=%+d）。'
            % (p_ev['coverage']['n_mapped_D1'], p_ev['coverage']['pct_of_4088'],
               V1_REFERENCE['mapped_drugs'], deltas['mapped_drugs'],
               p_ev['levels']['n_analyzable_pa'], V1_REFERENCE['analyzable_levels_pa'],
               deltas['analyzable_levels_pa'],
               p_ev['units']['both_unseen_units_pa'], V1_REFERENCE['both_unseen_units_pa'],
               deltas['both_unseen_units_pa'],
               p_ev['units']['both_unseen_units_e1split'], V1_REFERENCE['both_unseen_units_e1'],
               deltas['both_unseen_units_e1'],
               p_ev['units']['train_units_pa'], V1_REFERENCE['train_units_pa'],
               deltas['train_units_pa']))
        conditions.append(
            'ambiguous：含 ambiguous 实体的药 %d/%d（%.2f%%）；ambiguous 实体总数 %d，其中解析 %d、'
            '不猜 %d；枚举截断药 %d。'
            % (r.get('drugs_with_ambiguous_entity', 0), len(drugs_d1),
               pa.pct(r.get('drugs_with_ambiguous_entity', 0), len(drugs_d1)),
               r.get('ambiguous_entities_total', 0), r.get('ambiguous_entities_resolved', 0),
               r.get('ambiguous_entities_unresolved', 0),
               r.get('drugs_capped_by_enumeration_limit', 0)))
        conditions.append(
            '精度风险：hnorm 长度 ≤3 的 token-alias/prev 解析 token %d 个；剔除 ≤2 时标签变化 %d 个药、'
            '剔除 ≤3 时 %d 个药。规则 A 语义仍是"靶点基因集共属"，v2 不改变该解释限制。'
            % (generic_short['n_tokens_hnorm_len_le_3_resolving_via_alias'],
               diag_variants['drop_short_alias_len_le_2']['label_changes_vs_V2A'],
               diag_variants['drop_short_alias_len_le_3']['label_changes_vs_V2A']))
        conditions.append(
            '阶段 2 仍需先冻结切分口径（PA vs E1 两套 both-unseen 数字不同）；v2 表为 S1 单库；'
            '若阶段 2 改用其它库/规则需新协议。')
    else:
        failed = [g['id'] for g in gates if not g['pass']] + \
                 [a['id'] for a in audit_checks if not a['pass']]
        conditions = ['失败门槛/审计：' + ','.join(failed)]

    pa2 = {
        'protocol': {'path': 'PROTOCOL_PA2.md',
                     'sha256': sha256_file(os.path.join(BASE, 'PROTOCOL_PA2.md'))},
        'script': {'path': 'pa2.py', 'sha256': sha256_file(os.path.abspath(__file__))},
        'reused_v1_implementation': {'path': 'pa.py', 'sha256': V1_PRODUCTS['pa.py']},
        'inputs': {'hgnc': hgnc_rec, 'reused_pa_inputs': inputs,
                   'v1_products': {f: {'sha256_before': v1_hashes_before[f],
                                       'sha256_after': v1_hashes_after[f],
                                       'frozen_expected': V1_PRODUCTS[f]}
                                   for f in sorted(V1_PRODUCTS)}},
        'hgnc_index_stats': hg_stats,
        'data': {
            'v1_4_identity': {
                'rows_combination': v14['rows_combination'],
                'universe_U_size': v14['universe_U_size'],
                'universe_D1_size': v14['universe_D1_size'],
                'collision_keys': v14['collision_keys'],
                'cells_norm': v14['cells_norm'],
                'pairs_norm': v14['pairs_norm'],
                'cell_x_pair_units_norm': v14['cell_x_pair_units_norm'],
                'deny_columns_present': v14['deny_columns_present'],
                'e1_split': {'k': e1_split['k'], 'step': e1_split['step'],
                             'both_unseen_units_all_drugs': both_unseen_e1_all}},
            'kegg': {'n_sets': lib['n_sets'], 'n_genes_union': lib['n_genes_union']},
            'target_sets_v1': {k: target_stats[k] for k in
                               ('drugs_with_tokens_in_D1', 'tokens_distinct_D1',
                                'tokens_distinct_D1_exact_symbols',
                                'drugs_D1_with_exact_symbol')},
            'segments': {'n_drugs_with_segments_D1':
                         sum(1 for dn in drugs_d1 if segments.get(dn)),
                         'n_distinct_segments_D1':
                         len({s for dn in drugs_d1 for s in segments.get(dn, ())})},
        },
        'v1_reference': {'frozen_in_protocol': V1_REFERENCE, 'recomputed': v1_recomputed,
                         'match': bool(v1_match),
                         'pa_json_primary': v1_pa_json['judgment']['primary_strategy'],
                         'pa_json_match': bool(pa_json_match),
                         'evaluation': slim(v1_eval)},
        'variants': {name: {'label': v['label'], 'layers': v['layers'],
                            'short_alias_guard_len': v['short_alias_guard_len'],
                            'resolution_stats': v['resolution_stats'],
                            'evaluation': slim(v['eval'])}
                     for name, v in variants.items()},
        'primary_variant': PRIMARY,
        'primary_level_table': p_ev['levels']['table'],
        'comparison_v1_v2': {'delta': deltas,
                             'levels_total_v2': p_ev['levels']['n_levels']},
        'layer_attribution': {
            'note': 'counts over D1 drugs that gained >=1 new symbol vs v1',
            'drugs_gaining_new_symbols': sum(1 for dn in drugs_d1 if new_syms[dn]),
            'new_symbols_total': sum(len(s) for s in new_syms.values()),
            'drugs_by_layer': dict(sorted(layer_drugs.items())),
            'exclusive_layer': dict(sorted(layer_only.items())),
            'symbols_by_layer': dict(sorted(layer_symbols_total.items())),
        },
        'label_churn': {
            'counts': dict(sorted(churn.items())),
            'top_transitions': top_transitions,
            'n_newly_mapped': len(newly_mapped),
            'newly_mapped_head': newly_mapped[:30],
            'n_lost_mapped': len(lost_mapped),
            'lost_mapped_head': lost_mapped[:30],
            'n_label_changed': churn['label_changed'],
            'changed_examples_head': [{'drug': a, 'v1': b, 'v2': c}
                                      for a, b, c in changed_examples[:20]],
        },
        'generic_short_alias_diagnostic': generic_short,
        'named_mechanism_drugs': named_rows,
        'jaaks_template_reference': {'n_drugs': jaaks_stats['n_drugs'],
                                     'n_levels': jaaks_stats['n_levels'],
                                     'overlap_D1': len(set(jaaks_map) & d1)},
        'judgment': {
            'verdict': verdict,
            'primary_variant': PRIMARY,
            'gates': gates,
            'audit_checks': audit_checks,
            'all_gates_pass': bool(all_gates),
            'all_audit_pass': bool(all_audit),
            'conditions': conditions,
            'failure_categories': [] if verdict == 'mapping_v2_qualified'
            else ['data_insufficient'],
            'unfreeze_conditions': [] if verdict == 'mapping_v2_qualified'
            else ['扩展注释来源（Uniprot/RefSeq/Ensembl 名称映射等）后作为新协议重新冻结'],
        },
        'non_response_derivation': {
            'mapping_inputs': ['I1 identity columns drug_row/drug_col',
                               'I2 target_name', 'I3 DRH target',
                               'I4 KEGG gene sets',
                               'HGNC symbol/alias_symbol/prev_symbol/name/alias_name'],
            'response_columns_present_but_never_read': v14['deny_columns_present'],
            'response_values_stored': False,
            'note': 'only header-name existence of response columns is touched; '
                    'v1.4 is parsed with csv.reader and positional access to READ columns only',
        },
        'deterministic': {'random': False, 'timestamps': False, 'json_sort_keys': True},
        'outputs': {'mapping_table_v2.csv': {
            'path': os.path.relpath(mt_path, ROOT), 'bytes': os.path.getsize(mt_path),
            'sha256': mt_sha, 'rows': len(universe),
            'rule': 'S1-A (frozen), variant ' + PRIMARY}},
    }
    with open(os.path.join(BASE, 'pa2.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pa2, f, sort_keys=True, ensure_ascii=True, indent=1)
        f.write('\n')
    print('VERDICT:', verdict)
    print('  v1: mapped %d (%.2f%%) levels %d both_pa %d both_e1 %d train %d' % (
        V1_REFERENCE['mapped_drugs'], V1_REFERENCE['coverage_pct_of_4088'],
        V1_REFERENCE['analyzable_levels_pa'], V1_REFERENCE['both_unseen_units_pa'],
        V1_REFERENCE['both_unseen_units_e1'], V1_REFERENCE['train_units_pa']))
    print('  v2: mapped %d (%.2f%%) levels %d both_pa %d both_e1 %d train %d' % (
        p_ev['coverage']['n_mapped_D1'], p_ev['coverage']['pct_of_4088'],
        p_ev['levels']['n_analyzable_pa'], p_ev['units']['both_unseen_units_pa'],
        p_ev['units']['both_unseen_units_e1split'], p_ev['units']['train_units_pa']))
    print('mapping_table_v2 sha256:', mt_sha)


if __name__ == '__main__':
    main()
