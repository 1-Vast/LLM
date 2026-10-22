"""Post-exposure JSON-only identity summary and nonfinite exposure accounting."""
from collections import Counter
import json
import re

import redirect_followup as follow
import source_schema as source

NONFINITE = re.compile(r'(?i)^[+−-]?(?:inf(?:inity)?|nan)$')


def main():
    path = follow.OUT / 'SCHEMA_AND_STRING_IDENTITIES.json'
    before = source.sha(path)
    result = json.loads(path.read_text(encoding='utf-8'))
    exposed = []
    summaries = []
    for sheet in result['sheets']:
        for cell in sheet['string_schema_identity_cells']:
            if 'text' in cell and NONFINITE.fullmatch(cell['text'].strip()):
                exposed.append({'sheet': sheet['sheet_name'], 'coordinate': cell['coordinate']})
                cell.pop('text')
                cell.pop('exposure', None)
                cell['withheld'] = 'postexposure_nonfinite_numeric_string'
        text = {c['coordinate']: c['text'] for c in sheet['string_schema_identity_cells'] if 'text' in c}
        summaries.append({'sheet_name': sheet['sheet_name'], 'dimension': sheet['declared_dimension'],
            'cell_type_counts': sheet['cell_type_counts'], 'text_cells_count': len(text)})
    source.write_json(follow.OUT / 'SAFE_WORKING_SCHEMA.json', result)
    source.write_json(follow.OUT / 'NONFINITE_EXPOSURE.json', {'scope': 'ALREADY_EXPOSED_NONFINITE_STRING_COORDINATES',
        'count': len(exposed), 'coordinates': exposed, 'original_projection_unchanged': source.sha(path) == before,
        'note': 'Post-exposure filtering does not undo prior exposure; no source values re-opened.'})
    source.write_json(follow.OUT / 'SHEET_INVENTORY.json', summaries)
    output = {'sheet_inventory': summaries, 'nonfinite_exposed_cells': len(exposed), 'selected_string_schema': []}
    for sheet in result['sheets']:
        if sheet['sheet_name'] in {'Fig1B', 'Fig3BC', 'Fig4B', 'Fig4C'}:
            output['selected_string_schema'].append({'sheet_name': sheet['sheet_name'],
                'strings': [c for c in sheet['string_schema_identity_cells'] if 'text' in c]})
    source.write_json(follow.OUT / 'SELECTED_IDENTITY_SCHEMA.json', output)
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
