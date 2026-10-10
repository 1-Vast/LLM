"""Synthetic counterexamples; no source RNA or untreated/treated outcomes read."""
import json
from pathlib import Path

import numpy as np
import pytest

from research.decision_value.observation_reliability.noise import audit_groups, select_numerical_tie
from research.decision_value.observation_reliability.shadow import route
from research.decision_value.observation_reliability import run as audit_run


def test_weighted_scalar_identity_and_actual_group_sizes():
    rng = np.random.default_rng(12)
    sizes = [32, 32, 30, 28, 32, 32, 32, 32]
    groups = [rng.normal(size=(n, 39)) for n in sizes]
    weights = np.linspace(-.02, .03, 39)
    result = audit_groups(groups, weights, [dict(sample=str(i)) for i in range(8)], bootstrap_draws=64)
    assert [row["cells"] for row in result["groups"]] == sizes
    for values, n, row in zip(groups, sizes, result["groups"]):
        covariance = np.cov(values, rowvar=False, ddof=1)
        np.testing.assert_allclose(row["scalar_sample_variance"], weights @ covariance @ weights)
        np.testing.assert_allclose(row["scalar_sample_mean_variance"], np.var(values @ weights, ddof=1) / n)
        np.testing.assert_allclose(row["diagonal_only_sample_mean_variance"], np.sum(np.diag(covariance) * weights ** 2) / n)
    assert result["groups"][2]["scalar_sample_mean_variance"] != result["groups"][2]["scalar_sample_variance"] / 32
    json.dumps(result, allow_nan=False)


def test_positive_and_negative_covariance_are_not_independent_gene_noise():
    cells = np.arange(28., dtype=float)
    positive = np.column_stack([cells, cells])
    negative = np.column_stack([cells, -cells])
    result = audit_groups([positive, negative], [1., 1.], [{}, {}], bootstrap_draws=128)
    first, second = result["groups"]
    assert first["covariance_sample_mean_variance"] > 0 and first["full_to_diagonal_ratio"] == pytest.approx(2.)
    assert second["scalar_sample_mean_variance"] == 0 and second["full_to_diagonal_ratio"] == 0
    assert second["covariance_sample_mean_variance"] < 0
    assert second["bootstrap_percentile_95"]["scalar_sample_mean_variance"] == [0., 0.]


def test_zero_variance_has_undefined_ratio_and_finite_bootstrap():
    result = audit_groups([np.ones((30, 39))], np.ones(39) / 39, [dict(sample="constant")], bootstrap_draws=32)
    row = result["groups"][0]
    assert row["scalar_sample_variance"] == row["diagonal_only_sample_mean_variance"] == 0
    assert row["full_to_diagonal_ratio"] is None and row["ratio_defined_bootstrap_draws"] == 0
    assert row["bootstrap_percentile_95"]["full_to_diagonal_ratio"] is None
    json.dumps(result, allow_nan=False)


def test_endpoint_weights_applied_once_and_variance_not_added_twice():
    values = np.column_stack([np.arange(32.), np.arange(32.) ** 2])
    row = audit_groups([values], [2., 0.], [{}], bootstrap_draws=32)["groups"][0]
    expected = 4 * np.var(values[:, 0], ddof=1) / 32
    assert row["scalar_sample_mean_variance"] == pytest.approx(expected)
    assert row["diagonal_only_sample_mean_variance"] == pytest.approx(expected)
    assert row["covariance_sample_mean_variance"] == pytest.approx(0.)


def test_bootstrap_is_repeatable_preserves_gene_vectors_and_metadata():
    cells = np.arange(32.)
    groups = [np.column_stack([cells, -cells])]
    metadata = [dict(sample="s1", plate="p1", context="public")]
    first = audit_groups(groups, [1., 1.], metadata, bootstrap_draws=128, seed=17)
    second = audit_groups(groups, [1., 1.], metadata, bootstrap_draws=128, seed=17)
    assert first == second and first["groups"][0]["metadata"] == metadata[0]
    assert first["groups"][0]["bootstrap_percentile_95"]["scalar_sample_mean_variance"] == [0., 0.]
    assert "independent cultures" in first["assumption"]


