"""Post-run recomputation of eight S0 feedback values; never rerun the screen."""
import hashlib
import json
import time

import screen


def ids_hash(compounds):
    payload = json.dumps(compounds, separators=(',', ':')).encode()
    return hashlib.sha256(payload).hexdigest()


def main():
    started = time.perf_counter()
    screen.check_freeze()
    output = screen.OUT / 'S0_FEEDBACK_REPLAY.json'
    assert not output.exists(), 'postrun audit output must not be overwritten'
    original_deployments = screen.OUT / 'DEPLOYMENTS.json'
    before = screen.sha(original_deployments)
    manifest = json.loads((screen.OUT / 'EPISODE_MANIFEST.json').read_text())
    episodes = manifest['episodes']['later']
    deployments = json.loads(original_deployments.read_text())
    allowed = [comp for episode in episodes for split in ('calibration', 'development')
               for comp in episode[split]]
    # The legacy NPZ loader decodes entire arrays before selecting these approved rows.
    # Terminal slices are never returned to fitting, proposal, selection or scoring.
    pack = screen.load_pack(allowed)
    feedback, records = {}, []
    fit_cpu = 0.
    route_regressions = 0
    for episode in episodes:
        cal = screen.subset(pack, episode['calibration'])
        dev = screen.subset(pack, episode['development'])
        cpu_started = time.process_time()
        solver = screen.fit_solver(cal, screen.S0)
        value = screen.score(dev, screen.predict(dev, solver))[0]
        fit_cpu += time.process_time() - cpu_started
        route_regressions += sum(model is not None for model in solver['models'])
        feedback[episode['id']] = value
        records.append({
            'episode': episode['id'], 'program': screen.S0,
            'calibration_ids': episode['calibration'],
            'calibration_ids_sha256': ids_hash(episode['calibration']),
            'calibration_row_indices': episode['row_indices']['calibration'],
            'development_ids': episode['development'],
            'development_ids_sha256': ids_hash(episode['development']),
            'development_row_indices': episode['row_indices']['development'],
            'recomputed_development_score': value,
        })
    checks = []
    for record in deployments:
        observed = {screen.S0: feedback[record['episode']]}
        observed.update({item['program']: item['development_score'] for item in record['trajectory']})
        selected = min(observed, key=lambda program: (-observed[program], program))
        checks.append({
            'episode': record['episode'], 'seed': record['seed'], 'arm': record['arm'],
            'recomputed_S0_development_score': feedback[record['episode']],
            'original_candidate_feedback': record['trajectory'],
            'original_deployment': record['deployment'], 'replayed_deployment': selected,
            'matches': selected == record['deployment'],
        })
    assert len(records) == 8 and len(checks) == 168
    assert screen.sha(original_deployments) == before
    screen.check_freeze()
    status = 'PASS' if all(item['matches'] for item in checks) else 'FAIL'
    screen.write('S0_FEEDBACK_REPLAY.json', {
        'classification': 'POSTRUN_RECOMPUTATION', 'status': status,
        'not_original_logged_feedback': True,
        'audit_code_sha256': screen.sha(screen.ROOT / 'research/strategy_rethink_20261022/audit_s0_feedback.py'),
        'freeze_sha256': screen.sha(screen.OUT / 'FREEZE.json'),
        'route_source_sha256': screen.sha(screen.SOURCE),
        'original_deployments_sha256_before_and_after': before,
        'S0_feedback': records, 'deployment_checks': checks,
        'matching_deployments': sum(item['matches'] for item in checks),
        'additional_solver_fits': 8, 'additional_route_regressions': route_regressions,
        'fit_and_development_score_cpu_seconds': fit_cpu,
        'wall_seconds_including_hashes_and_IO': time.perf_counter() - started,
        'terminal_selected_or_scored': False, 'source_scores_refit': False,
        'screen_main_rerun': False, 'old_outputs_changed': False,
        'full_npz_truth_decode_memory_contact': True,
        'numeric_contact_note': 'NPZ arrays decoded in full before slicing; only later calibration/development slices returned, no terminal slices selected or scored.',
    })
    print(json.dumps({'classification': 'POSTRUN_RECOMPUTATION', 'status': status,
                      'matching_deployments': sum(item['matches'] for item in checks),
                      'additional_solver_fits': 8, 'route_regressions': route_regressions}))
    assert status == 'PASS', 'retain failing replay output; do not overwrite'


if __name__ == '__main__':
    main()
