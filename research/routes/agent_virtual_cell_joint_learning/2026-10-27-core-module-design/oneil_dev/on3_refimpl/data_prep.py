"""ON3 data prep: metadata-only unit building + frozen mask + reconstruction audit.

Reads ONLY identity/dose columns and viability NULLNESS (no response values parsed).
Outputs on3_refimpl/reconstruction_audit.json with target30 and per-fold denominators.
"""
from __future__ import annotations

import hashlib
import json
import os
import unicodedata

import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
OUT = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on3_refimpl')
COMP = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                    '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
SEED = '20261130'
FOLDS = {'0': ['a2058', 'colo320dm', 'kpl1', 'ncih23', 'pa1', 'uacc62'],
         '1': ['a2780', 'dld1', 'lncap', 'ncih460', 'rpmi7951', 'uwb1289'],
         '2': ['a375', 'efm192b', 'msto', 'ncih520', 'skmel30', 'uwb1289brca1'],
         '3': ['a427', 'es2', 'ncih1650', 'ov90', 'skmes1', 'vcap'],
         '4': ['caov3', 'ht144', 'ncih2122', 'ovcar3', 'skov3', 'zr751']}


def norm(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def reconstruction_audit(cells, partners, a, ap, masked):
    dsu = DSU()
    for c, p, x, y, m in zip(cells, partners, a, ap, masked):
        if m:
            continue
        dsu.union((c, tuple(sorted((x, p)))), (c, tuple(sorted((y, p)))))
    total = int(sum(masked))
    recon = 0
    for c, p, x, y, m in zip(cells, partners, a, ap, masked):
        if not m:
            continue
        n1 = (c, tuple(sorted((x, p))))
        n2 = (c, tuple(sorted((y, p))))
        if n1 in dsu.p and n2 in dsu.p and dsu.find(n1) == dsu.find(n2):
            recon += 1
    return total, recon


def main():
    d = pd.read_excel(COMP, sheet_name='combination response',
                      usecols=['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)',
                               'drugB_name', 'drugB Conc (µM)',
                               'viability1', 'viability2', 'viability3', 'viability4'])
    for c in ('cell_line', 'drugA_name', 'drugB_name'):
        d[c] = d[c].astype(str).map(norm)
    d['batch'] = d.BatchID.astype(int)
    d['cc'] = d[['viability1', 'viability2', 'viability3', 'viability4']].notna().all(axis=1)
    d = d.drop(columns=['viability1', 'viability2', 'viability3', 'viability4'])
    d = d[d.cc].dropna(subset=['cell_line', 'drugA_name', 'drugB_name'])
    d = d[d.batch == 1]
    jc = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME'], low_memory=False)
    jcells = {norm(x) for x in jc.CELL_LINE_NAME.unique()}
    target = sorted(set(d.cell_line) - jcells)
    tgt = set(target)
    drugs = sorted(set(d.drugA_name) | set(d.drugB_name))
    k = int(np.ceil(0.20 * len(drugs)))
    ranked = sorted(drugs, key=lambda g: hashlib.sha256(("ON3v0.2|M|%s|%s" % (SEED, g)).encode()).hexdigest())
    M = sorted(ranked[:k])
    # complete member contexts -> legal units
    ctx_cols = ['cell_line', 'partner', 'prole']
    rec = pd.concat([
        pd.DataFrame({'cell': d.cell_line, 'partner': d.drugB_name, 'prole': 'b', 'member': d.drugA_name}),
        pd.DataFrame({'cell': d.cell_line, 'partner': d.drugA_name, 'prole': 'a', 'member': d.drugB_name}),
    ], ignore_index=True)
    mset = rec.groupby(['cell', 'partner', 'prole', 'member']).size().reset_index(name='n')
    cm = mset[mset.n == 16]
    units = []
    for (cell, partner, prole), grp in cm.groupby(['cell', 'partner', 'prole']):
        ml = sorted(grp.member)
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                units.append((cell, partner, prole, ml[i], ml[j]))
    U = pd.DataFrame(units, columns=['cell', 'partner', 'prole', 'a', 'ap'])
    U = U[U.cell.isin(tgt)].copy()
    S = set(M)
    U['masked'] = [bool((p in S) or (x in S) or (y in S)) for p, x, y in zip(U.partner, U.a, U.ap)]

    def audit(frame):
        total, recon = reconstruction_audit(frame.cell.tolist(), frame.partner.tolist(),
                                            frame.a.tolist(), frame.ap.tolist(), frame.masked.tolist())
        return {'masked_units': total, 'reconstructable_units': recon,
                'rate': (recon / total) if total else None}

    out = {
        'generated_by': 'on3_refimpl/data_prep.py (metadata + viability nullness only; NO response values)',
        'inputs': {'workbook': {'path_rel': 'data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls',
                                'sha256': sha(COMP)},
                   'jaaks_cellnames': {'path_rel': 'data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv',
                                       'sha256': sha(JAAKS)}},
        'seed': SEED, 'masked_drugs': M, 'n_masked_drugs': len(M),
        'target_cells': target, 'target_n_units': int(len(U)),
        'target_masked_units': int(U.masked.sum()),
        'target_audit': audit(U),
        'folds': {},
    }
    for f, cells in FOLDS.items():
        sub = U[U.cell.isin(cells)]
        out['folds'][f] = {'cells': cells, 'units': int(len(sub)),
                           'masked_units': int(sub.masked.sum()),
                           'unmasked_units': int((~sub.masked).sum()),
                           'audit': audit(sub)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'reconstruction_audit.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('target audit', out['target_audit'])
    for f in FOLDS:
        print('fold', f, out['folds'][f]['masked_units'], out['folds'][f]['audit']['reconstructable_units'])
    print('wrote', os.path.join(OUT, 'reconstruction_audit.json'))


if __name__ == '__main__':
    main()