def test_small_or_nonfinite_groups_and_invalid_weights_refuse():
    with pytest.raises(ValueError, match="at_least_two"):
        audit_groups([np.zeros((1, 39))], np.ones(39), [{}])
    with pytest.raises(ValueError, match="axis_matched"):
        audit_groups([np.zeros((28, 38))], np.ones(39), [{}])
    with pytest.raises(ValueError, match="finite_endpoint"):
        audit_groups([np.zeros((28, 39))], np.full(39, np.nan), [{}])
    with pytest.raises(ValueError, match="axis_matched"):
        audit_groups([np.full((28, 39), np.nan)], np.ones(39), [{}])


def test_prospective_tolerance_prefers_cost_then_simple_without_rewriting_old_losses():
    losses = np.array([1., 1. + 5e-11, 1. + 2e-11, 1. + 1e-5])
    result = select_numerical_tie(losses, [6, 5, 5, 1], [0, 2, 1, 0])
    assert result["eligible"] == [0, 1, 2] and result["selected"] == 2
    assert result["selected_loss"] > result["best_loss"]
    np.testing.assert_array_equal(losses, [1., 1. + 5e-11, 1. + 2e-11, 1. + 1e-5])
    assert select_numerical_tie([0., 5e-13], [6, 5], [0, 1])["selected"] == 1
    assert select_numerical_tie([0., 2e-12], [6, 5], [0, 1])["selected"] == 0


def verified_record(**extras):
    return dict(status="verified", source_verified=True, receipt="source/receipt.json", **extras)


def test_shadow_router_rejects_B_and_private_inputs_instead_of_using_them():
    with pytest.raises(ValueError, match="evaluation_B"):
        route(dict(axis=verified_record(), train_B=[1., 2.]))
    with pytest.raises(ValueError, match="evaluation_B"):
        route(dict(axis=dict(status="verified", source_verified=True, receipt=dict(outcomes=[1.]))))
    with pytest.raises(ValueError, match="strict_source"):
        route(dict(axis=dict(status="verified", source_verified=True, receipt="a", LLM_assertion="valid")))


def test_shadow_routing_authenticates_axis_before_controls_and_never_buys():
    scenarios = [({}, "authenticate_axis"),
        (dict(axis=dict(status="failed", source_verified=True, receipt="bad_axis")), "authenticate_axis"),
        (dict(axis=verified_record()), "audit_controls"),
        (dict(axis=verified_record(), control_noise=verified_record()), "request_matched_treated_repeats")]
    for evidence, expected in scenarios:
        result = route(evidence)
        assert result["proposed_step"] == expected
        assert result["shadow"] and result["purchase_count"] == 0 and result["predicted_benefit"] is None
        assert set(result["available_hypotheses"]) == {"H1", "H2", "H3", "H4"}


def test_controls_are_not_treated_repeat_or_transfer_certificates():
    evidence = dict(axis=verified_record(), control_noise=verified_record())
    assert route(evidence)["proposed_step"] == "request_matched_treated_repeats"
    evidence["treated_repeats"] = verified_record(matched=True, time_match=True, independent_units=True)
    assert route(evidence)["proposed_step"] == "paired_information_trial"
    evidence["transfer"] = verified_record()
    assert route(evidence)["proposed_step"] == "paired_information_trial"
    evidence["P2_certificate"] = verified_record()
    assert route(evidence)["proposed_step"] == "paired_information_trial"
    evidence["P2_certificate"]["status"] = "qualified"
    result = route(evidence)
    assert result["proposed_step"] == "consider_acquisition" and result["predicted_benefit"] is None
    assert any("prices" in blocker for blocker in result["blocking_evidence"])


