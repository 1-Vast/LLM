"""Describe frozen mask failure without choosing another panel or threshold."""
import json

from prepare import LOG, sha, write


def main():
    result_path = LOG / 'COVERAGE_RESULT.json'
    result = json.loads(result_path.read_text(encoding='utf-8'))
    manifest = json.loads((LOG / 'MANIFEST_v2.json').read_text(encoding='utf-8'))
    details = {row['core']: row for row in result['details']}
    groups = result['group_denominators']
    parts = {}
    for part, ids in manifest['retained_ids'].items():
        parts[part] = {'candidates': len(ids), 'qualified': len(result['qualified_ids'][part]),
            'per_requirement_passes': {group: sum(5 * details[core]['finite_counts'][group] >= 4 * nominal for core in ids)
                                       for group, nominal in groups.items()},
            'finite_fraction_by_requirement': {group: sum(details[core]['finite_counts'][group] for core in ids) / (len(ids) * nominal)
                                                for group, nominal in groups.items()},
            'compounds_with_any_zero_audit_pool': {rep: sum(any(count == 0 for count in details[core]['finite_by_pool'][rep].values())
                                                         for core in ids) for rep in ('X2', 'X3')}}
    description = {'scope': 'Post-gate finite-mask description only; no alternate threshold/pool/split search or response statistics.',
                   'source_result_sha256': sha(result_path), 'parts': parts, 'test_plates': result['test_plates'],
                   'logical_bundle_accesses_per_execution': 39178, 'numeric_to_bool_conversions_per_execution': result['total_converted_slots']}
    write(LOG / 'MASK_DESCRIPTION.json', description)
    print(json.dumps(description))


if __name__ == '__main__':
    main()
