"""Annotate frozen nominations; no fitting, new selection or lung value decoding."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT/'log/20261023/interaction_error_diagnostic'
OUT = ROOT/'log/20261023/rank_reversal_mechanism'
DATA = ROOT/'log/20261023/update_law_search/task/interaction_supplement.body'
DEV = ['MCF7', 'MDAMB231', 'MCF10A', 'CAL27', 'CAL33']
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_q(path, pairs):
    with zipfile.ZipFile(path) as archive:
        shared = [''.join(s.itertext()) for s in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet2.xml'))

    def value(cell):
        v = cell.find('m:v', NS)
        if v is None:
            return ''.join(cell.itertext())
        return shared[int(v.text)] if cell.attrib.get('t') == 's' else v.text

    rows = sheet.findall('m:sheetData/m:row', NS)
    header = {''.join(c for c in cell.attrib['r'] if c.isalpha()): value(cell) for cell in rows[0]}
    cols = {col: DEV.index(name) for col, name in header.items() if name in DEV}
    assert len(cols) == 5 and not {'H', 'I'} & cols.keys()
    wanted = set(pairs)
    grouped, ordered = {}, set()
    for row in rows[1:]:
        cells = {''.join(c for c in cell.attrib['r'] if c.isalpha()): cell for cell in row}
        key = (value(cells['A']), value(cells['B']))
        assert key not in ordered
        ordered.add(key)
        pair = tuple(sorted(key))
        if pair not in wanted:
            continue
        q = np.full(5, np.nan)
        for col, j in cols.items():
            cell = cells.get(col)
            if cell is None or cell.attrib.get('t') == 'e':
                continue
            text = value(cell)
            if not text:
                continue
            try:
                q[j] = float(text)
            except ValueError:
                assert text.lower() in ('nan', 'na', 'n/a', 'none'), text
        finite = np.isfinite(q)
        assert np.all((q[finite] >= 0) & (q[finite] <= 1)), pair
        grouped.setdefault(pair, []).append(q)
    assert wanted == set(grouped)
    maximum, minimum, incomplete, mirrors, mismatch = [], [], [], 0, 0
    for pair in pairs:
        values = np.array(grouped[pair])
        assert len(values) in (1, 2)
        complete = np.isfinite(values).all(axis=0)
        low, high = np.full(5, np.nan), np.full(5, np.nan)
        for j in range(5):
            finite = values[:, j][np.isfinite(values[:, j])]
            if len(finite):
                low[j] = finite.min()
            if complete[j]:
                high[j] = finite.max()
        minimum.append(low)
        maximum.append(high)
        incomplete.append(~complete)
        if len(values) == 2:
            mirrors += 1
            mismatch += int(not np.allclose(values[0], values[1], rtol=0, atol=1e-10, equal_nan=True))
    return np.array(maximum), np.array(minimum), np.array(incomplete), dict(
        eligible=len(pairs), mirrored_groups=mirrors, mirrored_q_disagreement=mismatch,
        incomplete_cells=int(np.sum(incomplete)), parsed_columns=DEV,
        exact_point_one_orientation_cells=sum(int(np.sum(np.array(v) == .1)) for v in grouped.values()),
        unparsed_columns=['A549', 'A427'], source_sheet='cell-line-fdrs')


def counts(indices, y, q):
    known = np.isfinite(q[indices])
    supported = (y[indices] < 0) & known & (q[indices] <= .1)
    return dict(n=len(indices), supported_negative=int(supported.sum()),
                known_q=int(known.sum()), q_supported=int((known & (q[indices] <= .1)).sum()),
                unknown=int((~known).sum()))


def main():
    begin = time.perf_counter()
    assert not (OUT/'FDR_ANNOTATION.json').exists()
    assert sha(DATA) == '4a10d978247ebc5009284ca95c7c59c096530f502638932823db17093d842230'
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), OUT/'PLAN.md',
                PRIOR/'RESULTS.json', PRIOR/'PREDICTIONS.npz', PRIOR/'PAIR_IDS.json']}
    freeze = OUT/'ANNOTATION_FREEZE.json'
    assert not freeze.exists()
    freeze.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), files=bindings,
                                     scope='Before any new FDR value parsing'), indent=2), encoding='utf-8')
    pairs = [tuple(p) for p in json.loads((PRIOR/'PAIR_IDS.json').read_text())]
    results = json.loads((PRIOR/'RESULTS.json').read_text())
    saved = np.load(PRIOR/'PREDICTIONS.npz', allow_pickle=False)
    y = saved['development_scores']
    high, low, incomplete, metadata = read_q(DATA, pairs)
    np.savez_compressed(OUT/'FDR_DEVELOPMENT.npz', maximum_q=high, minimum_q=low,
                        incomplete=incomplete)
    records = []
    for case in results['records']:
        name, salt, budget = case['context'], case['salt'], case['budget']
        j = DEV.index(name)
        prefix = f'{name}_{salt}_{budget}'
        query = saved[prefix+'_query']
        methods = ['source_mean', 'calibration', 'score_direct', 'identity_ordinary', 'gi_oracle']
        annotations = {}
        for method in methods:
            prediction = y[query, j] if method == 'gi_oracle' else saved[prefix+'_'+method]
            nominations = query[np.argsort(prediction, kind='stable')[:20]]
            annotations[method] = dict(pair_indices=nominations.tolist(),
                                       conservative=counts(nominations, y[:, j], high[:, j]),
                                       optimistic_sensitivity=counts(nominations, y[:, j], low[:, j]))
        assert annotations['source_mean']['pair_indices'] == annotations['calibration']['pair_indices']
        records.append(dict(context=name, salt=salt, budget=budget, annotations=annotations))
    contrasts = []
    for a in range(5):
        for b in range(a+1, 5):
            contrast = dict(context_a=DEV[a], context_b=DEV[b])
            for name, q in [('conservative', high), ('optimistic_sensitivity', low)]:
                supported = np.isfinite(q[:, a]) & np.isfinite(q[:, b]) & (q[:, a] <= .1) & (q[:, b] <= .1)
                opposite = supported & (((y[:, a] < 0) & (y[:, b] > 0)) | ((y[:, a] > 0) & (y[:, b] < 0)))
                contrast[name] = dict(both_q_supported=int(supported.sum()),
                                      opposite_sign=int(opposite.sum()),
                                      negative_a_positive_b=int((opposite & (y[:, a] < 0)).sum()),
                                      positive_a_negative_b=int((opposite & (y[:, a] > 0)).sum()))
            contrasts.append(contrast)
    panel = {DEV[j]: {name: counts(np.arange(len(pairs)), y[:, j], q[:, j])
                      for name, q in [('conservative', high), ('optimistic_sensitivity', low)]} for j in range(5)}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), metadata=metadata, panel=panel,
                  records=records, contrasts=contrasts, bindings=bindings,
                  q_sha256=sha(OUT/'FDR_DEVELOPMENT.npz'), seconds=time.perf_counter()-begin,
                  scope='Fixed prediction annotation only; not complete SL calls, cross-context tests, retraining or model selection',
                  goal='ACTIVE / NOT_ACHIEVED')
    (OUT/'FDR_ANNOTATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(metadata=metadata, panel=panel, contrasts=contrasts)))


if __name__ == '__main__':
    main()
