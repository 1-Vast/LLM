"""Synthetic metadata-only output guard tests, independent of GEO measurements."""
import json

import pytest

from auditor_metadata import project_miniml, project_soft


def test_miniml_discards_tables_and_exports_protocol_identity_only():
    raw = b'''<MINiML xmlns="http://www.ncbi.nlm.nih.gov/geo/info/MINiML"><Sample iid="GSM1"><Title>cell A 24h</Title><Channel><Source>cell A</Source><Treatment-Protocol>drug A 10 uM</Treatment-Protocol></Channel><Description>forbidden stray</Description><Data-Table><Row>123456.78998765</Row></Data-Table></Sample></MINiML>'''
    result = project_miniml(raw)
    text = json.dumps(result)
    assert result["samples"][0]["accession"] == "GSM1"
    assert "drug A 10 uM" in text
    assert "123456.78998765" not in text
    assert "forbidden stray" not in text
    assert result["measurement_table_blocks_discarded"] == 1


def test_soft_stops_before_sample_measurement_table_even_if_forged_metadata_follows():
    raw = b'!Series_geo_accession = GSE30516\n!Series_title = study\n!sample_table_begin\nID_REF VALUE\nprobe1 123456.78998765\n!Series_summary = forbidden-after-table\n'
    result = project_soft(raw)
    assert result["stopped_before_sample_table_begin"]
    assert "123456.78998765" not in json.dumps(result)
    assert "forbidden-after-table" not in json.dumps(result)


def test_empty_table_cannot_swallow_later_samples():
    raw = b'<MINiML><Sample iid="GSM1"><Data-Table/></Sample><Sample iid="GSM2"><Title>second identity</Title><Data-Table><Row>987654.321</Row></Data-Table></Sample></MINiML>'
    result = project_miniml(raw)
    assert [r["accession"] for r in result["samples"]] == ["GSM1", "GSM2"]
    assert result["measurement_table_blocks_discarded"] == 2
    assert "987654.321" not in json.dumps(result)


@pytest.mark.parametrize("raw", [b"<html>wrong content</html>", b"<MINiML><Sample>"])
def test_unexpected_or_malformed_xml_is_rejected(raw):
    with pytest.raises(Exception):
        project_miniml(raw)


def test_soft_rejects_missing_or_wrong_exact_series():
    with pytest.raises(ValueError):
        project_soft(b"!Series_geo_accession = GSE1\n")
