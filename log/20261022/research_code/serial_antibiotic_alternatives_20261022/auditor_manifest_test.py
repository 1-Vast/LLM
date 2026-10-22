import json

from auditor_manifest import project_esearch, project_oa, project_supplements


def test_oa_only_projects_manifest_and_keeps_explicit_error():
    result = project_oa(b'<OA><records><record id="PMC1" license="CC BY"><link format="tgz" href="ftp://example.org/a.tgz" updated="now"/></record></records><error code="x">not available</error></OA>')
    assert result["records"][0]["links"][0]["format"] == "tgz"
    assert result["errors"][0]["attributes"]["code"] == "x"


def test_biosample_count_excludes_idlist_and_retains_field_warning():
    result = project_esearch(json.dumps({"esearchresult": {"count": "0", "retmax": "0", "idlist": ["123456.789"], "warninglist": {"phrasesnotfound": ["BioProject"]}}}).encode())
    assert "123456.789" not in json.dumps(result)
    assert result["warninglist"]


def test_supplement_projection_does_not_export_article_results():
    raw = b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><front><article-meta><article-id pub-id-type="pmc">1</article-id></article-meta></front><body><p>MIC response 123456.789</p><supplementary-material id="s1"><label>Supplement</label><media xlink:href="supp.pdf" mimetype="application" mime-subtype="pdf">Supplementary Data</media></supplementary-material></body></article>'
    result = project_supplements(raw)
    assert result["supplements"][0]["media"][0]["href"] == "supp.pdf"
    assert "123456.789" not in json.dumps(result)
