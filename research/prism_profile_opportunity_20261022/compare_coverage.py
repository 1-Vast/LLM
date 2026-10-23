"""Compare sealed mask counters after both independent real executions."""
import json

from prepare import LOG, sha, write


def main():
    root_path = LOG / 'COVERAGE_RESULT.json'
    independent_path = LOG / 'skeptic/INDEPENDENT_COVERAGE_RESULT.json'
    root = json.loads(root_path.read_text(encoding='utf-8'))
    independent = json.loads(independent_path.read_text(encoding='utf-8'))
    checks, mismatches = 0, []

    def compare(name, first, second):
        nonlocal checks
        if isinstance(first, dict) and isinstance(second, dict):
            compare(name + '/keys', sorted(first), sorted(second))
            for key in first.keys() & second.keys():
                compare(name + '/' + key, first[key], second[key])
        else:
            checks += 1
            if first != second:
                mismatches.append({'name': name, 'root': first, 'independent': second})

    for key in ('status', 'passed', 'gates', 'counts', 'test_plates', 'qualified_ids',
                'test_minimum_at_70_percent', 'group_denominators', 'total_finite', 'total_converted_slots'):
        compare(key, root[key], independent[key])
    compare('details', {row['core']: {k: v for k, v in row.items() if k != 'core'} for row in root['details']},
            independent['details'])
    write(LOG / 'INDEPENDENT_COMPARISON.json', {'passed': not mismatches, 'checks': checks,
          'mismatches': mismatches, 'root_sha256': sha(root_path), 'independent_sha256': sha(independent_path),
          'type': 'Exact integers/identities; independent raw finite-counter implementation, no root imports.'})
    print(json.dumps({'passed': not mismatches, 'checks': checks, 'mismatches': len(mismatches)}))
    if mismatches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
