"""Export only frozen development rows; Arrow may decode the shared row group."""
import hashlib
import json
from pathlib import Path
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/emerald_functional_rule'


def permitted(rows, plan):
    return all(r['cell_line'] in plan['development'] and r['condition'] in plan['conditions']
               for r in rows)


if __name__ == '__main__':
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for name, digest in freeze['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    plan = json.loads((OUT / 'IDENTITY_PLAN.json').read_text())
    assert set(plan['development']).isdisjoint(plan['reserve'])
    target = OUT / 'DEVELOPMENT_ROWS.json'
    assert not target.exists()
    source = ROOT / 'log/20261023/dose_update_qualification/summary_statistics.parquet'
    table = ds.dataset(source, format='parquet').to_table(
        columns=['cell_line', 'condition', 'growth_rate'], filter=(
            ds.field('cell_line').isin(plan['development']) &
            ds.field('condition').isin(plan['conditions'])))
    rows = table.to_pylist()
    assert permitted(rows, plan)
    target.write_text(json.dumps(rows), encoding='utf-8')
    (OUT / 'EXPORT_RECEIPT.json').write_text(json.dumps(dict(
        rows=len(rows), contexts=len({r['cell_line'] for r in rows}),
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(), reserve_exported=False,
        limitation='Shared row group may internally decode reserve; no reserve rows exported.'
    ), indent=2), encoding='utf-8')
