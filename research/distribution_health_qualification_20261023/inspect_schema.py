"""Try schema-only SQLite reading from retained prefix; never query cell rows."""
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
DATA_SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'
LOG_OUT = ROOT / 'log/20261023/distribution_health_qualification/source'

if __name__ == '__main__':
    result = {'scope': 'Schema query on prefix; no cell/health data SELECT'}
    try:
        uri = (DATA_SOURCE / 'sqlite_prefix.body').as_uri() + '?mode=ro&immutable=1'
        with sqlite3.connect(uri, uri=True) as connection:
            rows = connection.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_master').fetchall()
        result.update(status='SCHEMA_READ', objects=[dict(zip(
            ('type', 'name', 'tbl_name', 'rootpage', 'sql'), row)) for row in rows])
    except sqlite3.DatabaseError as error:
        result.update(status='PREFIX_SCHEMA_NOT_READABLE', error=str(error))
    (LOG_OUT / 'SCHEMA_INSPECTION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'objects'}, indent=2))
    for obj in result.get('objects', []):
        print(obj['type'], obj['name'], 'rootpage', obj['rootpage'], 'sql_chars', len(obj['sql'] or ''))
