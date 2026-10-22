import json

from auditor_title_citations import TARGET_DOI, TARGET_TITLE, project


def test_only_direct_bibliography_leaves_description_worker():
    result = project({"description": f'<p>{TARGET_TITLE}; doi https://doi.org/{TARGET_DOI}</p><p>response 12345.6789</p>'})
    assert result["target_paper_DOI_literal_present"] and result["target_paper_fulltitle_present"]
    assert "12345.6789" not in json.dumps(result)
    assert result["citation_DOI_strings"] == [TARGET_DOI]


def test_empty_or_unrelated_description_does_not_authenticate():
    result = project({"description": "Multiplex chamber imaging, response 12345.6789"})
    assert not result["target_paper_DOI_literal_present"] and not result["target_paper_fulltitle_present"]
    assert "12345.6789" not in json.dumps(result)
