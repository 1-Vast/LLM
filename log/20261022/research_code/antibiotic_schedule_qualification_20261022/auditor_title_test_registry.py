import json

from auditor_title_registry import project_datacite, project_figshare, project_zenodo


def test_zenodo_projects_file_identity_without_embedded_response_values():
    data = {"hits": {"total": 1, "hits": [{"id": 1, "metadata": {"title": "study", "creators": [{"name": "Jeong, Yoon"}], "description": "response 12345.6789", "related_identifiers": [{"identifier": "10.1101/2025.10.30.684665", "relation": "isSupplementTo"}]}, "files": [{"key": "metadata.csv", "size": 42, "response_values": [98765.4321]}]}]}}
    output = json.dumps(project_zenodo(data))
    assert "12345.6789" not in output and "98765.4321" not in output
    assert "10.1101/2025.10.30.684665" in output and "metadata.csv" in output


def test_datacite_excludes_descriptions_and_measurement_fields():
    result = project_datacite({"meta": {"total": 1}, "data": [{"id": "x", "attributes": {"titles": [{"title": "study"}], "descriptions": ["12345.6789"], "response_values": [98765.4321]}}]})
    assert "12345.6789" not in json.dumps(result) and "98765.4321" not in json.dumps(result)
    assert result["total"] == 1


def test_figshare_excludes_embedded_data_and_keeps_paper_relation():
    result = project_figshare([{"id": 1, "title": "study", "resource_doi": "10.1101/2025.10.30.684665", "description": "12345.6789", "values": [98765.4321]}])
    assert "12345.6789" not in json.dumps(result) and "98765.4321" not in json.dumps(result)
    assert result["records"][0]["resource_doi"] == "10.1101/2025.10.30.684665"
