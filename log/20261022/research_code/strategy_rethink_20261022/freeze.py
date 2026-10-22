"""Hash final protocol/code/ID manifest before the first real scalar fit."""
from screen import OUT, ROOT, SOURCE, sha, write


paths = list((ROOT / 'research/strategy_rethink_20261022').glob('*.py'))
paths += [OUT / name for name in ('PROTOCOL.md', 'EPISODE_MANIFEST.json', 'SCHEMA_AUDIT.json',
                                  'BOUNDARY_CHECKS.json', 'PREFREEZE_REVIEW.md')]
write('FREEZE.json', {'files': [{'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
                              for path in sorted(paths)],
                      'route_input_sha256': sha(SOURCE), 'real_scalar_fits_before_freeze': 0,
                      'scope': 'conditional_exposed_background_noninnovative'})
print('Protocol, code, exact IDs and input digest frozen before real fitting.')
