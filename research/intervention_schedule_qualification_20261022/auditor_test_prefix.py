import json

from auditor_prefix_metadata import project_prefix


def test_stops_before_table_and_recovers_incomplete_sample_protocol_only():
    raw = b'<MINiML><Sample iid="GSM1"><Title>sample</Title><Channel><Treatment-Protocol>drug A 24h</Treatment-Protocol></Channel><Data-Table><Row>123456.789</Row></Data-Table></Sample></MINiML>'
    result = project_prefix(raw)
    assert result["stopped_before_first_Data_Table"]
    assert result["entries"][0]["accession"] == "GSM1"
    assert not result["entries"][0]["complete_before_table_cutoff"]
    assert "drug A 24h" in json.dumps(result)
    assert "123456.789" not in json.dumps(result)


def test_platform_table_before_samples_cannot_be_called_sample_coverage():
    result = project_prefix(b'<MINiML><Platform iid="GPL1"><Data-Table><Row>1234.567</Row></Data-Table></Platform><Sample iid="GSM1"></Sample></MINiML>')
    assert result["entries"] == []
    assert not result["full_family_coverage_authenticated"]
