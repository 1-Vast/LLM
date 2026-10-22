import hashlib
import json

import acquire_and_inventory as inventory


def test_response_changes_cannot_change_exported_inventory(tmp_path, monkeypatch):
    path = tmp_path / "test.csv"
    monkeypatch.setattr(inventory, "OUT", tmp_path)
    monkeypatch.setattr(inventory, "SEALED", path)
    def run(response):
        text = "sample_id,assay_name,smiles,conc0,data0,efficacy,auc,curve_class2\nA,primary,CCO,1e-6," + response + ",999,123,-1\n"
        path.write_text(text, encoding="utf-8")
        (tmp_path / "CSV_SOURCE.json").write_text(json.dumps({"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}))
        inventory.child()
        return (tmp_path / "BLIND_COVERAGE.json").read_text(), (tmp_path / "IDENTITY_ROWS.json").read_text()
    first = run("-10000")
    second = run("10000")
    assert first == second
    rows = json.loads(first[1])
    assert set(rows[0]) == {"sample_id", "assay_name", "smiles", "conc0"}


def test_fitted_and_observed_responses_are_not_in_whitelist():
    assert not inventory.IDENTITY.intersection({"data0", "data14", "auc", "efficacy", "max_response", "r2", "curve_class2", "log_ac50"})
