import json

from auditor_brief import project


def test_brief_projects_only_identity_protocol_and_stops_before_values():
    raw = b'^SAMPLE = GSM1\n!Sample_geo_accession = GSM1\n!Sample_treatment_protocol_ch1 = drug A 10 uM 24h\n!Sample_unknown_metric = 12345.6789\n!sample_table_begin\nID_REF VALUE\nprobe1 98765.4321\n^SAMPLE = GSM2\n'
    result = project(raw)
    assert len(result["samples"]) == 1
    assert result["stopped_before_sample_table_begin"]
    assert "10 uM 24h" in json.dumps(result)
    assert "12345.6789" not in json.dumps(result)
    assert "98765.4321" not in json.dumps(result)