def test_conflicted_or_failed_qualification_proposes_direct_B_or_stop():
    evidence = dict(axis=verified_record(), control_noise=verified_record(),
        treated_repeats=verified_record(matched=True, time_match=True, independent_units=True),
        transfer=dict(status="conflict", source_verified=True, receipt="contradictory_sources"))
    result = route(evidence)
    assert result["proposed_step"] == "direct_B_or_stop" and result["purchase_count"] == 0
    evidence["transfer"] = verified_record()
    evidence["P2_certificate"] = dict(status="failed", source_verified=True, receipt="failed_gate")
    assert route(evidence)["proposed_step"] == "direct_B_or_stop"


def test_missing_or_unverified_receipt_and_type_errors_cannot_release_acquisition():
    evidence = dict(axis=dict(status="verified", source_verified=False, receipt="a"))
    assert route(evidence)["proposed_step"] == "authenticate_axis"
    assert route(dict(axis=dict(status="verified", source_verified=True)))["proposed_step"] == "authenticate_axis"
    with pytest.raises(ValueError, match="boolean"):
        route(dict(axis=dict(status="verified", source_verified="true", receipt="a")))


def prepared_fake_audit(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parent
    here = tmp_path / 'study'
    (here / 'axis').mkdir(parents=True)
    for name in ('CONTROL_PLAN.json', 'ENDPOINT.json', 'PROTOCOL.json'):
        (here / name).write_bytes((source / name).read_bytes())
    plan = audit_run.read(here / 'CONTROL_PLAN.json')
    endpoint = audit_run.read(here / 'ENDPOINT.json')
    mapping = tmp_path / 'mapping.json'
    names = [None] * 2000
    for index, symbol in zip(endpoint['coordinates'], endpoint['symbols']):
        names[index] = symbol
    audit_run.write(mapping, dict(names=names))
    axis_hashes = {}
    for name, field in (('PROTOCOL.json', 'protocol_sha256'), ('FREEZE.json', 'freeze_sha256'), ('RESULTS.json', 'results_sha256')):
        audit_run.write(here / 'axis' / name, dict(synthetic_only=True, file=name))
        axis_hashes[field] = audit_run.digest(here / 'axis' / name)
    source_files = sorted({group['file'] for group in plan['selected']})
    audit_run.write(here / 'axis/CERTIFICATE.json', dict(status='PASS', endpoint39_verified=True,
        source_revision=plan['revision'], source_files=source_files,
        per_file_endpoint39_verified={file: True for file in source_files},
        mapping_file='mapping.json', mapping_sha256=audit_run.digest(mapping),
        endpoint_definition_sha256=audit_run.digest(here / 'ENDPOINT.json'), **axis_hashes))
    audit_run.write(here / 'FREEZE.json', dict(inputs={path.relative_to(tmp_path).as_posix(): audit_run.digest(path)
        for path in (here / 'CONTROL_PLAN.json', here / 'ENDPOINT.json', here / 'PROTOCOL.json',
                     here / 'axis/CERTIFICATE.json', mapping)}))
    monkeypatch.setattr(audit_run, 'ROOT', tmp_path)
    monkeypatch.setattr(audit_run, 'HERE', here)
    return here, plan


def test_axis_block_precedes_every_network_request(tmp_path, monkeypatch):
    (tmp_path / 'axis').mkdir()
    monkeypatch.setattr(audit_run, 'HERE', tmp_path)
    requests = []
    monkeypatch.setattr(audit_run.requests, 'get', lambda *args, **kwargs: requests.append((args, kwargs)))
    monkeypatch.setattr(audit_run, 'fetch_rows', lambda *args: requests.append(args))
    with pytest.raises(ValueError, match='CERTIFICATE_MISSING'):
        audit_run.execute(tmp_path / 'output')
    assert not requests and not (tmp_path / 'output').exists()


def test_frozen_hash_mismatch_precedes_network_and_output_creation(tmp_path, monkeypatch):
    here, _ = prepared_fake_audit(tmp_path, monkeypatch)
    (here / 'PROTOCOL.json').write_text('{}', encoding='utf-8')
    requests = []
    monkeypatch.setattr(audit_run, 'fetch_rows', lambda *args: requests.append(args))
    with pytest.raises(ValueError, match='frozen_noise_input_changed'):
        audit_run.execute(tmp_path / 'output')
    assert not requests and not (tmp_path / 'output').exists()


def test_endpoint_binding_mismatch_blocks_before_network(tmp_path, monkeypatch):
    here, _ = prepared_fake_audit(tmp_path, monkeypatch)
    endpoint = audit_run.read(here / 'ENDPOINT.json')
    endpoint['coordinates'][0] += 1
    audit_run.write(here / 'ENDPOINT.json', endpoint)
    requests = []
    monkeypatch.setattr(audit_run, 'fetch_rows', lambda *args: requests.append(args))
    with pytest.raises(ValueError, match='ENDPOINT_AXIS_AUTHENTICATION'):
        audit_run.execute(tmp_path / 'output')
    assert not requests and not (tmp_path / 'output').exists()


def test_axis_inner_receipt_hash_tamper_blocks_before_network(tmp_path, monkeypatch):
    here, _ = prepared_fake_audit(tmp_path, monkeypatch)
    audit_run.write(here / 'axis/RESULTS.json', dict(status='fabricated_PASS'))
    requests = []
    monkeypatch.setattr(audit_run, 'fetch_rows', lambda *args: requests.append(args))
    with pytest.raises(ValueError, match='CERTIFICATE_INPUT_HASH_MISMATCH'):
        audit_run.execute(tmp_path / 'output')
    assert not requests and not (tmp_path / 'output').exists()


def test_axis_mapping_rehash_cannot_hide_wrong_endpoint_identity(tmp_path, monkeypatch):
    here, _ = prepared_fake_audit(tmp_path, monkeypatch)
    mapping = tmp_path / 'mapping.json'
    names = audit_run.read(mapping)['names']
    endpoint = audit_run.read(here / 'ENDPOINT.json')
    names[endpoint['coordinates'][0]] = 'WRONG_GENE'
    audit_run.write(mapping, dict(names=names))
    certificate = audit_run.read(here / 'axis/CERTIFICATE.json')
    certificate['mapping_sha256'] = audit_run.digest(mapping)
    audit_run.write(here / 'axis/CERTIFICATE.json', certificate)
    requests = []
    monkeypatch.setattr(audit_run, 'fetch_rows', lambda *args: requests.append(args))
    with pytest.raises(ValueError, match='ENDPOINT_MEANING_MISMATCH'):
        audit_run.execute(tmp_path / 'output')
    assert not requests and not (tmp_path / 'output').exists()


def test_actual_fetch_rows_uses_registered_offset_exact_HTTP_span_and_float32(tmp_path, monkeypatch):
    _, plan = prepared_fake_audit(tmp_path, monkeypatch)
    group = plan['selected'][0]
    rows = group['rows'][:2]
    assert rows[1] == rows[0] + 1
    values = np.arange(4000, dtype='<f4').reshape(2, 2000)
    payload = values.tobytes()
    offset = group['exact_x_hvg_ranges'][0]['start'] - rows[0] * 8000
    start, end = offset + rows[0] * 8000, offset + (rows[-1] + 1) * 8000 - 1
    calls = []

    class Response:
        status_code = 206
        headers = {'Content-Range': f'bytes {start}-{end}/5000000000'}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def iter_content(self, size):
            yield payload[:8000]
            yield payload[8000:]

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(audit_run.requests, 'get', get)
    actual, receipt = audit_run.fetch_rows(group['file'], rows, plan)
    np.testing.assert_array_equal(actual, values)
    assert receipt['bytes'] == 16000 and receipt['byte_start'] == start and receipt['byte_end'] == end
    assert calls[0][1]['headers'] == {'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'}
    assert receipt['sha256'] == audit_run.hashlib.sha256(payload).hexdigest()


def test_fake250_control_rows_use_actual_n_and_exact_range_accounting(tmp_path, monkeypatch):
    _, plan = prepared_fake_audit(tmp_path, monkeypatch)
    requests = []
    cells = {}
    for group in plan['selected']:
        for row in group['rows']:
            values = (np.arange(2000) * .001 + (row % 17) * .02 + np.sin(np.arange(2000) + row) * .003).astype('<f4')
            cells[(group['file'], row)] = values

    def fetch(file, rows, active_plan):
        assert active_plan == plan
        assert rows == list(range(rows[0], rows[-1] + 1))
        assert all((file, row) in cells for row in rows)
        requests.append((file, rows))
        group = next(group for group in plan['selected'] if group['file'] == file)
        offset = group['exact_x_hvg_ranges'][0]['start'] - group['rows'][0] * 8000
        values = np.stack([cells[(file, row)] for row in rows])
        payload = values.tobytes()
        return values, dict(file=file, rows=rows, bytes=len(payload), byte_start=offset + rows[0] * 8000,
            byte_end=offset + (rows[-1] + 1) * 8000 - 1, sha256=audit_run.hashlib.sha256(payload).hexdigest())

    monkeypatch.setattr(audit_run, 'fetch_rows', fetch)
    result = audit_run.execute(tmp_path / 'output')
    assert [row['cells'] for row in result['groups']] == [32, 32, 30, 28, 32, 32, 32, 32]
    assert result['control_RNA_bytes'] == 2_000_000 and result['treated_RNA_bytes'] == 0
    assert not result['P2_release'] and result['independent_culture_count'] is None and result['decision_gain'] is None
    assert result['source_range_reads'] == len(requests)
    fetched = [(file, row) for file, rows in requests for row in rows]
    assert len(fetched) == len(set(fetched)) == 250
    endpoint = audit_run.read(audit_run.HERE / 'ENDPOINT.json')
    weights = np.array(endpoint['weights'])
    for group, row in zip(plan['selected'], result['groups']):
        values = np.stack([cells[(group['file'], index)] for index in group['rows']])[:, endpoint['coordinates']].astype(float)
        expected = weights @ np.cov(values, rowvar=False, ddof=1) @ weights / len(values)
        np.testing.assert_allclose(row['scalar_sample_mean_variance'], expected, rtol=1e-12)
    corrections = result['all32_correction']
    assert [row['variance_understatement_if_divided_by32'] for row in corrections] == [.0625, .125]
    receipt = audit_run.read(tmp_path / 'output/RUN_RECEIPT.json')
    assert receipt['status'] == 'PASS_CONTROL_AUDIT'
    assert all(audit_run.digest(tmp_path / 'output' / name) == digest for name, digest in receipt['outputs'].items())


def test_download_future_failure_records_completed_bytes_and_blocks_results(tmp_path, monkeypatch):
    _, plan = prepared_fake_audit(tmp_path, monkeypatch)
    failing = min(group['rows'][0] for group in plan['selected'] if group['file'] == 'c40.h5ad')

    def fetch(file, rows, active_plan):
        if file == 'c40.h5ad' and failing in rows:
            raise ValueError('synthetic_range_failure')
        return np.zeros((len(rows), 2000)), dict(file=file, rows=rows, bytes=len(rows) * 8000)

    monkeypatch.setattr(audit_run, 'fetch_rows', fetch)
    with pytest.raises(ValueError, match='ranges_incomplete'):
        audit_run.execute(tmp_path / 'output')
    failed = audit_run.read(tmp_path / 'output/FAILED.json')
    assert failed['status'] == 'BLOCKED/CONTROL_DOWNLOAD' and failed['failures']
    assert failed['downloaded_body_bytes'] == sum(row['bytes'] for row in failed['completed_receipts']) < 2_000_000
    assert not (tmp_path / 'output/RESULTS.json').exists()
